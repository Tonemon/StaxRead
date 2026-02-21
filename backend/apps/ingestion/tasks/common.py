import os
import tempfile
import uuid
from typing import List, Dict

import numpy as np
from django.conf import settings

from apps.knowledge.models import Chunk, Source
from apps.ingestion.embeddings import embed_documents
from apps.ingestion.qdrant_client import get_qdrant_client


BATCH_SIZE = 64


def download_to_tmp(storage_key: str) -> str:
    """Download an object from MinIO to a temporary file, return the path."""
    from apps.ingestion.storage import get_minio_client
    client = get_minio_client()
    _, ext = os.path.splitext(storage_key)
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.close()
    client.fget_object(settings.MINIO_BUCKET, storage_key, tmp.name)
    return tmp.name


def upsert_chunks(source: Source, chunk_data: List[Dict], dense: np.ndarray, sparse_list: list) -> None:
    """
    Bulk create Chunk rows in PostgreSQL and upsert points to Qdrant.

    chunk_data: list of {chunk_index, text, page_number, ...}
    dense: ndarray (N, 768)
    sparse_list: list of N sparse embedding objects
    """
    from qdrant_client.models import PointStruct, SparseVector

    qdrant = get_qdrant_client()
    collection = settings.QDRANT_COLLECTION
    kb_id = str(source.kb_id)

    # Bulk create PG records
    chunks = Chunk.objects.bulk_create([
        Chunk(
            kb=source.kb,
            source=source,
            text=cd["text"],
            chunk_index=cd["chunk_index"],
            metadata={k: v for k, v in cd.items() if k not in ("text", "chunk_index")},
        )
        for cd in chunk_data
    ])

    # Upsert to Qdrant in batches
    points = []
    for i, (chunk, sv) in enumerate(zip(chunks, sparse_list)):
        points.append(PointStruct(
            id=str(chunk.pk),
            vector={
                "dense": dense[i].tolist(),
                "sparse": SparseVector(
                    indices=sv.indices.tolist(),
                    values=sv.values.tolist(),
                ),
            },
            payload={
                "kb_id": kb_id,
                "source_id": str(source.pk),
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            },
        ))

    for batch_start in range(0, len(points), BATCH_SIZE):
        batch = points[batch_start:batch_start + BATCH_SIZE]
        qdrant.upsert(collection_name=collection, points=batch)
