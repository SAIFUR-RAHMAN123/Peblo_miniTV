# Peblo TV Mini

CMS upload → published catalogue → Netflix-style browse. Built for the Peblo
"Peblo TV Mini" take-home challenge.

## Stack

- **Backend:** FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **CMS:** React + TypeScript + Vite + TanStack Query
- **Viewer:** React + TypeScript + Vite + TanStack Query
- **Storage:** local disk behind an abstraction (swap-in ready for Cloudflare R2)

## How to run

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
docker-compose up --build
```

- API: http://localhost:8000 (docs at `/docs`)
- CMS: http://localhost:5173
- Viewer: http://localhost:5174
- Postgres: localhost:5432

The backend container runs migrations and seeds the database automatically
on first boot (`docker-entrypoint.sh`). Log into the CMS with `admin-dev-key`
or `editor-dev-key` (see `.env.example`).

The seed data ships with known validation issues by design (see "What's
imperfect" below) — the raw seed alone won't produce a populated Viewer
until those are resolved and something is published. Either fix them by
hand through the CMS's Publish page (it tells you exactly what's wrong), or
run the same resolution the CI pipeline uses:
```bash
docker-compose exec backend python -m scripts.ci_resolve_seed_issues
curl -X POST -H "Authorization: Bearer admin-dev-key" http://localhost:8000/admin/catalog/publish
```

### Option B — Manual (local Postgres + venv/npm)

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL to match your local Postgres
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# CMS (new terminal)
cd cms
npm install
npm run dev   # http://localhost:5173

# Viewer (new terminal)
cd viewer
npm install
npm run dev   # http://localhost:5174
```

Run backend tests: `cd backend && pytest -v` (needs a `peblo_tv_test`
database — see `backend/tests/conftest.py`). Run frontend tests:
`npm test` in `cms/` or `viewer/` (needs the backend running, since these
are integration tests against the real API).

## What's imperfect in the seed data (found, not told)

The validation report surfaces these automatically, but for reference:

| Issue | Episodes |
|---|---|
| Two published episodes share `(content_group, language)` | `ep_0004` / `ep_9001` |
| Published episode with zero artwork | `ep_0036` |
| Published Season-0 trailers missing poster+banner | `ep_0093`, `ep_0094` |
| Show with no `section` set | `Rhyme Rangers` (all-draft, so not yet blocking) |

## Roles

Two static bearer tokens map to roles server-side (see
`backend/app/core/security.py`) — not client-asserted, so this is real
enforcement, not a UI toggle:
- `editor-dev-key` → CRUD on shows/episodes/artwork
- `admin-dev-key` → everything editor can do, plus publish

## Decisions & trade-offs

- **Artwork lives on episodes, not shows.** The schema has no show-level
  artwork. A show's poster/banner in the catalogue is its first published
  episode's artwork (documented in `catalog_builder.py`). Real Peblo likely
  wants show-level key art too; out of scope here.
- **No hard DB uniqueness on `(content_group, language)` or on episode
  position `(show, season, episode, language)`.** The seed data ships with
  a genuine violation of both. A hard constraint would make that state
  un-seedable, hiding the exact problem the exercise wants surfaced.
  Instead: new writes are checked at the API layer (409 with a readable
  reason), and existing violations are caught by the validation report
  and block publish. See the comment in
  `backend/alembic/versions/0001_initial_schema.py`.
- **Language variant collapsing** picks `en` as the representative variant
  when both exist (arbitrary but deterministic — documented in
  `catalog_builder.py`).
- **Trailers (season 0)** are separated into their own `trailers` list at
  build time, never mixed into `seasons`.

---

## Part E — Written

### 1. Atomicity, and what happens if the process dies mid-publish

`storage/local.py`'s `write_atomic` writes the new catalogue to a temp file
in the *same* directory, then calls `os.replace()` to swap it over
`catalog.json`. `os.replace` is an atomic rename on POSIX — a concurrent
reader either sees the fully-old file or the fully-new file, never a
partial write. `GET /catalog` always serves the current file's actual
bytes, so this is enough on its own.

The publish *run* is recorded separately: a `PublishRun` row is created
with `outcome='running'` before any file I/O happens, and updated to
`success`/`failed` after. If the process dies between those two states,
the row is stuck at `running` with no `finished_at` — that's the signal an
operator should alert on (see Part D). The catalogue file itself is
never touched until the run has already passed validation, so a mid-publish
crash never corrupts or partially-writes it; worst case, the *next* publish
attempt just tries again.

Publish is also **idempotent**: rerunning it with unchanged data produces
byte-identical `sections`/`entries` (deterministic ordering, see
`catalog_builder.py`) and simply creates a new `PublishRun` row — safe to
retry or schedule repeatedly.

### 2. Storage abstraction: local → R2

