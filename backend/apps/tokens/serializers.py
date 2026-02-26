from rest_framework import serializers
from apps.tokens.models import APIToken
from apps.knowledge.models import KnowledgeBase


class KBScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = ["id", "name"]


class APITokenSerializer(serializers.ModelSerializer):
    knowledge_bases = KBScopeSerializer(many=True, read_only=True)
    kb_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False, default=list
    )
    expires_in_days = serializers.IntegerField(
        write_only=True, required=False, allow_null=True, min_value=1
    )

    class Meta:
        model = APIToken
        fields = [
            "id", "name", "description",
            "token_prefix",
            "knowledge_bases", "kb_ids",
            "is_active",
            "created_at", "last_used_at", "last_used_ip", "expires_at",
            "expires_in_days",
        ]
        read_only_fields = [
            "id", "token_prefix", "knowledge_bases",
            "created_at", "last_used_at", "last_used_ip",
        ]


class APITokenCreateSerializer(APITokenSerializer):
    token = serializers.CharField(read_only=True)

    class Meta(APITokenSerializer.Meta):
        fields = APITokenSerializer.Meta.fields + ["token"]
