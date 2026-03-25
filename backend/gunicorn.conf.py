import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
# Allow up to 120 s for model loading before the arbiter kills a worker.
timeout = 120
