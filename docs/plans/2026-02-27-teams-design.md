# Teams — Design Document

**Date:** 2026-02-27
**Status:** Approved

## Goal

Add a `Team` model so users can collaborate around shared Knowledge Bases, Git credentials, and API tokens. Personal KBs continue to exist unchanged alongside team KBs. Access is role-based with six roles per team.

## Approach

Option A — minimal extension: add `Team` and `TeamMembership` tables, add nullable `team_id` FK to `KnowledgeBase`, `GitCredential`, and `APIToken`. Reuse the existing `KBAccess` table for explicit per-KB assignments to Guest/Member/External users. No schema change to `KBAccess`.

---

## Roles

From least to most privileged:

| Role | Description |
|---|---|
| **Guest** | Read-only. Accesses only KBs explicitly assigned by Admin/Owner. Must be a team member. |
| **External** | Same as Guest but the user has no team membership — access via `KBAccess` only, no `TeamMembership` row. |
| **Member** | Guest + can edit sources and KB properties on explicitly assigned KBs. |
| **Manager** | Member + implicit access to all team KBs + create/delete team KBs + manage team API tokens and git credentials. |
| **Admin** | Manager + manage team members and roles (up to `admin`) + change team name/description/icon. |
| **Owner** | Admin + transfer ownership + delete team. Exactly one per team. Cannot be removed; must transfer ownership first (becomes `admin` after transfer). |

`External` is not stored as a membership role — it is a UI label for users who have a `KBAccess` row on a team KB but no `TeamMembership` row.

---

## Data Model

### New tables

```sql
teams
    id              UUID PRIMARY KEY
    name            TEXT NOT NULL
    description     TEXT
    icon_url        TEXT              -- optional uploaded avatar
    created_at      TIMESTAMPTZ
    updated_at      TIMESTAMPTZ

team_memberships
    id              UUID PRIMARY KEY
    team_id         → teams           ON DELETE CASCADE
    user_id         → users           ON DELETE CASCADE
    role            TEXT  ('guest' | 'member' | 'manager' | 'admin' | 'owner')
    invited_by      → users (nullable)
    joined_at       TIMESTAMPTZ
    UNIQUE (team_id, user_id)
```

### Changes to existing tables

```sql
knowledge_bases
    + team_id       → teams (nullable)   -- NULL = personal KB
    owner_id stays  → users              -- creator, for audit/display

git_credentials
    + team_id       → teams (nullable)   -- NULL = personal credential
    owner_id stays  → users              -- the Manager+ who created it

api_tokens
    + team_id       → teams (nullable)   -- NULL = personal token
    user_id stays   → users              -- the Manager+ who created it
```

### KBAccess (schema unchanged)

Continues to handle:
- Personal KB sharing (existing behaviour, unchanged)
- Explicit KB assignment to Guest/Member within a team
- External user access to specific team KBs (no `TeamMembership` row required)

---

## Access Control Logic

A single `get_accessible_kbs(user)` helper used by all search and KB list views, implemented as a single ORM query with `Q()` objects:

```
1. Personal ownership:
   kb.team_id IS NULL AND kb.owner_id = user

2. Team implicit (Manager / Admin / Owner):
   kb.team_id IN teams where user has role IN ('manager', 'admin', 'owner')

3. Team explicit (Guest / Member):
   kb.team_id IN teams where user has role IN ('guest', 'member')
   AND KBAccess(kb=kb, user=user, status='accepted') exists

4. External / personal sharing:
   KBAccess(kb=kb, user=user, status='accepted') exists
   (covers both personal KB sharing and external access to team KBs)
```

Qdrant always receives the resolved flat list of `kb_ids` — the vector DB never sees roles or teams.

### Permission matrix

| Action | Guest | Member | Manager | Admin | Owner |
|---|:-:|:-:|:-:|:-:|:-:|
| Search assigned KBs | ✓ | ✓ | ✓ | ✓ | ✓ |
| Edit sources / KB properties (assigned) | — | ✓ | ✓ | ✓ | ✓ |
| Create / delete team KBs | — | — | ✓ | ✓ | ✓ |
| Manage team API tokens & git credentials | — | — | ✓ | ✓ | ✓ |
| Manage members & roles (ceiling: admin) | — | — | — | ✓ | ✓ |
| Change team name / description / icon | — | — | — | ✓ | ✓ |
| Transfer ownership / delete team | — | — | — | — | ✓ |

