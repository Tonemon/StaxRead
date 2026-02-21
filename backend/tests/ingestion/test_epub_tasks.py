import uuid
import pytest
import numpy as np
from unittest.mock import MagicMock, patch


@pytest.fixture
def source(db):
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import KnowledgeBase, Source

    User = get_user_model()
    user = User.objects.create_user(username="epubuser", password="pw")
    kb = KnowledgeBase.objects.create(name="EPUB KB", owner=user)
    source = Source.objects.create(
        kb=kb,
        title="Test EPUB",
        source_type=Source.SourceType.EPUB,
        storage_key="documents/test.epub",
    )
    return source


def make_sparse_vec():
    v = MagicMock()
    v.indices = np.array([1, 5], dtype=np.int32)
    v.values = np.array([0.5, 0.3], dtype=np.float32)
    return v


@pytest.mark.django_db
def test_ingest_epub_creates_chunks_and_sets_ready(source):
    from apps.knowledge.models import Chunk, Source

    chunks_data = [{"chunk_index": 0, "text": "Chapter one text.", "page_number": 1}]
    dense = np.random.rand(1, 768).astype(np.float32)
    sparse = [make_sparse_vec()]

    mock_qdrant = MagicMock()
    with patch("apps.ingestion.tasks.epub.download_to_tmp", return_value="/tmp/test.epub"), \
         patch("apps.ingestion.tasks.epub.extract_epub_text", return_value="Chapter one text."), \
         patch("apps.ingestion.tasks.epub.chunk_text", return_value=["Chapter one text."]), \
         patch("apps.ingestion.tasks.epub.embed_documents", return_value=(dense, sparse)), \
         patch("apps.ingestion.tasks.common.get_qdrant_client", return_value=mock_qdrant), \
         patch("apps.ingestion.tasks.epub.os.unlink"):
        from apps.ingestion.tasks.epub import ingest_epub
        ingest_epub(str(source.pk))

    source.refresh_from_db()
    assert source.status == Source.Status.READY
    assert Chunk.objects.filter(source=source).count() == 1
    mock_qdrant.upsert.assert_called_once()


@pytest.mark.django_db
def test_ingest_epub_sets_error_on_failure(source):
    from apps.knowledge.models import Source

    with patch("apps.ingestion.tasks.epub.download_to_tmp", side_effect=Exception("Network error")):
        from apps.ingestion.tasks.epub import ingest_epub
        ingest_epub(str(source.pk))

    source.refresh_from_db()
    assert source.status == Source.Status.ERROR
    assert "Network error" in source.error_message


@pytest.mark.django_db
def test_ingest_epub_sets_processing_during_run(source):
    from apps.knowledge.models import Source

    status_during_run = []

    def fake_extract(path):
        src = Source.objects.get(pk=source.pk)
        status_during_run.append(src.status)
        return "Some text"

    with patch("apps.ingestion.tasks.epub.download_to_tmp", return_value="/tmp/f.epub"), \
         patch("apps.ingestion.tasks.epub.extract_epub_text", side_effect=fake_extract), \
         patch("apps.ingestion.tasks.epub.chunk_text", return_value=["Some text"]), \
         patch("apps.ingestion.tasks.epub.embed_documents", return_value=(np.zeros((1, 768)), [make_sparse_vec()])), \
         patch("apps.ingestion.tasks.common.get_qdrant_client", return_value=MagicMock()), \
         patch("apps.ingestion.tasks.epub.os.unlink"):
        from apps.ingestion.tasks.epub import ingest_epub
        ingest_epub(str(source.pk))

    assert Source.Status.PROCESSING in status_during_run
