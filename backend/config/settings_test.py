"""Test settings — overrides database to SQLite in-memory."""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("STAXREAD_FERNET_KEY", "lGOZ0YVpK6Q4TqrPFZQgI_XOGB85bZ9RxP0TLrH_RiA=")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ALLOWED_HOSTS", "localhost")
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "staxread")
os.environ.setdefault("MINIO_SECRET_KEY", "staxread-secret")
os.environ.setdefault("MINIO_BUCKET", "staxread-documents")
os.environ.setdefault("MINIO_USE_SSL", "false")

from config.settings import *  # noqa: F401, F403, E402

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
