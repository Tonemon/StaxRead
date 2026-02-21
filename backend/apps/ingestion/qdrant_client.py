from django.conf import settings
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PayloadSchemaType,
    SparseVectorParams,
    VectorParams,
    VectorsConfig,
)


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def ensure_collection_exists() -> None:
    """Create the 'chunks' collection if it doesn't already exist."""
    client = get_qdrant_client()
    collection_name = settings.QDRANT_COLLECTION

    if client.collection_exists(collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(size=768, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(),
        },
    )

    client.create_payload_index(
        collection_name=collection_name,
        field_name="kb_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
