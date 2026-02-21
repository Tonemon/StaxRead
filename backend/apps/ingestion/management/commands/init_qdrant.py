from django.core.management.base import BaseCommand
from apps.ingestion.qdrant_client import ensure_collection_exists


class Command(BaseCommand):
    help = "Initialize Qdrant collection for StaxRead"

    def handle(self, *args, **options):
        self.stdout.write("Initializing Qdrant collection...")
        ensure_collection_exists()
        self.stdout.write(self.style.SUCCESS("Qdrant collection ready."))
