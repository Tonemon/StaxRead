import uuid
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_minio(settings):
    settings.MINIO_ENDPOINT = "localhost:9000"
    settings.MINIO_ACCESS_KEY = "staxread"
    settings.MINIO_SECRET_KEY = "staxread-secret"
    settings.MINIO_BUCKET = "staxread-documents"
    settings.MINIO_USE_SSL = False

    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    return mock_client


def test_upload_file_calls_put_object(mock_minio, tmp_path, settings):
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"%PDF-1.4 content")

    source_id = uuid.uuid4()
    with patch("apps.ingestion.storage.get_minio_client", return_value=mock_minio):
        from apps.ingestion.storage import upload_file
        object_name = upload_file(source_id, str(test_file), "application/pdf")

    mock_minio.put_object.assert_called_once()
    assert str(source_id) in object_name
    assert ".pdf" in object_name


def test_upload_file_returns_object_name(mock_minio, tmp_path, settings):
    test_file = tmp_path / "book.epub"
    test_file.write_bytes(b"EPUB content")
    source_id = uuid.uuid4()

    with patch("apps.ingestion.storage.get_minio_client", return_value=mock_minio):
        from apps.ingestion.storage import upload_file
        object_name = upload_file(source_id, str(test_file), "application/epub+zip")

    assert isinstance(object_name, str)
    assert len(object_name) > 0


def test_get_presigned_url_returns_string(mock_minio, settings):
    mock_minio.presigned_get_object.return_value = "http://localhost:9000/staxread-documents/object?signature=abc"
    source_id = uuid.uuid4()

    with patch("apps.ingestion.storage.get_minio_client", return_value=mock_minio):
        from apps.ingestion.storage import get_presigned_url
        url = get_presigned_url(source_id, "pdf")

    assert isinstance(url, str)
    mock_minio.presigned_get_object.assert_called_once()


def test_get_minio_client_creates_bucket_if_not_exists(settings):
    settings.MINIO_ENDPOINT = "localhost:9000"
    settings.MINIO_ACCESS_KEY = "staxread"
    settings.MINIO_SECRET_KEY = "staxread-secret"
    settings.MINIO_BUCKET = "staxread-documents"
    settings.MINIO_USE_SSL = False

    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = False

    from apps.ingestion import storage
    storage._get_minio_client.cache_clear()

    with patch("apps.ingestion.storage.Minio", return_value=mock_client):
        storage._get_minio_client()

    mock_client.make_bucket.assert_called_once_with("staxread-documents")
