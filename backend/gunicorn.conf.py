import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
# Allow up to 120 s for model loading in workers before the arbiter kills them.
timeout = 120

# Signal to AppConfig.ready() that Gunicorn is running, so it skips warmup
# there. post_worker_init() below handles loading in each worker after Django
# is fully initialized.
os.environ["DJANGO_RUNNING_UNDER_GUNICORN"] = "1"


def post_worker_init(worker):
    """
    Called in each worker after the WSGI application is fully loaded
    (Django setup is complete, all AppConfig.ready() methods have run).
    Load embedding models here so every worker is ready before serving requests.
    """
    try:
        from apps.ingestion.embeddings import warmup
        worker.log.info("Worker %s: pre-loading embedding models...", worker.pid)
        warmup()
        worker.log.info("Worker %s: embedding models ready.", worker.pid)
    except Exception:
        worker.log.exception("Worker %s: failed to pre-load embedding models", worker.pid)
