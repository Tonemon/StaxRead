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
class TestGitCredentialAPI:
    def test_create_git_credential(self, alice_client):
        response = alice_client.post(
            reverse("gitcredential-list"),
            {"label": "My GitHub", "pat": "ghp_TestToken123"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["label"] == "My GitHub"

    def test_pat_not_returned_in_response(self, alice_client):
        response = alice_client.post(
            reverse("gitcredential-list"),
            {"label": "My GitLab", "pat": "glpat_SecretToken"},
            format="json",
        )
        assert response.status_code == 201
        assert "pat" not in response.data
        assert "pat_encrypted" not in response.data

    def test_user_only_sees_own_credentials(self, alice_client, bob_client, alice, bob):
        from apps.knowledge.models import GitCredential
        cred = GitCredential(user=alice, label="Alice's Cred")
        cred.set_pat("alice-token")
        cred.save()
        bob_cred = GitCredential(user=bob, label="Bob's Cred")
        bob_cred.set_pat("bob-token")
        bob_cred.save()

        response = alice_client.get(reverse("gitcredential-list"))
        labels = [c["label"] for c in response.data]
        assert "Alice's Cred" in labels
        assert "Bob's Cred" not in labels

    def test_user_cannot_access_others_credential(self, alice_client, bob, alice):
        from apps.knowledge.models import GitCredential
        cred = GitCredential(user=bob, label="Bob Only")
        cred.set_pat("bob-token")
        cred.save()

        response = alice_client.get(
            reverse("gitcredential-detail", kwargs={"pk": str(cred.pk)})
        )
        assert response.status_code == 404

    def test_unauthenticated_cannot_access(self, db):
        response = APIClient().get(reverse("gitcredential-list"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestSourceAPI:
    def test_create_source_for_kb(self, alice_client, alice):
        from apps.knowledge.models import KnowledgeBase, Source
        kb = KnowledgeBase.objects.create(name="Test KB", owner=alice)
        response = alice_client.post(
            reverse("source-list"),
            {
                "kb": str(kb.pk),
                "title": "My PDF",
                "source_type": Source.SourceType.PDF,
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["status"] == Source.Status.PENDING

    def test_user_only_sees_sources_in_accessible_kbs(self, alice_client, bob_client, alice, bob):
        from apps.knowledge.models import KnowledgeBase, Source
        alice_kb = KnowledgeBase.objects.create(name="Alice KB", owner=alice)
        bob_kb = KnowledgeBase.objects.create(name="Bob KB", owner=bob)
        Source.objects.create(kb=alice_kb, title="Alice Doc", source_type=Source.SourceType.PDF)
        Source.objects.create(kb=bob_kb, title="Bob Doc", source_type=Source.SourceType.PDF)

        response = alice_client.get(reverse("source-list"))
        titles = [s["title"] for s in response.data]
        assert "Alice Doc" in titles
        assert "Bob Doc" not in titles

    def test_unauthenticated_cannot_access_sources(self, db):
        response = APIClient().get(reverse("source-list"))
        assert response.status_code == 401
