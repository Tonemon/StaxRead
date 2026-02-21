FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    git \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MODEL_CACHE_DIR=/app/model_cache
ENV GIT_REPOS_DIR=/app/git_repos
