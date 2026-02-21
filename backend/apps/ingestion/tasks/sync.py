import logging

from celery import shared_task

from apps.knowledge.models import Source
from apps.ingestion.tasks.git import ingest_git

logger = logging.getLogger(__name__)


@shared_task
def sync_all_git_sources() -> None:
    """Dispatch ingest_git for all Git sources that are in READY status."""
    sources = Source.objects.filter(
        source_type=Source.SourceType.GIT,
        status=Source.Status.READY,
    )
    count = 0
    for source in sources:
        ingest_git.delay(str(source.pk))
        count += 1
    logger.info("Dispatched sync for %d Git sources", count)
