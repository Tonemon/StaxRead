import logging
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)

_SKIP_COMMANDS = {
    "migrate", "makemigrations", "squashmigrations",
    "showmigrations", "sqlmigrate", "collectstatic",
    "shell", "dbshell", "test", "createsuperuser",
}


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ingestion"

    def ready(self):
        if sys.argv[1:2] and sys.argv[1] in _SKIP_COMMANDS:
            return
        # celery beat only schedules tasks — it never embeds anything
        if "beat" in sys.argv:
            return
        try:
            from apps.ingestion.embeddings import warmup
            logger.info("Pre-loading embedding models...")
            warmup()
            logger.info("Embedding models loaded and ready.")
        except Exception:
            logger.exception("Failed to pre-load embedding models")
