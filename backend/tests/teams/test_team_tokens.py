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
class TestTeamAPITokens:
    def test_manager_can_create_team_token(self, alice_client, alice):
        from apps.teams.models import Team
        team = Team.create(name="Eng", created_by=alice)
        resp = alice_client.post(
            reverse("team-api-tokens-list", kwargs={"team_pk": str(team.pk)}),
            {"name": "CI Token"},
            format="json",
        )
        assert resp.status_code == 201
        assert "token" in resp.data
        assert resp.data["token"].startswith("stax_")

    def test_member_cannot_create_team_token(self, alice_client, bob_client, alice, bob):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="member")
        resp = bob_client.post(
            reverse("team-api-tokens-list", kwargs={"team_pk": str(team.pk)}),
            {"name": "Token"},
            format="json",
        )
        assert resp.status_code == 403

    def test_team_token_scoped_to_team_kbs(self, alice_client, alice):
        from apps.teams.models import Team
        from apps.knowledge.models import KnowledgeBase
        team = Team.create(name="Eng", created_by=alice)
        kb = KnowledgeBase.objects.create(name="Team KB", owner=alice, team=team)
        resp = alice_client.post(
            reverse("team-api-tokens-list", kwargs={"team_pk": str(team.pk)}),
            {"name": "CI Token", "kb_ids": [str(kb.pk)]},
            format="json",
        )
        assert resp.status_code == 201

    def test_team_token_rejects_non_team_kb(self, alice_client, alice, bob):
        from apps.teams.models import Team
        from apps.knowledge.models import KnowledgeBase
        team = Team.create(name="Eng", created_by=alice)
        personal_kb = KnowledgeBase.objects.create(name="Personal", owner=alice)
        resp = alice_client.post(
            reverse("team-api-tokens-list", kwargs={"team_pk": str(team.pk)}),
            {"name": "CI Token", "kb_ids": [str(personal_kb.pk)]},
            format="json",
        )
        assert resp.status_code == 400
