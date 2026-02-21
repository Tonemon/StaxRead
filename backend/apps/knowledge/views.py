from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.knowledge.models import KnowledgeBase, KBAccess
from apps.knowledge.serializers import KnowledgeBaseSerializer

User = get_user_model()


class KnowledgeBaseViewSet(ModelViewSet):
    serializer_class = KnowledgeBaseSerializer

    def get_queryset(self):
        return KnowledgeBase.objects.filter(
            access_entries__user=self.request.user
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
        KBAccess.objects.get_or_create(kb=kb, user=target_user)
        return Response({"detail": f"Shared with {target_user.username}."})

    @action(detail=True, methods=["post"])
    def unshare(self, request, pk=None):
        kb = self.get_object()
        if kb.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        KBAccess.objects.filter(kb=kb, user__pk=user_id).delete()
        return Response({"detail": "Access removed."})
