import logging
import os
import subprocess
import uuid
from typing import List, Dict
from urllib.parse import urlparse, urlunparse

from celery import shared_task
from django.conf import settings

from apps.knowledge.models import Source, Chunk
from apps.ingestion.chunking import chunk_text
from apps.ingestion.embeddings import embed_documents
from apps.ingestion.extractors import extract_pdf_pages
from apps.ingestion.chunking import chunk_pages
from apps.ingestion.tasks.common import upsert_chunks, BATCH_SIZE

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".pdf"}


def _build_auth_url(source: Source) -> str:
    """Build git clone URL with PAT token embedded if credentials exist."""
    if not source.git_credential:
        return source.git_url
    pat = source.git_credential.get_pat()
    parsed = urlparse(source.git_url)
    auth_netloc = f"{pat}@{parsed.netloc}"
    return urlunparse(parsed._replace(netloc=auth_netloc))


def _get_repo_path(source: Source) -> str:
    return os.path.join(settings.GIT_REPOS_DIR, str(source.pk))


def _clone_or_pull(source: Source) -> str:
    repo_path = _get_repo_path(source)
    auth_url = _build_auth_url(source)

    if os.path.exists(repo_path):
        subprocess.run(
            ["git", "-C", repo_path, "pull", "origin", source.git_branch],
            check=True, capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "clone", "--branch", source.git_branch, "--depth=1", auth_url, repo_path],
            check=True, capture_output=True,
        )
    return repo_path


def _discover_files(repo_path: str) -> List[str]:
    """Walk the repo and return supported files."""
    result = []
    for root, _, files in os.walk(repo_path):
        for fname in files:
            _, ext = os.path.splitext(fname)
            if ext.lower() in SUPPORTED_EXTENSIONS:
                result.append(os.path.join(root, fname))
    return result


def extract_markdown(file_path: str) -> Dict:
    """Read a Markdown file, extract first heading and full text."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    heading = ""
    for line in content.splitlines():
        stripped = line.lstrip("#").strip()
        if line.startswith("#") and stripped:
            heading = stripped
            break

    return {"text": content.strip(), "heading": heading}


def _ingest_file(source: Source, file_path: str, chunk_offset: int) -> int:
    """Ingest a single file and return the next chunk offset."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".md":
        info = extract_markdown(file_path)
        raw_chunks = chunk_text(info["text"])
        chunks_data = [
            {"chunk_index": chunk_offset + i, "text": t, "page_number": 1, "heading": info["heading"]}
            for i, t in enumerate(raw_chunks)
        ]
    elif ext == ".pdf":
        pages = extract_pdf_pages(file_path)
        raw_chunks_data = chunk_pages(pages)
        chunks_data = [
            {**cd, "chunk_index": chunk_offset + cd["chunk_index"]}
            for cd in raw_chunks_data
        ]
    else:
        return chunk_offset

    for batch_start in range(0, len(chunks_data), BATCH_SIZE):
        batch = chunks_data[batch_start:batch_start + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        dense, sparse = embed_documents(texts)
        upsert_chunks(source, batch, dense, sparse)

    return chunk_offset + len(chunks_data)


@shared_task(bind=True, max_retries=0)
def ingest_git(self, source_id: str) -> None:
    try:
        source = Source.objects.get(pk=uuid.UUID(source_id))
    except Source.DoesNotExist:
        logger.warning("Source %s was deleted before ingestion started, skipping.", source_id)
        return

    source.status = Source.Status.PROCESSING
    source.error_message = ""
    source.save(update_fields=["status", "error_message"])

    try:
        repo_path = _clone_or_pull(source)
        files = _discover_files(repo_path)

        # Delete existing chunks for re-ingestion
        source.chunks.all().delete()

        chunk_offset = 0
        for file_path in files:
            chunk_offset = _ingest_file(source, file_path, chunk_offset)

        from django.utils import timezone
        source.status = Source.Status.READY
        source.last_synced_at = timezone.now()
        source.save(update_fields=["status", "last_synced_at"])

    except Exception as exc:
        if not Source.objects.filter(pk=source.pk).exists():
            logger.warning("Source %s was deleted during ingestion, discarding.", source_id)
            return
        logger.exception("Git ingestion failed for source %s", source_id)
        source.status = Source.Status.ERROR
        source.error_message = str(exc)
        source.save(update_fields=["status", "error_message"])
