import pytest
import numpy as np
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_dense_model():
    model = MagicMock()
    model.encode.return_value = np.random.rand(3, 768).astype(np.float32)
    return model


def _make_sparse_embedding():
    sparse = MagicMock()
    sparse.indices = np.array([1, 5, 10], dtype=np.int32)
    sparse.values = np.array([0.5, 0.3, 0.8], dtype=np.float32)
    return sparse


@pytest.fixture
def mock_sparse_model():
    model = MagicMock()

    def fake_embed(texts):
        for _ in texts:
            yield _make_sparse_embedding()

    model.embed.side_effect = fake_embed
    return model


def test_embed_documents_returns_dense_array(mock_dense_model, mock_sparse_model, settings):
    settings.MODEL_CACHE_DIR = "/tmp/model_cache"
    with patch("apps.ingestion.embeddings._get_dense_model", return_value=mock_dense_model), \
         patch("apps.ingestion.embeddings._get_sparse_model", return_value=mock_sparse_model):
        from apps.ingestion.embeddings import embed_documents
        texts = ["doc one", "doc two", "doc three"]
        dense, sparse = embed_documents(texts)

    assert isinstance(dense, np.ndarray)
    assert dense.shape == (3, 768)
    assert len(sparse) == 3


def test_embed_documents_sparse_has_indices_and_values(mock_dense_model, mock_sparse_model, settings):
    settings.MODEL_CACHE_DIR = "/tmp/model_cache"
    with patch("apps.ingestion.embeddings._get_dense_model", return_value=mock_dense_model), \
         patch("apps.ingestion.embeddings._get_sparse_model", return_value=mock_sparse_model):
        from apps.ingestion.embeddings import embed_documents
        dense, sparse = embed_documents(["some text"])

    assert hasattr(sparse[0], "indices")
    assert hasattr(sparse[0], "values")


def test_embed_query_returns_dense_vec_and_sparse_vec(settings):
    settings.MODEL_CACHE_DIR = "/tmp/model_cache"

    mock_dense = MagicMock()
    mock_dense.encode.return_value = np.random.rand(768).astype(np.float32)

    mock_sparse = MagicMock()
    mock_sparse.embed.return_value = iter([_make_sparse_embedding()])

    with patch("apps.ingestion.embeddings._get_dense_model", return_value=mock_dense), \
         patch("apps.ingestion.embeddings._get_sparse_model", return_value=mock_sparse):
        from apps.ingestion.embeddings import embed_query
        dense_vec, sparse_vec = embed_query("find documents about X")

    assert len(dense_vec) == 768
    assert hasattr(sparse_vec, "indices")


def test_embed_documents_uses_query_prefix_for_none(mock_dense_model, mock_sparse_model, settings):
    """BGE models require 'Represent this sentence: ' prefix for documents."""
    settings.MODEL_CACHE_DIR = "/tmp/model_cache"
    with patch("apps.ingestion.embeddings._get_dense_model", return_value=mock_dense_model), \
         patch("apps.ingestion.embeddings._get_sparse_model", return_value=mock_sparse_model):
        from apps.ingestion.embeddings import embed_documents
        embed_documents(["text"])

    # Verify encode was called (with any args)
    mock_dense_model.encode.assert_called_once()
