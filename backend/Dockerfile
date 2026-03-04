FROM python:3.12-slim

ARG GPU=0

RUN apt-get update && apt-get install -y \
    git \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# GPU build: reinstall torch from PyPI default index (includes CUDA) and swap
# onnxruntime for onnxruntime-gpu so fastembed can use CUDAExecutionProvider.
RUN if [ "$GPU" = "1" ]; then \
        pip install --no-cache-dir --force-reinstall "torch==2.5.*" && \
        pip uninstall -y onnxruntime && \
        pip install --no-cache-dir onnxruntime-gpu; \
    fi

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MODEL_CACHE_DIR=/app/model_cache
ENV GIT_REPOS_DIR=/app/git_repos

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
