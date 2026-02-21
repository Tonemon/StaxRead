# StaxRead — System Design

**Date:** 2026-02-21
**Status:** Approved

## Overview

StaxRead is a self-hosted, CPU-only semantic search application that ingests books (PDF, epub) and Git repositories (Markdown, PDF) into named Knowledge Bases, and lets authenticated users search across them with no hallucination or generative output. Results are exact retrieved passages ranked by relevance.

**Target scale:** 1–10 users, hundreds of documents, one or more large Git repos.

**Future consideration (not in scope now):** local LLM inference for personalised answer generation. The architecture is designed to accommodate this without structural changes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Django 5 + Django REST Framework |
| Task queue | Celery + Celery Beat |
| Message broker / cache | Redis |
| Relational DB | PostgreSQL 16 |
| Vector DB | Qdrant (dense + sparse hybrid search) |
| Object storage | MinIO |
| Frontend | Nuxt 3 + Nuxt UI Pro (open-source licence) |
| Reverse proxy | Nginx |
| Containerisation | Docker Compose |

---

## Docker Services

| Service | Image | Role |
|---|---|---|
| `nginx` | nginx:alpine | Reverse proxy — `/api/*` → Django, `/*` → Nuxt |
| `django` | custom Python 3.12 | Gunicorn, port 8000 |
| `celery` | same as django | Ingestion workers |
| `celery-beat` | same as django | Scheduled Git sync |
| `redis` | redis:alpine | Celery broker + result backend |
| `postgres` | postgres:16 | Relational data |
| `qdrant` | qdrant/qdrant | Vector DB |
| `minio` | minio/minio | File object storage |
| `nuxt` | custom Node 20 | SSR frontend server, port 3000 |

**Docker volumes:**

| Volume | Contents |
|---|---|
| `postgres_data` | PostgreSQL data files |
| `qdrant_data` | Qdrant indexes and vector data |
| `minio_data` | Uploaded PDF and epub files |
| `git_repos` | Cloned Git repositories (Celery worker only) |
| `model_cache` | BGE-base-en-v1.5 weights (~438 MB, downloaded once) |

---

## Embedding Model

**Model:** `BAAI/bge-base-en-v1.5`

- Size: ~438 MB, 768-dimensional dense vectors
- MTEB English average: 64.2 (significantly outperforms `all-MiniLM-L6-v2` at 56.3)
- CPU throughput: ~2,500–4,000 sentences/sec (batch=32, 8-core CPU)
- Query prefix: `"Represent this sentence for searching relevant passages: {query}"`
- Loaded in Celery workers on startup; weights cached in `model_cache` volume

