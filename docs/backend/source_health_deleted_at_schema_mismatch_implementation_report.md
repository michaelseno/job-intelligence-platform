# Implementation Report

## 1. Summary of Changes
Reworked Alembic revision `20260424_0002` so PostgreSQL no longer recreates `sources`. The migration now adds `deleted_at` and swaps the legacy unconditional `dedupe_key` uniqueness for the intended active-row partial unique index while preserving the existing primary key and dependent foreign keys.

## 2. Files Modified
- `alembic/versions/20260424_0002_sources_soft_delete_schema.py`
- `tests/integration/test_source_health_migrations.py`
- `docs/backend/source_health_deleted_at_schema_mismatch_implementation_plan.md`
- `docs/backend/source_health_deleted_at_schema_mismatch_implementation_report.md`

## 3. Key Logic Implemented
- Updated the migration to use SQLite batch operations only where needed and PostgreSQL-safe in-place DDL everywhere else.
- Preserved the `sources` table identity by avoiding any `recreate="always"` path on PostgreSQL.
- Added regression assertions that the migrated schema keeps foreign keys from `source_runs`, `job_postings`, and `job_source_links`, exposes `deleted_at`, removes the legacy unique constraint, and creates the active-only dedupe index.

## 4. Assumptions Made
- The local PostgreSQL target is the correct environment for re-running the failing revision.
- Existing data in the local database does not violate the intended active-only uniqueness rule at migration time.

## 5. Validation Performed
- `"/tmp/job-intelligence-platform-venv/bin/python" -m pytest tests/integration/test_source_health_migrations.py`
- `DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/job_intelligence_platform" "/tmp/job-intelligence-platform-venv/bin/alembic" -c alembic.ini current` → `20260423_0001` before rerun
- `DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/job_intelligence_platform" "/tmp/job-intelligence-platform-venv/bin/alembic" -c alembic.ini upgrade head` → succeeded to `20260424_0002`
- PostgreSQL schema inspection confirmed `sources.deleted_at`, removal of `uq_sources_dedupe_key`, creation of `ix_sources_dedupe_key_active_unique`, and retained foreign keys from `source_runs.source_id`, `job_postings.primary_source_id`, and `job_source_links.source_id`
- Local HTTP smoke checks against `http://127.0.0.1:8000` with `Accept: text/html`:
  - `GET /source-health` → `200`
  - `GET /sources` → `200`
  - `GET /dashboard` → `200`

## 6. Known Limitations / Follow-Ups
- Automated repository regression coverage still executes on SQLite by default; PostgreSQL coverage currently relies on manual/local rerun.
- Downgrading after creating duplicate `dedupe_key` rows across deleted and active sources can fail because the legacy unconditional unique constraint is stricter than the upgraded design.
- `GET /dashboard` without an HTML-leaning `Accept` header still returns `500` because the route is declared with `response_class=HTMLResponse` but returns a `dict` for non-HTML requests; this was observed during smoke checks and appears unrelated to the migration fix.
- QA should still verify source delete/recreate flows in a PostgreSQL-backed runtime seeded with representative data.

## 7. Commit Status
- No commit created, per task instructions.
