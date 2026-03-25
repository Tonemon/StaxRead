import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
# Allow up to 120 s for model loading before the arbiter kills a worker.
timeout = 120
# Load the WSGI app (Django setup + AppConfig.ready() + model warmup) in the
# master process before forking workers. Workers inherit the loaded lru_cache
# via copy-on-write — no per-worker model loading needed. This is the same
# pattern Celery uses (models loaded in main process, prefork workers inherit).
preload_app = True
