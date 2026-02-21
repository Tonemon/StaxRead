from rest_framework import serializers
from apps.knowledge.models import KnowledgeBase


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = ["id", "name", "description", "owner", "owner_username", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "owner_username", "created_at", "updated_at"]
