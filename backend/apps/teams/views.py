from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from apps.knowledge.models import GitCredential, KnowledgeBase
from apps.knowledge.serializers import GitCredentialSerializer
from apps.teams.models import Team, TeamMembership
from apps.teams.permissions import ADMIN_ROLES, MANAGER_ROLES
from apps.teams.serializers import TeamSerializer, TeamMembershipSerializer
from apps.tokens.models import APIToken
from apps.tokens.serializers import APITokenSerializer, APITokenCreateSerializer

User = get_user_model()

ROLE_ORDER = ["guest", "member", "manager", "admin", "owner"]


class TeamViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TeamSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Team.objects.filter(memberships__user=self.request.user).distinct()

    def perform_create(self, serializer):
        team = Team(
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description", ""),
            icon_url=serializer.validated_data.get("icon_url", ""),
        )
        team.save(created_by=self.request.user)
        serializer.instance = team

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            self.get_serializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        if not kwargs.get("partial"):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        team = self.get_object()
        if not TeamMembership.objects.filter(team=team, user=request.user, role__in=ADMIN_ROLES).exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        if not TeamMembership.objects.filter(team=team, user=request.user, role="owner").exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="transfer-ownership")
    def transfer_ownership(self, request, pk=None):
        team = self.get_object()
        if not TeamMembership.objects.filter(team=team, user=request.user, role="owner").exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        try:
            new_owner = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if not TeamMembership.objects.filter(team=team, user=new_owner).exists():
            return Response({"detail": "User is not a team member."}, status=status.HTTP_400_BAD_REQUEST)
        TeamMembership.objects.filter(team=team, user=request.user).update(role="admin")
        TeamMembership.objects.filter(team=team, user=new_owner).update(role="owner")
        return Response({"detail": "Ownership transferred."})


class TeamMemberViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = TeamMembershipSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def _get_team(self):
        return get_object_or_404(Team, pk=self.kwargs["team_pk"])

    def _caller_role(self, team):
        try:
            return TeamMembership.objects.get(team=team, user=self.request.user).role
        except TeamMembership.DoesNotExist:
            return None

    def get_queryset(self):
        team_pk = self.kwargs["team_pk"]
        # Must be a member to list
        if not TeamMembership.objects.filter(team_id=team_pk, user=self.request.user).exists():
            return TeamMembership.objects.none()
        return TeamMembership.objects.filter(team_id=team_pk).select_related("user")

    def get_object(self):
        team = self._get_team()
        return get_object_or_404(TeamMembership, pk=self.kwargs["pk"], team=team)

    def create(self, request, *args, **kwargs):
        team = self._get_team()
        caller_role = self._caller_role(team)
        if caller_role not in ADMIN_ROLES:
            return Response(status=status.HTTP_403_FORBIDDEN)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user_id"]  # validate_user_id returns a User object
        role = ser.validated_data.get("role", "member")

        if role == "owner":
            return Response({"detail": "Use transfer-ownership to assign owner."}, status=400)
        if ROLE_ORDER.index(role) > ROLE_ORDER.index(caller_role):
            return Response({"detail": "Cannot assign a role higher than your own."}, status=400)

        membership, created = TeamMembership.objects.get_or_create(
            team=team, user=user,
            defaults={"role": role, "invited_by": request.user},
        )
        if not created:
            return Response({"detail": "User is already a member."}, status=400)
        return Response(self.get_serializer(membership).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        team = self._get_team()
        caller_role = self._caller_role(team)
        if caller_role not in ADMIN_ROLES:
            return Response(status=status.HTTP_403_FORBIDDEN)

        membership = self.get_object()
        new_role = request.data.get("role")
        if not new_role:
            return Response({"detail": "role is required."}, status=400)

        # Validate role is a valid choice
        valid_roles = [choice[0] for choice in TeamMembership.ROLE_CHOICES]
        if new_role not in valid_roles:
            return Response({"role": [f'"{new_role}" is not a valid choice.']}, status=400)

        if new_role == "owner":
            return Response({"detail": "Use transfer-ownership to assign owner."}, status=400)
        if ROLE_ORDER.index(new_role) > ROLE_ORDER.index(caller_role):
            return Response({"detail": "Cannot assign a role higher than your own."}, status=400)
        if membership.role == "owner":
            return Response({"detail": "Cannot change the owner's role directly."}, status=400)

        membership.role = new_role
        membership.save()
        return Response(self.get_serializer(membership).data)

    def destroy(self, request, *args, **kwargs):
        team = self._get_team()
        caller_role = self._caller_role(team)
        membership = self.get_object()

        # Self-leave is always allowed (unless owner)
        is_self = membership.user == request.user
        if membership.role == "owner":
            return Response({"detail": "Owner cannot be removed. Transfer ownership first."}, status=400)
        if not is_self and caller_role not in ADMIN_ROLES:
            return Response(status=status.HTTP_403_FORBIDDEN)

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamGitCredentialViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GitCredentialSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def _get_team(self):
        return get_object_or_404(Team, pk=self.kwargs["team_pk"])

    def _check_membership(self, min_roles):
        team = self._get_team()
        if not TeamMembership.objects.filter(
            team=team, user=self.request.user, role__in=min_roles
        ).exists():
            raise PermissionDenied()
        return team

    def get_queryset(self):
        team_pk = self.kwargs["team_pk"]
        if not TeamMembership.objects.filter(team_id=team_pk, user=self.request.user).exists():
            raise PermissionDenied()
        return GitCredential.objects.filter(team_id=team_pk)

    def perform_create(self, serializer):
        team = self._check_membership(MANAGER_ROLES)
        serializer.save(user=self.request.user, team=team)

    def update(self, request, *args, **kwargs):
        self._check_membership(MANAGER_ROLES)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._check_membership(MANAGER_ROLES)
        return super().destroy(request, *args, **kwargs)


class TeamAPITokenViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = APITokenSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    PATCH_ALLOWED_FIELDS = {"name", "description", "is_active"}

    def _get_team(self):
        return get_object_or_404(Team, pk=self.kwargs["team_pk"])

    def _check_manager(self):
        team = self._get_team()
        if not TeamMembership.objects.filter(
            team=team, user=self.request.user, role__in=MANAGER_ROLES
        ).exists():
            raise PermissionDenied()
        return team

    def get_queryset(self):
        team_pk = self.kwargs["team_pk"]
        if not TeamMembership.objects.filter(team_id=team_pk, user=self.request.user).exists():
            raise PermissionDenied()
        return APIToken.objects.filter(team_id=team_pk).prefetch_related("knowledge_bases")

    def create(self, request, *args, **kwargs):
        team = self._check_manager()
        ser = APITokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        kb_ids = [str(uid) for uid in data.pop("kb_ids", [])]
        expires_in_days = data.pop("expires_in_days", None)

        kbs = []
        if kb_ids:
            kbs = list(KnowledgeBase.objects.filter(pk__in=kb_ids, team=team))
            if len(kbs) != len(kb_ids):
                return Response(
                    {"kb_ids": "One or more KBs do not belong to this team."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        expires_at = timezone.now() + timedelta(days=expires_in_days) if expires_in_days else None
        instance, raw_token = APIToken.create_token(
            user=request.user,
            name=data["name"],
            description=data.get("description", ""),
            knowledge_bases=kbs or None,
            expires_at=expires_at,
        )
        instance.team = team
        instance.save(update_fields=["team"])

        out = APITokenCreateSerializer(instance).data
        out["token"] = raw_token
        return Response(out, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        self._check_manager()
        unexpected = set(request.data.keys()) - self.PATCH_ALLOWED_FIELDS
        if unexpected:
            return Response(
                {"detail": f"Fields not allowed: {', '.join(sorted(unexpected))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._check_manager()
        return super().destroy(request, *args, **kwargs)
