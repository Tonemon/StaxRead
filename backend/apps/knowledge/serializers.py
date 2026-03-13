from rest_framework import serializers
from apps.knowledge.models import GitCredential, KnowledgeBase, KBAccess, Source
from apps.teams.models import Team, TeamMembership
from apps.teams.access import MANAGER_ROLES


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), allow_null=True, required=False, default=None
    )
    team_name = serializers.CharField(source="team.name", read_only=True, default=None)
    user_permission = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBase
        fields = [
            "id", "name", "description",
            "owner", "owner_username",
            "team", "team_name",
            "user_permission",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "owner", "owner_username", "team_name",
            "user_permission", "created_at", "updated_at",
        ]

    def get_user_permission(self, obj) -> str:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return KBAccess.Permission.READ

        user = request.user

        if obj.team_id:
            # Use prefetched team memberships (to_attr='_user_team_memberships' on obj.team)
            team = obj.team
            user_memberships = getattr(team, '_user_team_memberships', None)
            if user_memberships is not None:
                if user_memberships and user_memberships[0].role in MANAGER_ROLES:
                    return KBAccess.Permission.WRITE
            else:
                # Fallback if not prefetched (e.g., detail view)
                try:
                    tm = TeamMembership.objects.get(team_id=obj.team_id, user=user)
                    if tm.role in MANAGER_ROLES:
                        return KBAccess.Permission.WRITE
                except TeamMembership.DoesNotExist:
                    pass

            # Check explicit KBAccess for external users
            user_access = getattr(obj, '_user_access_entries', None)
            if user_access is not None:
                return user_access[0].permission if user_access else KBAccess.Permission.READ
            else:
                # Fallback if not prefetched
                try:
                    access = KBAccess.objects.get(kb=obj, user=user, status=KBAccess.Status.ACCEPTED)
                    return access.permission
                except KBAccess.DoesNotExist:
                    return KBAccess.Permission.READ
        else:
            if obj.owner_id == user.pk:
                return KBAccess.Permission.WRITE
            user_access = getattr(obj, '_user_access_entries', None)
            if user_access is not None:
                return user_access[0].permission if user_access else KBAccess.Permission.READ
            else:
                # Fallback if not prefetched
                try:
                    access = KBAccess.objects.get(kb=obj, user=user, status=KBAccess.Status.ACCEPTED)
                    return access.permission
                except KBAccess.DoesNotExist:
                    return KBAccess.Permission.READ


class KBInvitationSerializer(serializers.ModelSerializer):
    kb_id = serializers.UUIDField(source="kb.id", read_only=True)
    kb_name = serializers.CharField(source="kb.name", read_only=True)
    kb_description = serializers.CharField(source="kb.description", read_only=True)
    owner_username = serializers.CharField(source="kb.owner.username", read_only=True)
    kb_team_name = serializers.CharField(source="kb.team.name", read_only=True, default=None)

    class Meta:
        model = KBAccess
        fields = ["id", "kb_id", "kb_name", "kb_description", "owner_username", "kb_team_name", "granted_at"]
        read_only_fields = fields


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
    chunk_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Source
        fields = [
            "id", "kb", "title", "source_type", "status",
            "storage_key", "file_size_bytes", "git_url", "git_credential", "git_branch",
            "last_synced_at", "error_message", "chunk_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "file_size_bytes", "last_synced_at", "error_message", "created_at", "updated_at"]
