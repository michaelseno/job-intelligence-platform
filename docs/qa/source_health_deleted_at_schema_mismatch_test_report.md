# Test Report

## 1. Execution Summary
- total tests: 10
- passed: 10
- failed: 0

Executed validation:
- Static review of `alembic/versions/20260424_0002_sources_soft_delete_schema.py`
- `"/tmp/job-intelligence-platform-venv/bin/python" -m pytest tests/integration/test_source_health_migrations.py -q` → passed
- `"/tmp/job-intelligence-platform-venv/bin/python" -m pytest tests/unit/test_sources.py -q` → passed
- `"/tmp/job-intelligence-platform-venv/bin/python" -m pytest tests/integration/test_api_flow.py -q` → passed
- `"/tmp/job-intelligence-platform-venv/bin/python" -m pytest tests/integration/test_source_health_migrations.py tests/unit/test_sources.py tests/integration/test_api_flow.py --collect-only -q` → 10 tests collected
- Live PostgreSQL QA validation on isolated temporary database via local Alembic + SQLAlchemy + `TestClient`:
  - upgrade `20260423_0001` → `20260424_0002` succeeded
  - `sources.deleted_at` present after migration
  - `uq_sources_dedupe_key` removed
  - `ix_sources_dedupe_key_active_unique` present and defined with `WHERE (deleted_at IS NULL)`
  - foreign keys from `source_runs.source_id`, `job_postings.primary_source_id`, and `job_source_links.source_id` remained intact
  - active duplicate `dedupe_key` rejected; replacement after soft delete succeeded
  - `OperationsService.list_source_health()` returned only the active replacement source
  - `/source-health`, `/sources`, and `/dashboard` HTML requests returned HTTP 200 in migrated PostgreSQL-backed app context

Validated acceptance evidence:
- Live PostgreSQL Alembic upgrade from `20260423_0001` to `20260424_0002` completed successfully on an isolated temporary database.
- `sources.deleted_at` exists after migration.
- Migration removes `uq_sources_dedupe_key` and creates partial unique index `ix_sources_dedupe_key_active_unique` with PostgreSQL predicate `WHERE (deleted_at IS NULL)`.
- Foreign keys from `source_runs`, `job_postings`, and `job_source_links` to `sources.id` remained intact after upgrade.
- PostgreSQL behavioral validation passed for: active duplicate rejection, soft-deleted row replacement, and active-only health listing.
- Migrated PostgreSQL-backed app smoke checks returned HTTP 200 for `/source-health`, `/sources`, and `/dashboard` HTML; `/source-health` and `/sources` rendered the active replacement source.
- Adjacent source API/service regressions passed in existing automated suites.

## 2. Failed Tests
- None.

## 3. Failure Classification
- None.

## 4. Observations
- Repository-level regression coverage includes an Alembic-driven upgrade path, which directly addresses the prior gap where tests only used `Base.metadata.create_all()`.
- QA additionally verified the fix on live PostgreSQL, which closes the original environment-specific validation gap.
- PostgreSQL app smoke validation confirmed the migrated `/source-health` path returns 200 instead of the previously reported 500.
- `product_spec.md` was not present in the repository root during QA; acceptance criteria were derived from the supplied bug report and backend implementation report.
- The observed `/dashboard` HTML success is within the constrained acceptance scope; the known non-HTML `/dashboard` response issue documented by backend remains outside this regression fix.

## 5. QA Decision
APPROVED

Rationale:
- All critical automated regressions passed.
- Live PostgreSQL migration, schema, behavioral, and migrated app smoke validations passed.
- No blocking defects were observed within the scope of this regression.
