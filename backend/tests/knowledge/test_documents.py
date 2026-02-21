import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="doc_alice", password="pw")


@pytest.fixture
def bob(db):
    return User.objects.create_user(username="doc_bob", password="pw")


@pytest.fixture
def alice_client(alice):
    client = APIClient()
    client.force_authenticate(user=alice)
    return client


@pytest.fixture
def pdf_source(alice):
    from apps.knowledge.models import KnowledgeBase, Source
    kb = KnowledgeBase.objects.create(name="Doc KB", owner=alice)
    return Source.objects.create(
        kb=kb,
        title="My PDF",
        source_type=Source.SourceType.PDF,
        storage_key="documents/test.pdf",
        status="ready",
    )


@pytest.fixture
def git_source(alice, tmp_path):
    from apps.knowledge.models import KnowledgeBase, Source
    kb = KnowledgeBase.objects.create(name="Git Doc KB", owner=alice)
    source = Source.objects.create(
        kb=kb,
        title="Git Repo",
        source_type=Source.SourceType.GIT,
        git_url="https://github.com/x/y.git",
        status="ready",
    )
    # Create a fake repo directory with a markdown file
    repo_dir = tmp_path / str(source.pk)
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("# Hello\n\nThis is the content.")
    return source, str(tmp_path)


@pytest.mark.django_db
class TestDocumentServing:
    def test_pdf_view_returns_presigned_url(self, alice_client, pdf_source):
        with patch("apps.knowledge.views.get_presigned_url", return_value="http://minio/doc.pdf?sig=abc"):
            response = alice_client.get(
                reverse("source-document", kwargs={"pk": str(pdf_source.pk)})
            )
        assert response.status_code == 200
        assert "url" in response.data
        assert response.data["url"] == "http://minio/doc.pdf?sig=abc"

    def test_non_accessible_source_returns_403(self, alice_client, bob):
        from apps.knowledge.models import KnowledgeBase, Source
        bob_kb = KnowledgeBase.objects.create(name="Bob KB", owner=bob)
        bob_source = Source.objects.create(
            kb=bob_kb,
            title="Bob's Doc",
            source_type=Source.SourceType.PDF,
            storage_key="documents/bob.pdf",
        )
        with patch("apps.knowledge.views.get_presigned_url", return_value="http://x/y"):
            response = alice_client.get(
                reverse("source-document", kwargs={"pk": str(bob_source.pk)})
            )
        assert response.status_code == 404

    def test_unauthenticated_returns_401(self, pdf_source):
        response = APIClient().get(
            reverse("source-document", kwargs={"pk": str(pdf_source.pk)})
        )
        assert response.status_code == 401

    def test_git_source_returns_file_content(self, alice_client, git_source, settings):
        source, tmp_dir = git_source
        settings.GIT_REPOS_DIR = tmp_dir
        response = alice_client.get(
            reverse("source-document", kwargs={"pk": str(source.pk)}),
            {"file": "README.md"},
        )
        assert response.status_code == 200
        assert "content" in response.data
        assert "Hello" in response.data["content"]

    def test_git_source_file_not_found_returns_404(self, alice_client, git_source, settings):
        source, tmp_dir = git_source
        settings.GIT_REPOS_DIR = tmp_dir
        response = alice_client.get(
            reverse("source-document", kwargs={"pk": str(source.pk)}),
            {"file": "nonexistent.md"},
        )
        assert response.status_code == 404
