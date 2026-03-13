import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ingestion"

    def ready(self):
        # Skip for any manage.py invocation (migrate, init_qdrant, shell, etc.)
        if sys.argv and sys.argv[0].endswith("manage.py"):
            return
        # Celery beat only schedules tasks — it never runs embeddings
        if "beat" in sys.argv:
            return
        # Under Gunicorn, post_fork() in gunicorn.conf.py handles warmup in
        # each worker after forking. Loading here (in the master) would produce
        # C-extension state (ONNX runtime, PyTorch threads) that doesn't
        # survive os.fork() cleanly.
        if os.environ.get("DJANGO_RUNNING_UNDER_GUNICORN"):
            return
        try:
            from apps.ingestion.embeddings import warmup
            logger.info("Pre-loading embedding models...")
            warmup()
            logger.info("Embedding models loaded and ready.")
        except Exception:
            logger.exception("Failed to pre-load embedding models")
