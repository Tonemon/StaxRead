# StaxRead

Self-hosted semantic search over your own documents. Ingest PDFs, EPUBs, and Git repositories into shareable Knowledge Bases, then retrieve exact passages via hybrid dense+sparse vector search — no hallucination, no generation.

## Features

- **Hybrid search** — dense (BAAI/bge-base-en-v1.5) + sparse (BM25 via FastEmbed) with Reciprocal Rank Fusion
- **Multiple source types** — PDF, EPUB, Git repositories (Markdown + PDFs)
- **Shareable Knowledge Bases** — invite other users; revoke access at any time
- **API tokens** — generate scoped Bearer tokens to query Knowledge Bases from external applications
- **Bookmarks** — save and organise search result passages
- **Git sync** — Celery Beat job periodically re-ingests Git sources
- **CPU-only** — no GPU required
- **Self-hosted** — all data stays on your infrastructure

## Prerequisites

- Docker and Docker Compose

## Quick start

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, STAXREAD_FERNET_KEY, and STAXREAD_DOMAIN (see below)
docker compose up --build
```

The application will be available at **https://localhost** (or whichever domain/IP you configured).

On first start, Django automatically runs migrations and initialises the Qdrant collection.

If no certificate files are found in `certs/` at startup, a self-signed certificate is generated automatically for the domain set in `STAXREAD_DOMAIN`. To use a real certificate, place `cert.pem` and `key.pem` in the `certs/` directory before starting the stack.

### Network access (LAN / home network)

To make StaxRead accessible from other devices on your network, set these three variables in `.env` to match the IP address or hostname of the machine running the stack:

```
STAXREAD_DOMAIN=192.168.1.50
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50
CSRF_TRUSTED_ORIGINS=https://192.168.1.50
```

Then open `https://192.168.1.50` from any device on the network. Your browser will warn about the self-signed certificate — this is expected. For a named internal domain (e.g. `staxread.acme.org`) the same pattern applies: replace the IP with the hostname.

### Generate required secrets

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

### Create the first superuser

```bash
docker compose exec django python manage.py createsuperuser
```

Log in at `https://<your-domain>` with these credentials. The **Admin** section (visible only to superusers) lets you manage users. The **Settings** section (all users) manages Knowledge Bases, Git credentials, sharing, and account preferences.

## Architecture

| Service | Role |
|---|---|
| nginx | Reverse proxy — routes `/api/*` and `/django-admin/*` to Django, everything else to Nuxt |
| django | Django 5 + DRF REST API, Gunicorn |
| celery | Ingestion workers (extract → chunk → embed → upsert) |
| celery-beat | Scheduled Git repo sync |
| redis | Celery broker and result backend |
| postgres | Primary database (users, KBs, sources, chunks, bookmarks) |
| qdrant | Vector database — single collection with dense+sparse vectors |
| minio | Object storage for PDF/EPUB files |
| nuxt | Nuxt 3 SSR frontend |


## Development

### API docs

When `DEBUG=True`, the REST API schema is available at:

- Swagger UI: https://localhost/api/schema/swagger-ui/
- ReDoc: https://localhost/api/schema/redoc/

### Running backend tests

```bash
docker compose exec django python -m pytest tests/
```

Or locally (SQLite in-memory, no services needed):
```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/
```

### Environment variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `STAXREAD_FERNET_KEY` | Fernet key for encrypting Git PATs |
| `STAXREAD_DOMAIN` | Hostname or IP used to access the stack — sets the SSL certificate SAN |
| `ALLOWED_HOSTS` | Django allowed hosts — must include `STAXREAD_DOMAIN` |
| `CSRF_TRUSTED_ORIGINS` | Django CSRF origins — must include `https://<STAXREAD_DOMAIN>` |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_URL` | Qdrant HTTP endpoint |
| `MINIO_ENDPOINT` | MinIO host:port |
| `MINIO_ACCESS_KEY` | MinIO access key |
| `MINIO_SECRET_KEY` | MinIO secret key |
