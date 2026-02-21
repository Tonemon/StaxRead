# StaxRead

Self-hosted semantic search over your own documents. Ingest PDFs, EPUBs, and Git repositories into shareable Knowledge Bases, then retrieve exact passages via hybrid dense+sparse vector search — no hallucination, no generation.

## Features

- **Hybrid search** — dense (BAAI/bge-base-en-v1.5) + sparse (BM25 via FastEmbed) with Reciprocal Rank Fusion
- **Multiple source types** — PDF, EPUB, Git repositories (Markdown + PDFs)
- **Shareable Knowledge Bases** — share read access with other users
- **Bookmarks** — save and organise search result passages
- **Git sync** — Celery Beat job periodically re-ingests Git sources
- **CPU-only** — no GPU required
- **Self-hosted** — all data stays on your infrastructure

## Prerequisites

- Docker and Docker Compose

## Quick start

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and STAXREAD_FERNET_KEY (see below)
docker compose up --build
```

The application will be available at http://localhost.

On first start, Django automatically runs migrations and initialises the Qdrant collection.

## Generate required secrets

**Django secret key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Fernet encryption key** (used to encrypt Git PAT tokens at rest):
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add both values to `.env`:
```
SECRET_KEY=<output of first command>
STAXREAD_FERNET_KEY=<output of second command>
```

## Create the first superuser

```bash
docker compose exec django python manage.py createsuperuser
```

Log in at http://localhost with these credentials. The Admin section (visible only to superusers) lets you manage Knowledge Bases, add sources, and create users.

## Architecture

| Service | Role |
|---|---|
| nginx | Reverse proxy — routes `/api/*` to Django, everything else to Nuxt |
| django | Django 5 + DRF REST API, Gunicorn |
| celery | Ingestion workers (extract → chunk → embed → upsert) |
| celery-beat | Scheduled Git repo sync |
| redis | Celery broker and result backend |
| postgres | Primary database (users, KBs, sources, chunks, bookmarks) |
| qdrant | Vector database — single collection with dense+sparse vectors |
| minio | Object storage for PDF/EPUB files |
| nuxt | Nuxt 3 SSR frontend |

## Running backend tests

```bash
docker compose exec django python -m pytest tests/
```

Or locally (SQLite in-memory, no services needed):
```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/
```

## Environment variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `STAXREAD_FERNET_KEY` | Fernet key for encrypting Git PATs |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_URL` | Qdrant HTTP endpoint |
| `MINIO_ENDPOINT` | MinIO host:port |
| `MINIO_ACCESS_KEY` | MinIO access key |
| `MINIO_SECRET_KEY` | MinIO secret key |
| `NUXT_PUBLIC_API_BASE` | API base URL seen by the browser |