---

## API Surface

New app: `apps/teams/`

```
# Teams
GET    /api/teams/
POST   /api/teams/                              ← creator becomes Owner
GET    /api/teams/{id}/
PATCH  /api/teams/{id}/                         ← Admin/Owner only
DELETE /api/teams/{id}/                         ← Owner only

# Members
GET    /api/teams/{id}/members/
POST   /api/teams/{id}/members/                 ← Admin/Owner; default role: member
PATCH  /api/teams/{id}/members/{user_id}/       ← Admin/Owner; role ceiling enforced
DELETE /api/teams/{id}/members/{user_id}/       ← Admin/Owner, or self-leave

# Ownership transfer
POST   /api/teams/{id}/transfer-ownership/      ← Owner only; body: { user_id }

# Team git credentials
GET    /api/teams/{id}/git-credentials/
POST   /api/teams/{id}/git-credentials/         ← Manager+
PATCH  /api/teams/{id}/git-credentials/{cred_id}/
DELETE /api/teams/{id}/git-credentials/{cred_id}/

# Team API tokens
GET    /api/teams/{id}/api-tokens/
POST   /api/teams/{id}/api-tokens/              ← Manager+
PATCH  /api/teams/{id}/api-tokens/{token_id}/
DELETE /api/teams/{id}/api-tokens/{token_id}/
```

### Changes to existing endpoints

- `POST /api/knowledge-bases/` — accepts optional `team_id`; user must be Manager+ in that team
- `GET /api/knowledge-bases/` — returns personal + all accessible team KBs
- `POST/GET /api/sources/` — permission check uses team role (Member+ for assigned, Manager+ for all team KBs)
- Personal `/api/git-credentials/` and `/api/api-tokens/` — unchanged, personal only

---

## Frontend Structure

### Sidebar (default layout)

KB list replaced with collapsible grouped sections:

```
── Personal ─────────────────────── (no settings icon)
   ○ KB Toggle: My Research

── Team Alpha ───────────────────── ⚙  (Manager+ only; → /settings/teams/{id}/general)
   ○ KB Toggle: Engineering Docs
   ○ KB Toggle: API References

── Team Beta ────────────────────── ⚙  (Manager+ only)
   ○ KB Toggle: Design System
```

- "All KBs" master toggle applies per section
- ⚙ icon only visible to Manager+ in that team

### Settings navigation

New `Teams` entry in the Settings sidebar between Sharing and Account:

```
/settings/teams/                          ← list + "New Team" button
/settings/teams/[id]/general              ← General tab (default)
/settings/teams/[id]/members              ← Members tab
/settings/teams/[id]/git-credentials      ← Team Git Credentials (Manager+)
/settings/teams/[id]/api-tokens           ← Team API Tokens (Manager+)
```

### `/settings/teams/[id]/general`

- Editable fields (Admin/Owner): name, description, icon upload
- Read-only display for lower roles
- Owner-only danger zone: Transfer Ownership, Delete Team

### `/settings/teams/[id]/members`

**Top — Invite** (Admin/Owner): username input + Invite button; new members default to `member` role.

**Middle — Members table**: username, role dropdown, joined date, Remove button.
- Dropdown visible to all, editable by Admin/Owner only
- After changing a role, a blue Save button appears inline on that row
- Admin dropdown omits `owner`; Owner dropdown includes all roles
- Owner row has no Remove button; cannot be targeted for removal

**Bottom — Role reference**: collapsible legend explaining each role.

### `/settings/teams/[id]/api-tokens`

Same layout as `/settings/sharing`. Banner at top:

> **Service Accounts** — Team API tokens are not tied to any individual user. Use them for integrations, CI pipelines, and automated services so access persists regardless of team membership changes.

Token scope limited to KBs belonging to this team.

### KB creation modal

`Location` dropdown added to the New KB modal:
- `Personal` — always available, default
- Team options — enabled only if user is Manager+ in that team; greyed out otherwise

---

## New Django App

`apps/teams/` containing:
- `models.py` — `Team`, `TeamMembership`
- `serializers.py` — team, membership, nested token/credential serializers
- `views.py` — `TeamViewSet`, `TeamMemberViewSet`, team-scoped credential and token viewsets
- `permissions.py` — `IsTeamManager`, `IsTeamAdmin`, `IsTeamOwner` permission classes
- `urls.py` — router registration
- `migrations/`