`storage/base.py` defines four methods (`write`, `write_atomic`, `read`,
`exists`, `public_url`); everything else in the app calls only these.
`storage/local.py` implements them with plain file I/O.
`storage/r2.py` sketches the R2/S3-compatible implementation (not wired up
— no bucket to test against) using `boto3` pointed at R2's S3-compatible
endpoint. The swap is the one line in `storage/__init__.py`'s
`get_storage()` that picks the backend by `STORAGE_BACKEND` env var — no
caller changes. One asymmetry: R2/S3's `PutObject` is atomic by nature (an
object either fully exists with new bytes or is untouched), so
`write_atomic` on `R2Storage` is just a plain `write` — the temp-file/rename
dance in `LocalStorage` only exists because local disk needs it.

### 3. Search: implementation, scale limit, next step

`GET /catalog/search` linear-scans the flat `entries` array already
embedded in the published catalogue JSON (built once at publish time,
alongside the hierarchical `sections` tree) and filters in Python:
substring match on `q` against show title / episode title / categories,
exact match on `category`/`language`/`section`, all ANDed together. This
is O(n) per request with a tiny constant factor — fine for anything up to
a few thousand entries.

It stops working well somewhere in the low tens-of-thousands of entries,
where per-request linear scan and cold JSON parsing start showing up in
p99 latency, and gets worse if catalogue size grows faster than request
volume can amortize a re-parse. The next step wouldn't be "add a search
service" immediately — it'd be an in-memory inverted index built once per
publish (title/category tokens → entry indices) held in the API process,
which turns most queries into O(1) set lookups and defers a real search
engine (Postgres full-text search, then Elasticsearch/Meilisearch) until
data volume or query complexity (typo tolerance, ranking) actually
justifies the operational cost.

### 4. Why serve a pre-published file instead of querying the DB per request

Three reasons: (a) the viewer is read-heavy and public-facing — every
request hitting Postgres directly couples viewer availability to database
health and CRUD write load; (b) the catalogue's shape (collapsed language
variants, section grouping, trailers separated) is a nontrivial
transform we don't want to redo per request; (c) it makes "what was live at
time T" trivially reconstructable from a `PublishRun` row and a storage
key, which a live query can't give you for free.

Where it bites: staleness (an edit isn't visible until the next publish —
acceptable here since publish is an explicit editorial action, not
inherent latency), and the search endpoint inherits catalogue-file
recency, so search results can momentarily lag CRUD changes by design.

### 5. What was left out, and AI tool usage

**Left out** (explicitly, given the 6–8 hour target): per-episode video
playback (no video URLs in the domain — the viewer treats language pills
as decorative selectors); show-level key art as a distinct concept from
episode art; audit log of who-changed-what; versioned catalogue
rollback; publish dry-run diff. All three are called out as optional
stretch goals in the brief and skipped in favor of getting Parts A–D solid.
Auth is static bearer tokens rather than real JWT/OAuth — sufficient to
demonstrate genuine server-side role enforcement without adding an
identity-provider dependency to a take-home.

**AI tool usage:** built end-to-end with Claude (Anthropic), used as a
pair-programmer with a tight verification loop rather than a black box —
every schema decision, migration, and service was tested against the real
challenge files (seed data, reference.json, sample images) in a scratch
environment (a live Postgres instance, real `pytest`/`vitest` runs, an
actual running FastAPI + React stack) before being handed over, and several
real bugs were caught and fixed this way before they ever reached this
repo: a route-ordering bug that broke the CMS's "New Show" flow, a
migration that accidentally made the seed data's known duplicate
un-seedable, and a CI sequencing gap where publishing raw seed data would
silently leave the catalogue empty. Judgment calls (which representative
language wins on collapse, how to structure the validation report, the
no-hard-constraint decision above) were made deliberately and are
documented inline at the point of decision rather than left implicit.

---

## Part D — Operability notes

**Health:** `GET /health` checks the DB connection (`SELECT 1`) and
reports `degraded` if unreachable, `ok` otherwise.

**What to alert on:** a `PublishRun` row stuck at `outcome='running'` for
longer than a publish should ever take (a few seconds at this catalogue
size). That state means the process died mid-publish — because the
catalogue write is atomic, viewers are never seeing broken data, but an
editor has no idea their publish silently didn't happen, and it needs a
human to re-trigger it. This is preferable to alerting on `failed`
outcomes, since a `failed` publish (blocked by validation) is often normal
and self-correcting once someone reads the report.

**Secrets in production:** the two static API keys and the DB URL would
move to a cloud secret manager (AWS Secrets Manager / GCP Secret Manager)
injected as environment variables at deploy time, never committed —
`.env.example` documents every variable needed but ships no real secret.

**Time spent (approximate):**
- Part A (Backend): ~3.5h
- Part B (CMS): ~1.5h
- Part C (Viewer): ~1h
- Part D (Pipeline): ~1h
- Part E (Written) + README: ~0.5h