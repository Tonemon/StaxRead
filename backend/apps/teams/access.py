from django.db.models import Q
from apps.knowledge.models import KnowledgeBase, KBAccess

MANAGER_ROLES = ("manager", "admin", "owner")
# Roles that may add/delete sources on a team KB. Guests are read-only.
WRITE_ROLES = ("member", "manager", "admin", "owner")


def get_accessible_kbs(user):
    """
    Return a KnowledgeBase queryset containing all KBs the user can access:
      1. Personal KBs: user has an accepted KBAccess entry (owner auto-gets one on create)
      2. Team KBs: user is any member of the team (all roles get read access)
    """
    from apps.teams.models import TeamMembership
    member_team_ids = TeamMembership.objects.filter(
        user=user
    ).values_list("team_id", flat=True)

    return KnowledgeBase.objects.filter(
        Q(access_entries__user=user, access_entries__status=KBAccess.Status.ACCEPTED)
        | Q(team__in=member_team_ids)
    ).distinct()


def has_write_permission(user, kb) -> bool:
    """
    Return True if the user may add or delete sources on this KB.

    Personal KB:  owner always has write; invited users need permission='write'.
    Team KB:      team role member/manager/admin/owner → write; guest → read.
                  External users (KBAccess entry, not team members) use their explicit permission.
    """
    from apps.teams.models import TeamMembership

    if kb.team_id:
        # Team members: role determines write access (member and above)
        try:
            tm = TeamMembership.objects.get(team_id=kb.team_id, user=user)
            if tm.role in WRITE_ROLES:
                return True
        except TeamMembership.DoesNotExist:
            pass
        # External user with explicit KBAccess (not a team member)
        try:
            access = KBAccess.objects.get(
                kb=kb, user=user, status=KBAccess.Status.ACCEPTED
            )
            return access.permission == KBAccess.Permission.WRITE
        except KBAccess.DoesNotExist:
            return False
    else:
        # Personal KB: owner always has write
        if kb.owner_id == user.pk:
            return True
        try:
            access = KBAccess.objects.get(
                kb=kb, user=user, status=KBAccess.Status.ACCEPTED
            )
            return access.permission == KBAccess.Permission.WRITE
        except KBAccess.DoesNotExist:
            return False
