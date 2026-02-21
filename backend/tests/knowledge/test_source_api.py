import io
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice_src", password="pw")


@pytest.fixture
def alice_client(alice):
    client = APIClient()
    client.force_authenticate(user=alice)
    return client


@pytest.fixture
def kb(alice):
    from apps.knowledge.models import KnowledgeBase
    return KnowledgeBase.objects.create(name="Test KB", owner=alice)


@pytest.mark.django_db
class TestSourceAPIIngestionTrigger:
    def test_create_git_source_triggers_ingest_git(self, alice_client, kb):
        from unittest.mock import patch
        with patch("apps.knowledge.views.ingest_git.delay") as mock_delay:
            response = alice_client.post(
                reverse("source-list"),
                {
                    "kb": str(kb.pk),
                    "title": "My Repo",
                    "source_type": "git",
                    "git_url": "https://github.com/example/repo.git",
                },
                format="json",
            )
        assert response.status_code == 201
        mock_delay.assert_called_once_with(response.data["id"])

    def test_create_epub_source_triggers_ingest_epub(self, alice_client, kb):
        from unittest.mock import patch
        epub_file = io.BytesIO(b"PK\x03\x04" + b"\x00" * 100)
        epub_file.name = "book.epub"
        with patch("apps.knowledge.views.ingest_epub.delay") as mock_delay, \
             patch("apps.knowledge.views.upload_file", return_value="documents/test.epub"):
            response = alice_client.post(
                reverse("source-list"),
                {
                    "kb": str(kb.pk),
                    "title": "My EPUB",
                    "source_type": "epub",
                    "file": epub_file,
                },
                format="multipart",
            )
        assert response.status_code == 201
        mock_delay.assert_called_once()

    def test_create_pdf_source_triggers_ingest_pdf(self, alice_client, kb):
        from unittest.mock import patch
        pdf_file = io.BytesIO(b"%PDF-1.4 test content")
        pdf_file.name = "doc.pdf"
        with patch("apps.knowledge.views.ingest_pdf.delay") as mock_delay, \
             patch("apps.knowledge.views.upload_file", return_value="documents/test.pdf"):
            response = alice_client.post(
                reverse("source-list"),
                {
                    "kb": str(kb.pk),
                    "title": "My PDF",
                    "source_type": "pdf",
                    "file": pdf_file,
                },
                format="multipart",
            )
        assert response.status_code == 201
        mock_delay.assert_called_once()

    def test_source_status_action_returns_current_status(self, alice_client, kb):
        from apps.knowledge.models import Source
        source = Source.objects.create(
            kb=kb,
            title="Status Test",
            source_type=Source.SourceType.GIT,
            git_url="https://github.com/x/y.git",
        )
        response = alice_client.get(
            reverse("source-status", kwargs={"pk": str(source.pk)})
        )
        assert response.status_code == 200
        assert "status" in response.data
        assert "error_message" in response.data

    def test_source_status_returns_error_message_when_failed(self, alice_client, kb):
        from apps.knowledge.models import Source
        source = Source.objects.create(
            kb=kb,
            title="Error Source",
            source_type=Source.SourceType.GIT,
            git_url="https://github.com/x/y.git",
            status=Source.Status.ERROR,
            error_message="Connection refused",
        )
        response = alice_client.get(
            reverse("source-status", kwargs={"pk": str(source.pk)})
        )
        assert response.status_code == 200
        assert response.data["status"] == Source.Status.ERROR
        assert "Connection refused" in response.data["error_message"]
