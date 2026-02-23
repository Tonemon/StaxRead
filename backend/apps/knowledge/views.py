import tempfile
import os

from django.contrib.auth import get_user_model
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.knowledge.models import GitCredential, KnowledgeBase, KBAccess, Source
from apps.knowledge.serializers import GitCredentialSerializer, KBInvitationSerializer, KnowledgeBaseSerializer, SourceSerializer
from apps.ingestion.tasks.pdf import ingest_pdf
from apps.ingestion.tasks.epub import ingest_epub
from apps.ingestion.tasks.git import ingest_git
from apps.ingestion.storage import upload_file, get_presigned_url

User = get_user_model()


class KnowledgeBaseViewSet(ModelViewSet):
    serializer_class = KnowledgeBaseSerializer

    def get_queryset(self):
        return KnowledgeBase.objects.filter(
            access_entries__user=self.request.user,
            access_entries__status=KBAccess.Status.ACCEPTED,
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        kb = self.get_object()
        if kb.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        kb = self.get_object()
        if kb.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        KBAccess.objects.get_or_create(
            kb=kb, user=target_user,
            defaults={"status": KBAccess.Status.PENDING},
        )
        return Response({"detail": f"{target_user.username} has been invited."})

    @action(detail=True, methods=["post"])
    def unshare(self, request, pk=None):
        kb = self.get_object()
        if kb.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        KBAccess.objects.filter(kb=kb, user__pk=user_id).delete()
        return Response({"detail": "Access removed."})


class KBInvitationViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = KBInvitationSerializer

    def get_queryset(self):
        return KBAccess.objects.filter(
            user=self.request.user,
            status=KBAccess.Status.PENDING,
        ).select_related("kb__owner")

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        invite = self.get_object()
        invite.status = KBAccess.Status.ACCEPTED
        invite.save()
        return Response({"detail": "Invitation accepted."})

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        invite = self.get_object()
        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GitCredentialViewSet(ModelViewSet):
    serializer_class = GitCredentialSerializer

    def get_queryset(self):
        return GitCredential.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SourceViewSet(ModelViewSet):
    serializer_class = SourceSerializer

    def get_queryset(self):
        accessible_kb_ids = KnowledgeBase.objects.filter(
            access_entries__user=self.request.user
        ).values_list("id", flat=True)
        qs = Source.objects.filter(kb__in=accessible_kb_ids)
        kb_id = self.request.query_params.get("kb")
        if kb_id:
            qs = qs.filter(kb=kb_id)
        return qs

    def create(self, request, *args, **kwargs):
        source_type = request.data.get("source_type")
        file_obj = request.FILES.get("file")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = serializer.save()

        # Handle file upload for PDF/EPUB
        if file_obj and source_type in (Source.SourceType.PDF, Source.SourceType.EPUB):
            content_type_map = {
                Source.SourceType.PDF: "application/pdf",
                Source.SourceType.EPUB: "application/epub+zip",
            }
            tmp = tempfile.NamedTemporaryFile(
                suffix=os.path.splitext(file_obj.name)[1],
                delete=False,
            )
            try:
                for chunk in file_obj.chunks():
                    tmp.write(chunk)
                tmp.close()
                object_name = upload_file(source.pk, tmp.name, content_type_map[source_type])
                source.storage_key = object_name
                source.save(update_fields=["storage_key"])
            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

        # Dispatch ingestion task
        source_id = str(source.pk)
        if source_type == Source.SourceType.PDF:
            ingest_pdf.delay(source_id)
        elif source_type == Source.SourceType.EPUB:
            ingest_epub.delay(source_id)
        elif source_type == Source.SourceType.GIT:
            ingest_git.delay(source_id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        source = self.get_object()
        return Response({
            "status": source.status,
            "error_message": source.error_message,
        })

    @action(detail=True, methods=["get"])
    def document(self, request, pk=None):
        from django.conf import settings
        source = self.get_object()  # raises 404 if not in queryset (access enforced)

        if source.source_type == Source.SourceType.PDF:
            ext = os.path.splitext(source.storage_key)[1].lstrip(".")
            url = get_presigned_url(source.pk, ext)
            return Response({"url": url, "source_type": source.source_type})

        elif source.source_type == Source.SourceType.EPUB:
            ext = os.path.splitext(source.storage_key)[1].lstrip(".")
            url = get_presigned_url(source.pk, ext)
            return Response({"url": url, "source_type": source.source_type})

        elif source.source_type == Source.SourceType.GIT:
            file_path_param = request.query_params.get("file", "")
            if not file_path_param:
                return Response({"detail": "file parameter required for git sources."}, status=400)
            repo_path = os.path.join(settings.GIT_REPOS_DIR, str(source.pk))
            full_path = os.path.normpath(os.path.join(repo_path, file_path_param))
            # Security: ensure path stays within repo
            if not full_path.startswith(repo_path):
                return Response({"detail": "Invalid file path."}, status=400)
            if not os.path.exists(full_path):
                return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return Response({"content": content, "file": file_path_param, "source_type": source.source_type})

        return Response({"detail": "Unsupported source type."}, status=400)
