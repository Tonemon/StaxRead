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

    def test_save_without_created_by_raises(self):
        # Team.objects.create() bypasses the classmethod and omits created_by.
        # The save() guard must catch this so no ownerless team can be persisted.
        from apps.teams.models import Team
        with pytest.raises(ValueError, match="created_by is required"):
            Team.objects.create(name="Orphan")

    def test_save_update_does_not_require_created_by(self, alice):
        # The created_by guard must only fire on INSERT, not on subsequent UPDATE.
        from apps.teams.models import Team
        team = Team.create(name="Engineering", created_by=alice)
        team.name = "Engineering (renamed)"
        team.save()  # must not raise
        team.refresh_from_db()
        assert team.name == "Engineering (renamed)"


@pytest.mark.django_db
class TestTeamFK:
    def test_kb_can_belong_to_team(self, alice):
        from apps.teams.models import Team
        from apps.knowledge.models import KnowledgeBase
        team = Team.create(name="Eng", created_by=alice)
        kb = KnowledgeBase.objects.create(name="Docs", owner=alice, team=team)
        assert kb.team == team

    def test_personal_kb_has_no_team(self, alice):
        from apps.knowledge.models import KnowledgeBase
        kb = KnowledgeBase.objects.create(name="Personal", owner=alice)
        assert kb.team is None

    def test_personal_kb_auto_creates_kbaccess(self, alice):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Personal", owner=alice)
        assert KBAccess.objects.filter(kb=kb, user=alice).exists()

    def test_team_kb_does_not_auto_create_kbaccess(self, alice):
        from apps.teams.models import Team
        from apps.knowledge.models import KnowledgeBase, KBAccess
        team = Team.create(name="Eng", created_by=alice)
        kb = KnowledgeBase.objects.create(name="Team Docs", owner=alice, team=team)
        assert not KBAccess.objects.filter(kb=kb, user=alice).exists()
