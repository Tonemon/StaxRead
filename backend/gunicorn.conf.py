import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
# Allow up to 120 s for model loading in workers before the arbiter kills them.
timeout = 120

# Signal to AppConfig.ready() that Gunicorn is running, so it skips warmup
# there. post_fork() below handles loading in each worker after the fork,
# ensuring every worker gets its own clean C-extension state.
os.environ["DJANGO_RUNNING_UNDER_GUNICORN"] = "1"


def post_fork(server, worker):
    """
    Called in each worker process after forking from the master.

    The master may have a populated @lru_cache for the embedding models, but
    ONNX runtime InferenceSession objects and PyTorch thread pools do not
    survive os.fork() safely. Clear the inherited cache entries and reload
    fresh model instances in this worker.
    """
    try:
        from apps.ingestion.embeddings import _get_dense_model, _get_sparse_model, warmup
        _get_dense_model.cache_clear()
        _get_sparse_model.cache_clear()
        server.log.info("Worker %s: pre-loading embedding models...", worker.pid)
        warmup()
        server.log.info("Worker %s: embedding models ready.", worker.pid)
    except Exception:
        server.log.exception("Worker %s: failed to pre-load embedding models", worker.pid)