**Sparse vectors:** FastEmbed BM25 (Qdrant's library) — no separate service required.

**Acceleration (optional):** ONNX Runtime via `optimum[onnxruntime]` for ~1.5–2.5× CPU speedup.

---

## Data Model

### PostgreSQL

```sql
-- Django auth users (built-in)
-- id, username, email, password_hash, is_staff, is_superuser, is_active

knowledge_bases
    id              UUID PRIMARY KEY
    owner_id        → users
    name            TEXT NOT NULL
    description     TEXT
    created_at      TIMESTAMPTZ
    updated_at      TIMESTAMPTZ

kb_access                          -- sharing table
    kb_id           → knowledge_bases  ON DELETE CASCADE
    user_id         → users            ON DELETE CASCADE
    granted_by      → users
    permission      TEXT  ('read' | 'manage')
    granted_at      TIMESTAMPTZ
    PRIMARY KEY (kb_id, user_id)

git_credentials                    -- encrypted PATs for private repos
    id              UUID PRIMARY KEY
    owner_id        → users
    name            TEXT             (e.g. "My GitHub Token")
    encrypted_pat   TEXT             (Fernet AES-256, key from env var)
    host_url        TEXT             (e.g. https://github.com)
    created_at      TIMESTAMPTZ

sources                            -- individual files or git repos within a KB
    id              UUID PRIMARY KEY
    kb_id           → knowledge_bases  ON DELETE CASCADE
    type            TEXT  ('pdf' | 'epub' | 'git')
    display_name    TEXT
    minio_path      TEXT             (pdf/epub: {source_id}/original.{ext})
    git_url         TEXT             (git only)
    git_branch      TEXT  DEFAULT 'main'
    git_credential  → git_credentials  (nullable, for private repos)
    file_hash       TEXT             (for deduplication on re-upload)
    status          TEXT  ('pending' | 'processing' | 'ready' | 'error')
    error_message   TEXT
    last_synced_at  TIMESTAMPTZ
    created_at      TIMESTAMPTZ

chunks                             -- text passages (point IDs match Qdrant)
    id              UUID PRIMARY KEY  (same UUID used as Qdrant point ID)
    source_id       → sources        ON DELETE CASCADE
    kb_id           → knowledge_bases (denormalised for fast KB-level deletes)
    chunk_index     INTEGER
    content         TEXT             (full chunk text, used for result display)
    page_number     INTEGER          (PDFs; null for git/epub)
    heading_path    TEXT             (markdown heading hierarchy; null for pdf)
    metadata        JSONB            (git_commit_hash, file_path, epub_chapter, etc.)

search_history
    id              UUID PRIMARY KEY
    user_id         → users
    query           TEXT
    kb_ids          JSONB            (array of KB UUIDs active at query time)
    created_at      TIMESTAMPTZ

bookmark_categories
    id              UUID PRIMARY KEY
    user_id         → users
    name            TEXT
    description     TEXT
    tags            JSONB            (array of strings)
    created_at      TIMESTAMPTZ

bookmarks
    id              UUID PRIMARY KEY
    user_id         → users
    chunk_id        → chunks         ON DELETE CASCADE
    category_id     → bookmark_categories  ON DELETE SET NULL
    search_id       → search_history (nullable)
    note            TEXT             (optional user annotation)
    created_at      TIMESTAMPTZ
```

### Qdrant

**Single collection:** `chunks`

```
Point:
├── id: UUID                    (matches chunks.id in PostgreSQL)
├── vectors:
│     ├── dense:  float[768]    (BGE-base-en-v1.5, L2-normalised)
│     └── sparse: {indices, values}  (FastEmbed BM25)
└── payload:
      ├── kb_id:       string   (indexed keyword — used for filtering)
      ├── source_id:   string
      ├── source_type: string   ('pdf' | 'epub' | 'git')
      └── chunk_index: int
```

Chunk `content` and all metadata live in PostgreSQL. Qdrant holds only what is needed for search. After Qdrant returns point IDs + scores, Django fetches full content from PostgreSQL by ID.

### MinIO

**Bucket:** `staxread-documents`

```
staxread-documents/
└── {source_id}/
      ├── original.pdf   (or original.epub)
      └── cover.jpg      (optional, for display in admin UI)
```

Git repos are cloned to the `git_repos` Docker volume, not MinIO.

---

## Ingestion Pipeline

All ingestion runs as Celery task chains. Each step is discrete so failures are retried at the exact failing step. Source `status` is updated at each transition.

### PDF / Epub

Triggered when a file is uploaded via the admin UI.

```
upload_to_minio_task
  └─ Store file at {source_id}/original.{ext} in MinIO
     source.status = "processing"

extract_text_task
  ├─ PDF:  PyMuPDF (fitz) — extract text per page, preserve page numbers
  └─ Epub: ebooklib — extract HTML chapters → strip tags → plain text

chunk_text_task
  └─ LangChain RecursiveCharacterTextSplitter
       chunk_size: 512 tokens
       chunk_overlap: 50 tokens
       sentence-aware boundaries (\n\n → \n → ". " → " ")

embed_and_upsert_task
  ├─ Dense:  BGE-base-en-v1.5 → float[768], normalised
  ├─ Sparse: FastEmbed BM25 → sparse vector
  ├─ Upsert to Qdrant in batches of 64 points
  └─ Bulk insert chunk records to PostgreSQL
     source.status = "ready"
```

### Git Repository

Triggered manually from the admin UI or on schedule (Celery Beat).

```
clone_or_sync_task
  ├─ New repo:  git clone https://{PAT}@{host}/{path} → /git_repos/{source_id}/
  └─ Existing:  git pull → detect changed/deleted files via git diff

  PAT decrypted from PostgreSQL using Fernet key (from STAXREAD_FERNET_KEY env var)

discover_files_task
  └─ Walk repo directory → collect .md and .pdf files
     Compare file hashes → skip unchanged files

For each new/changed file:
  └─ Same extract → chunk → embed → upsert chain as PDF/Epub above
     Metadata includes: file_path, git_commit_hash, heading_path

handle_deletions_task
  └─ Files removed from repo:
     delete their Qdrant points + PostgreSQL chunk records
```

### Scheduled Sync (Celery Beat)

Every 6 hours (configurable per-source in the admin UI):
- `sync_git_sources_task` → triggers `clone_or_sync_task` for all `status = "ready"` git sources

### Worker Configuration

- `--concurrency=2` (CPU-bound embedding limits parallelism)
- Model weights loaded once on worker startup from `model_cache` volume
- Celery Beat runs as a separate container to avoid duplicate task scheduling

---

## Search Pipeline

```
1. POST /api/search/
   body: { query: "...", kb_ids: ["uuid-A", "uuid-B"] }
   Authorization: Bearer {access_token}

2. Django permission check
   Intersect requested kb_ids with kb_access for current user
   → verified_kb_ids

3. Parallel encoding (in Django process)
   ├─ Dense:  BGE-base prefix + BGE-base-en-v1.5 → float[768]
   └─ Sparse: FastEmbed BM25 → sparse vector

4. Qdrant hybrid search (single API call)
   filter:   kb_id IN verified_kb_ids
   prefetch: top-40 dense + top-40 sparse
   fusion:   RRF (Reciprocal Rank Fusion)
   limit:    top-20 results (point IDs + relevance scores)

5. PostgreSQL enrichment
   SELECT chunks + sources WHERE chunk.id IN [returned IDs]
   → content, page_number, heading_path, source display_name, source type, metadata

6. Save to search_history (async Celery task, non-blocking)

7. Response
   [
     {
       chunk_id:        "uuid",
       content:         "exact matched text...",
       relevance_score: 0.87,
       source: {
         id:           "uuid",
         display_name: "Clean Code.pdf",
         type:         "pdf",
         page_number:  42,           // or file_path for git markdown
       },
       kb: { id: "uuid", name: "Programming Books" }
     },
     ...
   ]
```

**No generation, no hallucination.** The response is strictly retrieved chunk text — no LLM involved in the initial build. The future LLM path inserts between steps 6 and 7; the retrieval architecture is unchanged.

**Search history autocomplete:**
`GET /api/search/history/?limit=10` — returns last 10 unique queries for the current user, used for the dropdown when the search box is focused.

---

## Authentication

- **Mechanism:** JWT via `djangorestframework-simplejwt`
- **Token storage:** httpOnly cookies (set by Django response — not accessible to JavaScript)
- **Access token lifetime:** 15 minutes
- **Refresh token lifetime:** 7 days
- **Nuxt composable (`useAuth.ts`):**
  - Axios interceptor attaches access token to every `/api/` request
  - On 401: auto-calls `/api/auth/token/refresh/` → retries original request
  - On refresh failure: clears cookies → redirects to `/login`
- **Superuser access:** `is_superuser=True` required for `/admin/users/` — enforced by both Nuxt middleware and Django API permission class

---

## Frontend Structure

Two visual themes, one Nuxt codebase. Both layouts use Nuxt UI Pro (free tier — open-source project).

```
nuxt/
├── layouts/
│   ├── default.vue        ← Chat template style (user area)
│   └── admin.vue          ← Dashboard template style (admin panel)
├── middleware/
│   ├── auth.ts            ← Redirect to /login if no valid JWT
│   └── superuser.ts       ← Restrict /admin/users to superusers
├── composables/
│   ├── useAuth.ts         ← JWT token management
│   └── useSearch.ts       ← Search state, active KBs, history
├── stores/
│   └── search.ts          ← Pinia: active KB IDs, current results
└── pages/
    ├── login.vue                        ← Centred login card, no layout
    │
    ├── index.vue                        ← Search home (layout: default)
    │   Centred logo + search bar
    │
    ├── search.vue                       ← Results page (layout: default)
    │   Search bar moves to top on submit
    │   Results list: content, relevance score, source, bookmark button
    │
    ├── bookmarks.vue                    ← Bookmarks (layout: default)
    │   Grouped by category, with originating query shown
    │   Category management (create, rename, add tags, delete)
    │
    ├── documents/[id].vue               ← Document viewer (layout: default)
    │   PDF:      PDF.js (@tato30/vue-pdf), jumps to page from metadata
    │   Epub:     HTML fragment from Django, jumps to chapter/section
    │   Markdown: rendered with @nuxtjs/mdc, anchored to heading
    │
    └── admin/
        ├── index.vue                    ← Stats overview (layout: admin)
        ├── knowledge-bases/
        │   ├── index.vue                ← List + create KBs
        │   └── [id]/
        │       └── index.vue            ← KB detail: sources, sharing
        │           sources/index.vue    ← Add PDF, epub, Git repo
        ├── git-credentials/
        │   └── index.vue                ← Manage PATs
        └── users/
            └── index.vue               ← User management (superusers only)
```

**Active KB selection (user area):**
The left sidebar lists all KBs the user has access to, with toggles to enable/disable each for the current session. Active KB IDs are stored in Pinia and sent with every search request. Default: all permitted KBs enabled on first login.

**Source status in admin:**
Status badge per source (pending / processing / ready / error). Polled every 5 seconds while any source is in `processing` state.

**Deferred features (not in initial build):**
- Graph view of search results (force-directed, D3.js or Vis.js)

---

## Private Git Credentials

- User provides an HTTPS clone URL + a Personal Access Token (GitHub, GitLab, Gitea, etc.)
- PAT stored encrypted in PostgreSQL using **Fernet (AES-256)** symmetric encryption
- Encryption key: `STAXREAD_FERNET_KEY` environment variable (never stored in DB)
- Celery worker decrypts at clone time: `git clone https://{PAT}@{host}/{repo}.git`
- Admin UI shows PAT as masked field after saving; cannot be retrieved in plaintext

---

## Knowledge Base Sharing

```
PostgreSQL (source of truth for permissions):
  kb_access(kb_id, user_id, permission)

Sharing flow:
  Owner grants access → INSERT into kb_access
  Revoke access       → DELETE from kb_access

Search enforcement:
  Django intersects user's requested kb_ids with kb_access at query time
  Qdrant filter: kb_id IN [verified list] — server-side, never client-trusted

Session state:
  Active KB IDs stored in Pinia (client) and sent per request
  Server always re-validates against kb_access — client list is a hint, not auth
```

---

## API Surface (summary)

```
POST   /api/auth/token/              ← login
POST   /api/auth/token/refresh/      ← refresh JWT
POST   /api/auth/logout/             ← blacklist refresh token

GET    /api/search/                  ← execute search
GET    /api/search/history/          ← autocomplete history

GET    /api/knowledge-bases/         ← list accessible KBs
POST   /api/knowledge-bases/         ← create KB
GET    /api/knowledge-bases/{id}/
PATCH  /api/knowledge-bases/{id}/
DELETE /api/knowledge-bases/{id}/

POST   /api/knowledge-bases/{id}/share/    ← grant access to another user
DELETE /api/knowledge-bases/{id}/share/    ← revoke access

GET    /api/sources/
POST   /api/sources/                       ← upload PDF/epub or add git repo
DELETE /api/sources/{id}/
GET    /api/sources/{id}/status/           ← ingestion status polling

POST   /api/sources/{id}/sync/             ← manually trigger git sync

GET    /api/git-credentials/
POST   /api/git-credentials/
DELETE /api/git-credentials/{id}/

GET    /api/bookmarks/
POST   /api/bookmarks/
DELETE /api/bookmarks/{id}/

GET    /api/bookmark-categories/
POST   /api/bookmark-categories/
PATCH  /api/bookmark-categories/{id}/
DELETE /api/bookmark-categories/{id}/

GET    /api/documents/{id}/view/           ← stream file from MinIO (PDF/epub)
GET    /api/documents/{id}/content/        ← serve markdown content

GET    /api/users/                         ← superusers only
POST   /api/users/
PATCH  /api/users/{id}/
DELETE /api/users/{id}/
```

---

## Environment Variables (key ones)

```
# Django
SECRET_KEY=...
STAXREAD_FERNET_KEY=...          # Fernet key for PAT encryption
DATABASE_URL=postgres://...
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=staxread-documents
ALLOWED_HOSTS=localhost,...

# Nuxt
NUXT_PUBLIC_API_BASE=http://nginx/api
```

---

## Project Directory Structure (top-level)

```
StaxRead/
├── docker-compose.yml
├── .env.example
├── nginx/
│   └── nginx.conf
├── backend/                   ← Django project
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/                ← Django settings, URLs, Celery config
│   └── apps/
│       ├── accounts/          ← User model, JWT auth endpoints
│       ├── knowledge/         ← KnowledgeBase, Source, Chunk, kb_access models
│       ├── ingestion/         ← Celery tasks (extract, chunk, embed, upsert)
│       ├── search/            ← Search endpoint, history
│       └── bookmarks/         ← Bookmark, BookmarkCategory models + endpoints
└── frontend/                  ← Nuxt project
    ├── Dockerfile
    ├── package.json
    ├── nuxt.config.ts
    └── app/
        ├── layouts/
        ├── pages/
        ├── composables/
        ├── stores/
        └── components/
```
