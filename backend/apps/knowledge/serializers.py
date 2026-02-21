from rest_framework import serializers
from apps.knowledge.models import GitCredential, KnowledgeBase, Source


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = ["id", "name", "description", "owner", "owner_username", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "owner_username", "created_at", "updated_at"]


class GitCredentialSerializer(serializers.ModelSerializer):
    pat = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = GitCredential
        fields = ["id", "label", "pat", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        pat = validated_data.pop("pat")
        cred = GitCredential(**validated_data)
        cred.set_pat(pat)
        cred.save()
        return cred

    def update(self, instance, validated_data):
        pat = validated_data.pop("pat", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if pat:
            instance.set_pat(pat)
        instance.save()
        return instance


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = [
            "id", "kb", "title", "source_type", "status",
            "storage_key", "git_url", "git_credential", "git_branch",
            "last_synced_at", "error_message", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "last_synced_at", "error_message", "created_at", "updated_at"]
