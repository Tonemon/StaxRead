import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password="pw")

@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bob", password="pw")

@pytest.fixture
def alice_client(alice):
    c = APIClient(); c.force_authenticate(user=alice); return c

@pytest.fixture
def bob_client(bob):
    c = APIClient(); c.force_authenticate(user=bob); return c


@pytest.mark.django_db
class TestTeamGitCredentials:
    def test_manager_can_create_team_credential(self, alice_client, alice):
        from apps.teams.models import Team
        team = Team.create(name="Eng", created_by=alice)
        resp = alice_client.post(
            reverse("team-git-credentials-list", kwargs={"team_pk": str(team.pk)}),
            {"label": "GitHub PAT", "pat": "ghp_test123"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["label"] == "GitHub PAT"

    def test_member_cannot_create_team_credential(self, alice_client, bob_client, alice, bob):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="member")
        resp = bob_client.post(
            reverse("team-git-credentials-list", kwargs={"team_pk": str(team.pk)}),
            {"label": "PAT", "pat": "token"},
            format="json",
        )
        assert resp.status_code == 403

    def test_team_credential_not_visible_to_non_members(self, alice_client, bob_client, alice):
        from apps.teams.models import Team
        team = Team.create(name="Eng", created_by=alice)
        alice_client.post(
            reverse("team-git-credentials-list", kwargs={"team_pk": str(team.pk)}),
            {"label": "PAT", "pat": "token"},
            format="json",
        )
        resp = bob_client.get(
            reverse("team-git-credentials-list", kwargs={"team_pk": str(team.pk)})
        )
        assert resp.status_code == 403
