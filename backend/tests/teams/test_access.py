import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password="pw")

@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bob", password="pw")

@pytest.fixture
def carol(db):
    return User.objects.create_user(username="carol", password="pw")


@pytest.mark.django_db
class TestGetAccessibleKbs:
    def _ids(self, qs):
        return set(str(pk) for pk in qs.values_list("id", flat=True))

    def test_personal_owner_sees_own_kb(self, alice):
        from apps.knowledge.models import KnowledgeBase
        from apps.teams.access import get_accessible_kbs
        kb = KnowledgeBase.objects.create(name="Mine", owner=alice)
        assert str(kb.pk) in self._ids(get_accessible_kbs(alice))

    def test_personal_owner_does_not_see_others(self, alice, bob):
        from apps.knowledge.models import KnowledgeBase
        from apps.teams.access import get_accessible_kbs
        KnowledgeBase.objects.create(name="Bob's", owner=bob)
        result_ids = self._ids(get_accessible_kbs(alice))
        bob_kb_ids = self._ids(KnowledgeBase.objects.filter(owner=bob))
        assert not result_ids.intersection(bob_kb_ids)

    def test_manager_sees_team_kb_implicitly(self, alice, bob):
        from apps.teams.models import Team, TeamMembership
        from apps.knowledge.models import KnowledgeBase
        from apps.teams.access import get_accessible_kbs
        team = Team.create(name="Eng", created_by=alice)  # alice is owner
        TeamMembership.objects.create(team=team, user=bob, role="manager")
        kb = KnowledgeBase.objects.create(name="Team KB", owner=alice, team=team)
        assert str(kb.pk) in self._ids(get_accessible_kbs(bob))

    def test_guest_does_not_see_team_kb_without_explicit_access(self, alice, bob):
        from apps.teams.models import Team, TeamMembership
        from apps.knowledge.models import KnowledgeBase
        from apps.teams.access import get_accessible_kbs
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="guest")
        KnowledgeBase.objects.create(name="Team KB", owner=alice, team=team)
        # bob is guest with no KBAccess -> should NOT see it
        assert not self._ids(get_accessible_kbs(bob))

    def test_guest_sees_team_kb_with_explicit_access(self, alice, bob):
        from apps.teams.models import Team, TeamMembership
        from apps.knowledge.models import KnowledgeBase, KBAccess
        from apps.teams.access import get_accessible_kbs
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="guest")
        kb = KnowledgeBase.objects.create(name="Team KB", owner=alice, team=team)
        KBAccess.objects.create(kb=kb, user=bob, status="accepted")
        assert str(kb.pk) in self._ids(get_accessible_kbs(bob))

    def test_external_user_sees_team_kb_via_kbaccess(self, alice, carol):
        from apps.teams.models import Team
        from apps.knowledge.models import KnowledgeBase, KBAccess
        from apps.teams.access import get_accessible_kbs
        team = Team.create(name="Eng", created_by=alice)
        kb = KnowledgeBase.objects.create(name="Team KB", owner=alice, team=team)
        # carol has no team membership, just a KBAccess
        KBAccess.objects.create(kb=kb, user=carol, status="accepted")
        assert str(kb.pk) in self._ids(get_accessible_kbs(carol))
