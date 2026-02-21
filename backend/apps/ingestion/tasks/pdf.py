import os
import logging
import uuid

from celery import shared_task

from apps.knowledge.models import Source
from apps.ingestion.extractors import extract_pdf_pages
from apps.ingestion.chunking import chunk_pages
from apps.ingestion.embeddings import embed_documents
from apps.ingestion.tasks.common import download_to_tmp, upsert_chunks, BATCH_SIZE

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def ingest_pdf(self, source_id: str) -> None:
    source = Source.objects.get(pk=uuid.UUID(source_id))
    source.status = Source.Status.PROCESSING
    source.error_message = ""
    source.save(update_fields=["status", "error_message"])

    tmp_path = None
    try:
        tmp_path = download_to_tmp(source.storage_key)
        pages = extract_pdf_pages(tmp_path)
        chunks_data = chunk_pages(pages)

        if not chunks_data:
            raise ValueError("No chunks extracted from PDF")

        # Delete existing chunks for re-ingestion support
        source.chunks.all().delete()

        for batch_start in range(0, len(chunks_data), BATCH_SIZE):
            batch = chunks_data[batch_start:batch_start + BATCH_SIZE]
            texts = [c["text"] for c in batch]
            dense, sparse = embed_documents(texts)
            upsert_chunks(source, batch, dense, sparse)

        source.status = Source.Status.READY
        source.save(update_fields=["status"])

    except Exception as exc:
        logger.exception("PDF ingestion failed for source %s", source_id)
        source.status = Source.Status.ERROR
        source.error_message = str(exc)
        source.save(update_fields=["status", "error_message"])

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
