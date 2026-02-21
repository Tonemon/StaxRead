import pytest
from unittest.mock import MagicMock, patch, call


def test_get_qdrant_client_returns_client(settings):
    settings.QDRANT_URL = "http://localhost:6333"
    with patch("apps.ingestion.qdrant_client.QdrantClient") as MockClient:
        from apps.ingestion import qdrant_client as qc
        import importlib
        importlib.reload(qc)
        client = qc.get_qdrant_client()
        assert client is not None


def test_ensure_collection_creates_if_not_exists(settings):
    settings.QDRANT_URL = "http://localhost:6333"
    settings.QDRANT_COLLECTION = "chunks"

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False

    with patch("apps.ingestion.qdrant_client.get_qdrant_client", return_value=mock_client):
        from apps.ingestion.qdrant_client import ensure_collection_exists
        ensure_collection_exists()

    mock_client.create_collection.assert_called_once()
    call_kwargs = mock_client.create_collection.call_args
    assert call_kwargs.kwargs["collection_name"] == "chunks" or call_kwargs.args[0] == "chunks"


def test_ensure_collection_skips_if_exists(settings):
    settings.QDRANT_URL = "http://localhost:6333"
    settings.QDRANT_COLLECTION = "chunks"

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True

    with patch("apps.ingestion.qdrant_client.get_qdrant_client", return_value=mock_client):
        from apps.ingestion.qdrant_client import ensure_collection_exists
        ensure_collection_exists()

    mock_client.create_collection.assert_not_called()


def test_ensure_collection_creates_payload_index(settings):
    settings.QDRANT_URL = "http://localhost:6333"
    settings.QDRANT_COLLECTION = "chunks"

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False

    with patch("apps.ingestion.qdrant_client.get_qdrant_client", return_value=mock_client):
        from apps.ingestion.qdrant_client import ensure_collection_exists
        ensure_collection_exists()

    mock_client.create_payload_index.assert_called_once()
