import os
import sys
import traceback
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

# Pre-load embedding models here — wsgi.py is only ever executed by Gunicorn
# (never by manage.py or Celery), so no guards are needed.  With preload_app=True
# in gunicorn.conf.py this runs once in the master process; workers inherit the
# loaded lru_cache objects via copy-on-write, so no per-worker loading occurs.
try:
    from apps.ingestion.embeddings import warmup
    sys.stderr.write("[wsgi] Pre-loading embedding models...\n")
    sys.stderr.flush()
    warmup()
    sys.stderr.write("[wsgi] Embedding models loaded and ready.\n")
    sys.stderr.flush()
except Exception:
    sys.stderr.write("[wsgi] ERROR: Failed to pre-load embedding models:\n")
    sys.stderr.flush()
    traceback.print_exc(file=sys.stderr)
