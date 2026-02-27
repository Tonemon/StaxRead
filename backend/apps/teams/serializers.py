from django.contrib.auth import get_user_model
from rest_framework import serializers
from apps.teams.models import Team, TeamMembership

User = get_user_model()

ROLE_ORDER = ["guest", "member", "manager", "admin", "owner"]


class TeamMembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    role = serializers.ChoiceField(choices=TeamMembership.ROLE_CHOICES)

    class Meta:
        model = TeamMembership
        fields = ["id", "user_id", "username", "role", "joined_at"]
        read_only_fields = ["id", "username", "joined_at"]

    def validate_user_id(self, value):
        try:
            return User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")


class TeamSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "name", "description", "icon_url", "my_role", "created_at", "updated_at"]
        read_only_fields = ["id", "my_role", "created_at", "updated_at"]

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        try:
            return TeamMembership.objects.get(team=obj, user=request.user).role
        except TeamMembership.DoesNotExist:
            return None
