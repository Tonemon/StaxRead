from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.knowledge.models import KnowledgeBase, KBAccess, Source

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


class SourceWritePermissionTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="sowner", password="pw")
        self.reader = User.objects.create_user(username="sreader", password="pw")
        self.writer = User.objects.create_user(username="swriter", password="pw")
        self.kb = KnowledgeBase.objects.create(name="SrcKB", owner=self.owner)
        KBAccess.objects.create(
            kb=self.kb, user=self.reader, status=KBAccess.Status.ACCEPTED,
            permission=KBAccess.Permission.READ
        )
        KBAccess.objects.create(
            kb=self.kb, user=self.writer, status=KBAccess.Status.ACCEPTED,
            permission=KBAccess.Permission.WRITE
        )
        self.source = Source.objects.create(
            kb=self.kb, title="Doc", source_type="pdf", status="ready"
        )
        self.client = APIClient()

    def test_read_user_cannot_delete_source(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.delete(f"/api/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_write_user_can_delete_source(self):
        self.client.force_authenticate(user=self.writer)
        response = self.client.delete(f"/api/sources/{self.source.pk}/")
        self.assertEqual(response.status_code, 204)

    def test_read_user_cannot_create_source(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.post("/api/sources/", {
            "kb": str(self.kb.pk),
            "title": "Blocked Doc",
            "source_type": "pdf",
        }, format="json")
        self.assertEqual(response.status_code, 403)
