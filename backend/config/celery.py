import logging
import os

from celery import Celery
from celery.signals import worker_ready

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("staxread")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    try:
        from apps.ingestion.embeddings import warmup
        logger.info("Pre-loading embedding models in Celery worker...")
        warmup()
        logger.info("Embedding models loaded and ready.")
    except Exception:
        logger.exception("Failed to pre-load embedding models in Celery worker")
