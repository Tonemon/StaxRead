from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.knowledge.models import KnowledgeBase, KBAccess

User = get_user_model()


class KBAccessPermissionTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pw")
        self.kb = KnowledgeBase.objects.create(name="Test KB", owner=self.owner)

    def test_owner_access_entry_has_write_permission(self):
        entry = KBAccess.objects.get(kb=self.kb, user=self.owner)
        self.assertEqual(entry.permission, KBAccess.Permission.WRITE)

    def test_invited_user_gets_read_permission_by_default(self):
        other = User.objects.create_user(username="other", password="pw")
        entry = KBAccess.objects.create(
            kb=self.kb, user=other, status=KBAccess.Status.PENDING
        )
        self.assertEqual(entry.permission, KBAccess.Permission.READ)
