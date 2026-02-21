import uuid
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, ANY


@pytest.fixture
def source(db):
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import KnowledgeBase, Source

    User = get_user_model()
    user = User.objects.create_user(username="taskuser", password="pw")
    kb = KnowledgeBase.objects.create(name="Task KB", owner=user)
    source = Source.objects.create(
        kb=kb,
        title="Test PDF",
        source_type=Source.SourceType.PDF,
        storage_key="documents/test.pdf",
    )
    return source


def make_sparse_vec():
    v = MagicMock()
    v.indices = np.array([1, 5], dtype=np.int32)
    v.values = np.array([0.5, 0.3], dtype=np.float32)
    return v


@pytest.mark.django_db
def test_ingest_pdf_creates_chunks_and_sets_ready(source):
    from apps.knowledge.models import Chunk, Source

    pages = [{"page_number": 1, "text": "Hello world from PDF."}]
    chunks_data = [{"chunk_index": 0, "text": "Hello world from PDF.", "page_number": 1}]
    dense = np.random.rand(1, 768).astype(np.float32)
    sparse = [make_sparse_vec()]

    mock_qdrant = MagicMock()
    with patch("apps.ingestion.tasks.pdf.download_to_tmp", return_value="/tmp/test.pdf"), \
         patch("apps.ingestion.tasks.pdf.extract_pdf_pages", return_value=pages), \
         patch("apps.ingestion.tasks.pdf.chunk_pages", return_value=chunks_data), \
         patch("apps.ingestion.tasks.pdf.embed_documents", return_value=(dense, sparse)), \
         patch("apps.ingestion.tasks.common.get_qdrant_client", return_value=mock_qdrant), \
         patch("apps.ingestion.tasks.pdf.os.unlink"):
        from apps.ingestion.tasks.pdf import ingest_pdf
        ingest_pdf(str(source.pk))

    source.refresh_from_db()
    assert source.status == Source.Status.READY
    assert Chunk.objects.filter(source=source).count() == 1
    mock_qdrant.upsert.assert_called_once()


@pytest.mark.django_db
def test_ingest_pdf_sets_error_on_failure(source):
    from apps.knowledge.models import Source

    with patch("apps.ingestion.tasks.pdf.download_to_tmp", side_effect=Exception("Download failed")):
        from apps.ingestion.tasks.pdf import ingest_pdf
        ingest_pdf(str(source.pk))

    source.refresh_from_db()
    assert source.status == Source.Status.ERROR
    assert "Download failed" in source.error_message


@pytest.mark.django_db
def test_ingest_pdf_sets_processing_during_run(source):
    from apps.knowledge.models import Source

    status_during_run = []

    def fake_extract(path):
        src = Source.objects.get(pk=source.pk)
        status_during_run.append(src.status)
        return [{"page_number": 1, "text": "text"}]

    with patch("apps.ingestion.tasks.pdf.download_to_tmp", return_value="/tmp/f.pdf"), \
         patch("apps.ingestion.tasks.pdf.extract_pdf_pages", side_effect=fake_extract), \
         patch("apps.ingestion.tasks.pdf.chunk_pages", return_value=[{"chunk_index": 0, "text": "t", "page_number": 1}]), \
         patch("apps.ingestion.tasks.pdf.embed_documents", return_value=(np.zeros((1, 768)), [make_sparse_vec()])), \
         patch("apps.ingestion.tasks.common.get_qdrant_client", return_value=MagicMock()), \
         patch("apps.ingestion.tasks.pdf.os.unlink"):
        from apps.ingestion.tasks.pdf import ingest_pdf
        ingest_pdf(str(source.pk))

    assert Source.Status.PROCESSING in status_during_run
