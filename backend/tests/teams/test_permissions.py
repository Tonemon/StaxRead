import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password="pw")

@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bob", password="pw")


@pytest.mark.django_db
class TestTeamPermissions:
    def _make_request(self, user):
        request = APIRequestFactory().get("/")
        request.user = user
        return request

    def _setup(self, alice, bob, alice_role, bob_role):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)  # alice = owner
        if alice_role != "owner":
            TeamMembership.objects.filter(team=team, user=alice).update(role=alice_role)
        TeamMembership.objects.create(team=team, user=bob, role=bob_role)
        return team

    def test_manager_passes_is_team_manager(self, alice, bob):
        from apps.teams.permissions import IsTeamManager
        team = self._setup(alice, bob, "owner", "manager")
        perm = IsTeamManager()
        view = type("V", (), {"kwargs": {"pk": str(team.pk)}})()
        assert perm.has_permission(self._make_request(bob), view)

    def test_member_fails_is_team_manager(self, alice, bob):
        from apps.teams.permissions import IsTeamManager
        team = self._setup(alice, bob, "owner", "member")
        perm = IsTeamManager()
        view = type("V", (), {"kwargs": {"pk": str(team.pk)}})()
        assert not perm.has_permission(self._make_request(bob), view)

    def test_admin_passes_is_team_admin(self, alice, bob):
        from apps.teams.permissions import IsTeamAdmin
        team = self._setup(alice, bob, "owner", "admin")
        perm = IsTeamAdmin()
        view = type("V", (), {"kwargs": {"pk": str(team.pk)}})()
        assert perm.has_permission(self._make_request(bob), view)

    def test_manager_fails_is_team_admin(self, alice, bob):
        from apps.teams.permissions import IsTeamAdmin
        team = self._setup(alice, bob, "owner", "manager")
        perm = IsTeamAdmin()
        view = type("V", (), {"kwargs": {"pk": str(team.pk)}})()
        assert not perm.has_permission(self._make_request(bob), view)

    def test_manager_passes_with_team_pk_kwarg(self, alice, bob):
        from apps.teams.permissions import IsTeamManager
        team = self._setup(alice, bob, "owner", "manager")
        perm = IsTeamManager()
        # nested router uses team_pk instead of pk
        view = type("V", (), {"kwargs": {"team_pk": str(team.pk)}})()
        assert perm.has_permission(self._make_request(bob), view)
