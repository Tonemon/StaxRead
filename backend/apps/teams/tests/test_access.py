from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.knowledge.models import KnowledgeBase, KBAccess
from apps.teams.models import Team, TeamMembership
from apps.teams.access import get_accessible_kbs, has_write_permission

User = get_user_model()


class GetAccessibleKBsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pw")
        self.manager = User.objects.create_user(username="manager", password="pw")
        self.member = User.objects.create_user(username="member", password="pw")
        self.guest = User.objects.create_user(username="guest", password="pw")
        self.team = Team.create(name="Team A", created_by=self.owner)
        TeamMembership.objects.create(team=self.team, user=self.manager, role="manager")
        TeamMembership.objects.create(team=self.team, user=self.member, role="member")
        TeamMembership.objects.create(team=self.team, user=self.guest, role="guest")
        self.team_kb = KnowledgeBase.objects.create(
            name="Team KB", owner=self.owner, team=self.team
        )

    def test_manager_can_access_team_kb(self):
        qs = get_accessible_kbs(self.manager)
        self.assertIn(self.team_kb, qs)

    def test_member_can_access_team_kb(self):
        qs = get_accessible_kbs(self.member)
        self.assertIn(self.team_kb, qs)

    def test_guest_can_access_team_kb(self):
        qs = get_accessible_kbs(self.guest)
        self.assertIn(self.team_kb, qs)


class HasWritePermissionTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pw")
        self.reader = User.objects.create_user(username="reader", password="pw")
        self.writer = User.objects.create_user(username="writer", password="pw")
        self.kb = KnowledgeBase.objects.create(name="KB", owner=self.owner)
        KBAccess.objects.create(
            kb=self.kb, user=self.reader, status=KBAccess.Status.ACCEPTED,
            permission=KBAccess.Permission.READ
        )
        KBAccess.objects.create(
            kb=self.kb, user=self.writer, status=KBAccess.Status.ACCEPTED,
            permission=KBAccess.Permission.WRITE
        )
        self.team_owner = User.objects.create_user(username="towner", password="pw")
        self.team_member = User.objects.create_user(username="tmember", password="pw")
        self.team_manager = User.objects.create_user(username="tmanager", password="pw")
        self.team = Team.create(name="T", created_by=self.team_owner)
        TeamMembership.objects.create(team=self.team, user=self.team_manager, role="manager")
        TeamMembership.objects.create(team=self.team, user=self.team_member, role="member")
        self.team_kb = KnowledgeBase.objects.create(
            name="Team KB", owner=self.team_owner, team=self.team
        )

    def test_personal_kb_owner_has_write(self):
        self.assertTrue(has_write_permission(self.owner, self.kb))

    def test_read_user_does_not_have_write(self):
        self.assertFalse(has_write_permission(self.reader, self.kb))

    def test_write_user_has_write(self):
        self.assertTrue(has_write_permission(self.writer, self.kb))

    def test_team_manager_has_write_on_team_kb(self):
        self.assertTrue(has_write_permission(self.team_manager, self.team_kb))

    def test_team_member_does_not_have_write_on_team_kb(self):
        self.assertFalse(has_write_permission(self.team_member, self.team_kb))
