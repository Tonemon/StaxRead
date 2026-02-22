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
    client = APIClient()
    client.force_authenticate(user=alice)
    return client


@pytest.fixture
def bob_client(bob):
    client = APIClient()
    client.force_authenticate(user=bob)
    return client


@pytest.mark.django_db
class TestKnowledgeBaseAPI:
    def test_user_can_create_kb(self, alice_client):
        response = alice_client.post(
            reverse("knowledgebase-list"),
            {"name": "Alice's KB", "description": "Test"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["name"] == "Alice's KB"

    def test_user_only_sees_accessible_kbs(self, alice_client, bob_client, alice, bob):
        from apps.knowledge.models import KnowledgeBase
        alice_kb = KnowledgeBase.objects.create(name="Alice KB", owner=alice)
        bob_kb = KnowledgeBase.objects.create(name="Bob KB", owner=bob)

        response = alice_client.get(reverse("knowledgebase-list"))
        assert response.status_code == 200
        names = [kb["name"] for kb in response.data]
        assert "Alice KB" in names
        assert "Bob KB" not in names

    def test_owner_can_delete_kb(self, alice_client, alice):
        from apps.knowledge.models import KnowledgeBase
        kb = KnowledgeBase.objects.create(name="Delete Me", owner=alice)
        response = alice_client.delete(
            reverse("knowledgebase-detail", kwargs={"pk": str(kb.pk)})
        )
        assert response.status_code == 204

    def test_non_owner_cannot_delete_kb(self, alice_client, bob_client, alice, bob):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Alice's Protected KB", owner=alice)
        KBAccess.objects.create(kb=kb, user=bob)
        response = bob_client.delete(
            reverse("knowledgebase-detail", kwargs={"pk": str(kb.pk)})
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_kbs(self, db):
        response = APIClient().get(reverse("knowledgebase-list"))
        assert response.status_code == 401

    def test_owner_can_share_kb_with_another_user(self, alice_client, alice, bob):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Shareable KB", owner=alice)
        response = alice_client.post(
            reverse("knowledgebase-share", kwargs={"pk": str(kb.pk)}),
            {"user_id": str(bob.pk)},
            format="json",
        )
        assert response.status_code == 200
        assert KBAccess.objects.filter(kb=kb, user=bob).exists()

    def test_shared_user_sees_kb_in_list(self, alice_client, bob_client, alice, bob):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Shared to Bob", owner=alice)
        KBAccess.objects.create(kb=kb, user=bob)

        response = bob_client.get(reverse("knowledgebase-list"))
        names = [kb["name"] for kb in response.data]
        assert "Shared to Bob" in names

    def test_non_owner_cannot_share_kb(self, alice_client, bob_client, alice, bob):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Bob's KB", owner=bob)
        KBAccess.objects.create(kb=kb, user=alice)
        response = alice_client.post(
            reverse("knowledgebase-share", kwargs={"pk": str(kb.pk)}),
            {"user_id": str(bob.pk)},
            format="json",
        )
        assert response.status_code == 403

    def test_owner_can_unshare_kb(self, alice_client, alice, bob):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Unshare KB", owner=alice)
        KBAccess.objects.create(kb=kb, user=bob)

        response = alice_client.post(
            reverse("knowledgebase-unshare", kwargs={"pk": str(kb.pk)}),
            {"user_id": str(bob.pk)},
            format="json",
        )
        assert response.status_code == 200
        assert not KBAccess.objects.filter(kb=kb, user=bob).exists()
