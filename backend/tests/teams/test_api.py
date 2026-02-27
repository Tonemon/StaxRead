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
def carol(db):
    return User.objects.create_user(username="carol", password="pw")

@pytest.fixture
def alice_client(alice):
    c = APIClient()
    c.force_authenticate(user=alice)
    return c

@pytest.fixture
def bob_client(bob):
    c = APIClient()
    c.force_authenticate(user=bob)
    return c


@pytest.mark.django_db
class TestTeamCRUD:
    def test_create_team(self, alice_client, alice):
        from apps.teams.models import TeamMembership
        resp = alice_client.post(reverse("team-list"), {"name": "Eng"}, format="json")
        assert resp.status_code == 201
        assert resp.data["name"] == "Eng"
        assert resp.data["my_role"] == "owner"
        assert TeamMembership.objects.filter(user=alice, role="owner").exists()

    def test_list_only_own_teams(self, alice_client, bob_client, alice, bob):
        from apps.teams.models import Team
        Team.create(name="Alice Team", created_by=alice)
        Team.create(name="Bob Team", created_by=bob)
        resp = alice_client.get(reverse("team-list"))
        names = [t["name"] for t in resp.data]
        assert "Alice Team" in names
        assert "Bob Team" not in names

    def test_admin_can_patch_team(self, alice_client):
        from apps.teams.models import Team
        resp = alice_client.post(reverse("team-list"), {"name": "Old"}, format="json")
        team_id = resp.data["id"]
        resp = alice_client.patch(
            reverse("team-detail", kwargs={"pk": team_id}),
            {"name": "New"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "New"

    def test_owner_can_delete_team(self, alice_client):
        from apps.teams.models import Team
        resp = alice_client.post(reverse("team-list"), {"name": "DeleteMe"}, format="json")
        team_id = resp.data["id"]
        resp = alice_client.delete(reverse("team-detail", kwargs={"pk": team_id}))
        assert resp.status_code == 204


@pytest.mark.django_db
class TestTeamMembers:
    def test_admin_can_invite_member(self, alice_client, bob, alice):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)
        resp = alice_client.post(
            reverse("team-members-list", kwargs={"team_pk": str(team.pk)}),
            {"user_id": str(bob.pk), "role": "member"}, format="json"
        )
        assert resp.status_code == 201
        assert TeamMembership.objects.filter(team=team, user=bob, role="member").exists()

    def test_member_cannot_invite(self, bob_client, alice, bob, carol):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="member")
        resp = bob_client.post(
            reverse("team-members-list", kwargs={"team_pk": str(team.pk)}),
            {"user_id": str(carol.pk), "role": "member"}, format="json"
        )
        assert resp.status_code == 403

    def test_admin_can_change_role(self, alice_client, alice, bob):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="member")
        resp = alice_client.patch(
            reverse("team-members-detail", kwargs={"team_pk": str(team.pk), "pk": str(bob.pk)}),
            {"role": "manager"}, format="json"
        )
        assert resp.status_code == 200
        assert TeamMembership.objects.get(team=team, user=bob).role == "manager"

    def test_admin_cannot_promote_to_owner(self, alice_client, bob, carol, alice):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="admin")
        TeamMembership.objects.create(team=team, user=carol, role="member")
        bob_client = APIClient()
        bob_client.force_authenticate(user=bob)
        resp = bob_client.patch(
            reverse("team-members-detail", kwargs={"team_pk": str(team.pk), "pk": str(carol.pk)}),
            {"role": "owner"}, format="json"
        )
        assert resp.status_code == 400

    def test_owner_can_transfer_ownership(self, alice_client, alice, bob):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Eng", created_by=alice)
        TeamMembership.objects.create(team=team, user=bob, role="member")
        resp = alice_client.post(
            reverse("team-transfer-ownership", kwargs={"pk": str(team.pk)}),
            {"user_id": str(bob.pk)}, format="json"
        )
        assert resp.status_code == 200
        assert TeamMembership.objects.get(team=team, user=bob).role == "owner"
        assert TeamMembership.objects.get(team=team, user=alice).role == "admin"
