from rest_framework.permissions import BasePermission
from apps.teams.models import TeamMembership

MANAGER_ROLES = ("manager", "admin", "owner")
ADMIN_ROLES = ("admin", "owner")


def _get_team_pk(view):
    """Extract team PK from view kwargs (handles both 'pk' and 'team_pk')."""
    return view.kwargs.get("team_pk") or view.kwargs.get("pk")


class IsTeamMember(BasePermission):
    """User has any membership in the team."""
    def has_permission(self, request, view):
        team_pk = _get_team_pk(view)
        if not team_pk:
            return False
        return TeamMembership.objects.filter(
            team_id=team_pk, user=request.user
        ).exists()


class IsTeamManager(BasePermission):
    """User is Manager, Admin, or Owner of the team."""
    def has_permission(self, request, view):
        team_pk = _get_team_pk(view)
        if not team_pk:
            return False
        return TeamMembership.objects.filter(
            team_id=team_pk, user=request.user, role__in=MANAGER_ROLES
        ).exists()


class IsTeamAdmin(BasePermission):
    """User is Admin or Owner of the team."""
    def has_permission(self, request, view):
        team_pk = _get_team_pk(view)
        if not team_pk:
            return False
        return TeamMembership.objects.filter(
            team_id=team_pk, user=request.user, role__in=ADMIN_ROLES
        ).exists()


class IsTeamOwner(BasePermission):
    """User is Owner of the team."""
    def has_permission(self, request, view):
        team_pk = _get_team_pk(view)
        if not team_pk:
            return False
        return TeamMembership.objects.filter(
            team_id=team_pk, user=request.user, role="owner"
        ).exists()
