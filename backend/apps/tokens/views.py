from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, DestroyModelMixin,
    UpdateModelMixin, RetrieveModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.knowledge.models import KnowledgeBase
from apps.tokens.models import APIToken
from apps.tokens.serializers import APITokenSerializer, APITokenCreateSerializer


class APITokenViewSet(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin,
    UpdateModelMixin, DestroyModelMixin, GenericViewSet
):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [IsAuthenticated]
    serializer_class = APITokenSerializer

    PATCH_ALLOWED_FIELDS = {"name", "description", "is_active"}

    def get_queryset(self):
        return APIToken.objects.filter(user=self.request.user).prefetch_related("knowledge_bases")

    def create(self, request, *args, **kwargs):
        ser = APITokenCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        data = ser.validated_data
        kb_ids = [str(uid) for uid in data.pop("kb_ids", [])]
        expires_in_days = data.pop("expires_in_days", None)

        kbs = []
        if kb_ids:
            kbs = list(
                KnowledgeBase.objects.filter(
                    pk__in=kb_ids,
                    access_entries__user=request.user,
                )
            )
            if len(kbs) != len(kb_ids):
                return Response(
                    {"kb_ids": "One or more knowledge bases are not accessible."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        expires_at = None
        if expires_in_days is not None:
            expires_at = timezone.now() + timedelta(days=expires_in_days)

        instance, raw_token = APIToken.create_token(
            user=request.user,
            name=data["name"],
            description=data.get("description", ""),
            knowledge_bases=kbs or None,
            expires_at=expires_at,
        )

        out = APITokenCreateSerializer(instance).data
        out["token"] = raw_token
        return Response(out, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if not kwargs.get("partial"):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Restrict writable fields on PATCH
        unexpected = set(request.data.keys()) - self.PATCH_ALLOWED_FIELDS
        if unexpected:
            return Response(
                {"detail": f"Fields not allowed on update: {', '.join(sorted(unexpected))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)
