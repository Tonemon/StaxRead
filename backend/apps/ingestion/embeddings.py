from functools import lru_cache
from typing import List, Tuple

import numpy as np
from django.conf import settings


DENSE_MODEL_NAME = "BAAI/bge-base-en-v1.5"
SPARSE_MODEL_NAME = "prithivida/Splade_PP_en_v1"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _get_dense_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(
        DENSE_MODEL_NAME,
        cache_folder=settings.MODEL_CACHE_DIR,
    )


@lru_cache(maxsize=1)
def _get_sparse_model():
    from fastembed import SparseTextEmbedding
    return SparseTextEmbedding(
        model_name=SPARSE_MODEL_NAME,
        cache_dir=settings.MODEL_CACHE_DIR,
    )


def warmup() -> None:
    """Pre-load both embedding models into memory."""
    _get_dense_model()
    _get_sparse_model()


def embed_documents(texts: List[str]) -> Tuple[np.ndarray, list]:
    """
    Embed a batch of document texts.

    Returns:
        dense: ndarray of shape (N, 768)
        sparse: list of sparse embedding objects with .indices and .values
    """
    dense_model = _get_dense_model()
    sparse_model = _get_sparse_model()

    dense = dense_model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    sparse = list(sparse_model.embed(texts))

    return dense, sparse


def embed_query(query: str) -> Tuple[np.ndarray, object]:
    """
    Embed a single query string.

    Returns:
        dense_vec: 1D ndarray of shape (768,)
        sparse_vec: sparse embedding object with .indices and .values
    """
    dense_model = _get_dense_model()
    sparse_model = _get_sparse_model()

    prefixed = BGE_QUERY_PREFIX + query
    dense_vec = dense_model.encode(prefixed, normalize_embeddings=True, convert_to_numpy=True)
    sparse_vec = next(iter(sparse_model.embed([query])))

    return dense_vec, sparse_vec
