from django.db.models import Q
from apps.knowledge.models import KnowledgeBase, KBAccess

MANAGER_ROLES = ("manager", "admin", "owner")


def get_accessible_kbs(user):
    """
    Return a KnowledgeBase queryset containing all KBs the user can access:
      1. Personal KBs: user is owner (auto KBAccess created on save)
      2. Team KBs (manager+): implicit via TeamMembership role
      3. Team/personal KBs with explicit KBAccess (guest/member/external/personal share)

    Cases 1 and 3 are both covered by the KBAccess row check; case 2 is explicit.
    """
    from apps.teams.models import TeamMembership
    manager_team_ids = TeamMembership.objects.filter(
        user=user, role__in=MANAGER_ROLES
    ).values_list("team_id", flat=True)

    return KnowledgeBase.objects.filter(
        Q(access_entries__user=user, access_entries__status=KBAccess.Status.ACCEPTED)
        | Q(team__in=manager_team_ids)
    ).distinct()
