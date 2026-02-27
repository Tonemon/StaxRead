import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password="pw")


@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bob", password="pw")


@pytest.mark.django_db
class TestTeamModel:
    def test_create_team(self, alice):
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Engineering", created_by=alice)
        assert team.pk is not None
        assert TeamMembership.objects.filter(team=team, user=alice, role="owner").exists()

    def test_team_str(self, alice):
        from apps.teams.models import Team
        team = Team.create(name="Engineering", created_by=alice)
        assert str(team) == "Engineering"

    def test_unique_membership(self, alice):
        from django.db import IntegrityError
        from apps.teams.models import Team, TeamMembership
        team = Team.create(name="Engineering", created_by=alice)
        with pytest.raises(IntegrityError):
            TeamMembership.objects.create(team=team, user=alice, role="member")
