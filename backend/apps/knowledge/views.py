import tempfile
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.knowledge.models import GitCredential, KnowledgeBase, KBAccess, Source
from apps.knowledge.serializers import GitCredentialSerializer, KBInvitationSerializer, KnowledgeBaseSerializer, SourceSerializer
from apps.ingestion.tasks.pdf import ingest_pdf
from apps.ingestion.tasks.epub import ingest_epub
from apps.ingestion.tasks.git import ingest_git
from apps.ingestion.storage import upload_file, get_presigned_url
from apps.teams.access import get_accessible_kbs, has_write_permission, MANAGER_ROLES
from apps.teams.models import TeamMembership

User = get_user_model()


class KnowledgeBaseViewSet(ModelViewSet):
    serializer_class = KnowledgeBaseSerializer

    def get_queryset(self):
        user = self.request.user
        qs = get_accessible_kbs(user)
        team_id = self.request.query_params.get("team")
        if team_id:
            qs = qs.filter(team_id=team_id)
        qs = qs.prefetch_related(
            Prefetch(
                'access_entries',
                queryset=KBAccess.objects.filter(user=user, status=KBAccess.Status.ACCEPTED),
                to_attr='_user_access_entries',
            ),
            Prefetch(
                'team__memberships',
                queryset=TeamMembership.objects.filter(user=user),
                to_attr='_user_team_memberships',
            ),
        )
        return qs

    def perform_create(self, serializer):
        team = serializer.validated_data.get("team")
        if team is not None:
            if not TeamMembership.objects.filter(
                team=team, user=self.request.user, role__in=MANAGER_ROLES
            ).exists():
                raise PermissionDenied("You must be a Manager or above to create a team KB.")
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        kb = self.get_object()
        if kb.team_id:
            if not TeamMembership.objects.filter(
                team_id=kb.team_id, user=request.user, role__in=MANAGER_ROLES
            ).exists():
                return Response(status=status.HTTP_403_FORBIDDEN)
        elif kb.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def _can_manage_kb(self, request, kb):
        """True if the user may invite, remove, or change permissions on this KB."""
        if kb.team_id:
            return TeamMembership.objects.filter(
                team_id=kb.team_id, user=request.user, role__in=MANAGER_ROLES
            ).exists()
        return kb.owner == request.user

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        kb = self.get_object()
        if not self._can_manage_kb(request, kb):
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        # For team KBs: don't create a KBAccess entry for existing team members
        if kb.team_id:
            if TeamMembership.objects.filter(team_id=kb.team_id, user=target_user).exists():
                return Response(
                    {"detail": "User is already a team member and has implicit access."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        KBAccess.objects.get_or_create(
            kb=kb, user=target_user,
            defaults={"status": KBAccess.Status.PENDING, "permission": KBAccess.Permission.READ},
        )
        return Response({"detail": f"{target_user.username} has been invited."})

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        kb = self.get_object()
        result = []

        if kb.team_id:
            team_memberships = (
                TeamMembership.objects.filter(team_id=kb.team_id)
                .select_related("user")
            )
            team_user_ids = {str(tm.user_id) for tm in team_memberships}
            for tm in team_memberships:
                effective_perm = (
                    KBAccess.Permission.WRITE if tm.role in MANAGER_ROLES
                    else KBAccess.Permission.READ
                )
                result.append({
                    "user_id": str(tm.user.pk),
                    "username": tm.user.username,
                    "status": KBAccess.Status.ACCEPTED,
                    "permission": effective_perm,
                    "is_team_member": True,
                    "team_role": tm.role,
                })
            # External users (KBAccess entries not in the team)
            external = (
                KBAccess.objects.filter(kb=kb)
                .exclude(user__pk__in=team_user_ids)
                .select_related("user")
            )
            for e in external:
                result.append({
                    "user_id": str(e.user.pk),
                    "username": e.user.username,
                    "status": e.status,
                    "permission": e.permission,
                    "is_team_member": False,
                    "team_role": None,
                })
        else:
            # Personal KB: all KBAccess entries except the owner
            entries = (
                KBAccess.objects.filter(kb=kb)
                .exclude(user=kb.owner)
                .select_related("user")
            )
            for e in entries:
                result.append({
                    "user_id": str(e.user.pk),
                    "username": e.user.username,
                    "status": e.status,
                    "permission": e.permission,
                    "is_team_member": False,
                    "team_role": None,
                })

        return Response(result)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        kb = self.get_object()
        if kb.owner == request.user:
            return Response(
                {"detail": "Owner cannot leave their own knowledge base."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        KBAccess.objects.filter(kb=kb, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def unshare(self, request, pk=None):
        kb = self.get_object()
        if not self._can_manage_kb(request, kb):
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if kb.team_id:
            if TeamMembership.objects.filter(team_id=kb.team_id, user__pk=user_id).exists():
                return Response(
                    {"detail": "Cannot remove a team member via unshare. Remove them from the team instead."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        KBAccess.objects.filter(kb=kb, user__pk=user_id).delete()
        return Response({"detail": "Access removed."})

    @action(detail=True, methods=["post"])
    def set_permission(self, request, pk=None):
        kb = self.get_object()
        if not self._can_manage_kb(request, kb):
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        permission = request.data.get("permission")
        if permission not in (KBAccess.Permission.READ, KBAccess.Permission.WRITE):
            return Response(
                {"detail": "permission must be 'read' or 'write'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            access = KBAccess.objects.get(
                kb=kb, user__pk=user_id, status=KBAccess.Status.ACCEPTED
            )
        except KBAccess.DoesNotExist:
            return Response(
                {"detail": "No accepted access entry found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        access.permission = permission
        access.save(update_fields=["permission"])
        return Response({"detail": "Permission updated."})


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

    def _assert_write(self, request, kb):
        if not has_write_permission(request.user, kb):
            raise PermissionDenied("You do not have write access to this knowledge base.")

    def get_queryset(self):
        accessible_kb_ids = get_accessible_kbs(self.request.user).values_list("id", flat=True)
        qs = Source.objects.filter(kb__in=accessible_kb_ids).annotate(chunk_count=Count("chunks"))
        kb_id = self.request.query_params.get("kb")
        if kb_id:
            qs = qs.filter(kb=kb_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        source = self.get_object()
        self._assert_write(request, source.kb)
        return super().destroy(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        source_type = request.data.get("source_type")
        file_obj = request.FILES.get("file")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._assert_write(request, serializer.validated_data["kb"])
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
                source.file_size_bytes = file_obj.size
                source.save(update_fields=["storage_key", "file_size_bytes"])
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
        source = self.get_object()  # raises 404 if not in queryset (access enforced)

        if source.source_type == Source.SourceType.PDF:
            ext = os.path.splitext(source.storage_key)[1].lstrip(".")
            url = get_presigned_url(source.pk, ext, filename=f"{source.title}.{ext}")
            return Response({"url": url, "source_type": source.source_type})

        elif source.source_type == Source.SourceType.EPUB:
            ext = os.path.splitext(source.storage_key)[1].lstrip(".")
            url = get_presigned_url(source.pk, ext, filename=f"{source.title}.{ext}")
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
