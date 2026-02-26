import os
import logging
import uuid

from celery import shared_task

from apps.knowledge.models import Source
from apps.ingestion.extractors import extract_epub_text
from apps.ingestion.chunking import chunk_text
from apps.ingestion.embeddings import embed_documents
from apps.ingestion.tasks.common import download_to_tmp, upsert_chunks, BATCH_SIZE

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def ingest_epub(self, source_id: str) -> None:
    try:
        source = Source.objects.get(pk=uuid.UUID(source_id))
    except Source.DoesNotExist:
        logger.warning("Source %s was deleted before ingestion started, skipping.", source_id)
        return

    source.status = Source.Status.PROCESSING
    source.error_message = ""
    source.save(update_fields=["status", "error_message"])

    tmp_path = None
    try:
        tmp_path = download_to_tmp(source.storage_key)
        full_text = extract_epub_text(tmp_path)
        raw_chunks = chunk_text(full_text)

        if not raw_chunks:
            raise ValueError("No chunks extracted from EPUB")

        chunks_data = [
            {"chunk_index": i, "text": text, "page_number": 1}
            for i, text in enumerate(raw_chunks)
        ]

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
        if not Source.objects.filter(pk=source.pk).exists():
            logger.warning("Source %s was deleted during ingestion, discarding.", source_id)
            return
        logger.exception("EPUB ingestion failed for source %s", source_id)
        source.status = Source.Status.ERROR
        source.error_message = str(exc)
        source.save(update_fields=["status", "error_message"])

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
