# Bug Report

## 1. Summary
`GET /source-health` still fails with HTTP 500 in PostgreSQL-backed environments because the attempted fix migration (`20260424_0002`) is itself unsafe on PostgreSQL. The migration uses `batch_alter_table(..., recreate="always")` on `sources`, which forces table/primary-key recreation and fails while foreign keys from `source_runs`, `job_postings`, and `job_source_links` still reference `sources.id`. The upgrade aborts before `sources.deleted_at` is added, so runtime code continues to fail on `Source.deleted_at` queries.

## 2. Observed Symptoms
- failing workflow: `alembic upgrade 20260424_0002` on local PostgreSQL, followed by `GET /source-health`
- exact migration failure: PostgreSQL rejects the migration because it attempts to drop/recreate `sources_pkey` while dependent foreign keys still exist on tables including `source_runs`, `job_postings`, and `job_source_links`
- downstream runtime error: `psycopg.errors.UndefinedColumn: column sources.deleted_at does not exist`
- supplied failing path reaches `app/domain/operations.py`, where `OperationsService.list_source_health()` executes `select(Source).where(Source.deleted_at.is_(None))` (`app/domain/operations.py:13-14`)
- related query sites use the same column filter and are therefore also exposed to the same failure mode:
  - dashboard/source selectors (`app/web/routes.py:333-336`, `649`)
  - source management/list selectors (`app/web/routes.py:336`, `649`)
  - source service list/get/duplicate logic (`app/domain/sources.py:40-44`, `46-52`, `72-75`)

Observed behavior:
- PostgreSQL upgrade to `20260424_0002` fails before schema changes are applied
- `sources.deleted_at` remains absent after the failed upgrade
- environments that rely on PostgreSQL migrations still error as soon as code paths reference `sources.deleted_at`

Expected behavior:
- revision `20260424_0002` should apply cleanly on PostgreSQL without disturbing `sources` foreign-key relationships
- `/source-health` should return active sources successfully, excluding soft-deleted rows without raising SQL errors

## 3. Evidence Collected
- Files inspected:
  - `alembic/versions/20260424_0002_sources_soft_delete_schema.py`
  - `alembic/versions/20260423_0001_initial.py`
  - `app/persistence/models.py`
  - `app/domain/operations.py`
  - `app/domain/sources.py`
  - `app/web/routes.py`
  - `tests/integration/test_source_health_migrations.py`
  - `docs/qa/source_health_deleted_at_schema_mismatch_test_report.md`
- ORM/model evidence:
  - `Source` declares `deleted_at` on the model (`app/persistence/models.py:17-40`)
  - the model defines a partial unique index referencing `deleted_at` (`app/persistence/models.py:19-26`)
- Runtime/query evidence:
  - `OperationsService.list_source_health()` filters on `Source.deleted_at.is_(None)` (`app/domain/operations.py:13-14`)
  - `/source-health` calls that service directly (`app/web/routes.py:797-813`)
  - `SourceService` also uses `deleted_at` in list/get/duplicate logic (`app/domain/sources.py:40-44`, `46-52`, `72-75`)
- Migration evidence:
  - revision `20260424_0002` performs `op.batch_alter_table("sources", recreate="always")` before adding `deleted_at` and dropping `uq_sources_dedupe_key` (`alembic/versions/20260424_0002_sources_soft_delete_schema.py:24-28`)
  - the required logical changes are additive/in-place: add one nullable column, drop one unique constraint, and create one partial unique index (`alembic/versions/20260424_0002_sources_soft_delete_schema.py:24-36`)
  - the base schema already contains foreign keys to `sources.id` from:
    - `source_runs.source_id` (`alembic/versions/20260423_0001_initial.py:47-65`)
    - `job_postings.primary_source_id` (`alembic/versions/20260423_0001_initial.py:67-95`)
    - `job_source_links.source_id` (`alembic/versions/20260423_0001_initial.py:97-113`)
  - because the migration aborts before completion, `sources.deleted_at` is never added and the old unconditional uniqueness remains in place
- Environment/test evidence:
  - the migration regression test exercises SQLite only (`tests/integration/test_source_health_migrations.py:34-94`)
  - QA explicitly recorded that PostgreSQL was not available and PostgreSQL DDL/runtime behavior was not live-tested (`docs/qa/source_health_deleted_at_schema_mismatch_test_report.md:34-35`)

## 4. Root Cause Analysis
Immediate failure point:
- `20260424_0002_sources_soft_delete_schema.py` enters `op.batch_alter_table("sources", recreate="always")` (`alembic/versions/20260424_0002_sources_soft_delete_schema.py:24-28`). On PostgreSQL this attempts a table rebuild that requires dropping/recreating `sources_pkey`, but `source_runs`, `job_postings`, and `job_source_links` still have foreign keys to `sources.id` from the initial schema (`alembic/versions/20260423_0001_initial.py:47-113`). PostgreSQL blocks that operation, so the migration terminates before `deleted_at` is added.

Confirmed root cause:
- This is a backend migration defect with a release/deployment impact. The fix revision exists, but it was implemented with a table-recreation strategy that is incompatible with PostgreSQL foreign-key dependencies. Because deployment relies on applying Alembic migrations, the bad migration becomes a release blocker and leaves the application on a schema that still does not satisfy the backend's `deleted_at` contract.

Why this conclusion is supported by evidence:
- The codebase clearly expects `deleted_at` to exist in the ORM and query layer (`app/persistence/models.py`, `app/domain/operations.py`, `app/domain/sources.py`, `app/web/routes.py`).
- The fix migration uses `recreate="always"` even though the needed schema change does not require rebuilding the table (`alembic/versions/20260424_0002_sources_soft_delete_schema.py:24-36`).
- The `sources` table is referenced by multiple foreign keys in the base schema, so recreating it is materially different from a simple `ALTER TABLE` and is unsafe without explicitly handling dependent constraints (`alembic/versions/20260423_0001_initial.py:47-113`).
- The automated regression only proves the SQLite path; it does not cover PostgreSQL DDL behavior (`tests/integration/test_source_health_migrations.py:34-94`, `docs/qa/source_health_deleted_at_schema_mismatch_test_report.md:34-35`).

Failure classification:
- Backend migration issue: confirmed primary cause
- Release/deployment issue: confirmed secondary cause because PostgreSQL migration validation was not completed before rollout acceptance
- Frontend issue: not implicated

Impacted layers:
- Database migration/schema layer: primary defect
- Backend runtime/query layer: impacted because `/source-health` and related source queries depend on the missing column
- Release/QA layer: impacted because SQLite-only migration validation allowed the PostgreSQL-specific failure through

## 5. Confidence Level
- High

Reason:
- The supplied PostgreSQL failure mode directly matches the migration strategy in `20260424_0002`.
- The base schema definitively contains foreign keys that make `sources` table recreation unsafe.
- The runtime failure is a direct downstream consequence of the aborted migration.

## 6. Recommended Fix
- Rewrite `20260424_0002` to use PostgreSQL-safe in-place DDL instead of `batch_alter_table(..., recreate="always")`:
  - `op.add_column("sources", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))`
  - `op.drop_constraint("uq_sources_dedupe_key", "sources", type_="unique")`
  - `op.create_index("ix_sources_dedupe_key_active_unique", "sources", ["dedupe_key"], unique=True, postgresql_where=sa.text("deleted_at IS NULL"), sqlite_where=sa.text("deleted_at IS NULL"))`
- Preserve `sources.id` and `sources_pkey`; do not recreate the `sources` table and do not drop dependent foreign keys unless a separate explicit cross-table migration plan is required.
- Ensure the downgrade is also in-place: drop the partial index, recreate `uq_sources_dedupe_key`, then drop `deleted_at`.
- If any environment may contain drifted/manual data, run a preflight query before creating the partial unique index to confirm there are no duplicate active `dedupe_key` rows.
- Add PostgreSQL migration coverage to CI/release validation for Alembic-managed schemas.

## 7. Suggested Validation Steps
- Apply the revised Alembic migration to a PostgreSQL database created from `20260423_0001`.
- Confirm `sources` now contains `deleted_at` and that `sources_pkey` plus the foreign keys from `source_runs`, `job_postings`, and `job_source_links` remain intact.
- Confirm `uq_sources_dedupe_key` is gone and `ix_sources_dedupe_key_active_unique` exists with `WHERE deleted_at IS NULL`.
- Re-run `GET /source-health`; verify HTTP 200 and correct source list behavior.
- Re-check other affected surfaces:
  - `GET /dashboard`
  - `GET /sources`
  - source edit/delete flows
  - duplicate-source validation after deleting a source and recreating it
- Add/execute an integration check that boots a PostgreSQL DB through Alembic migrations and hits `/source-health`.

## 8. Open Questions / Missing Evidence
- The exact PostgreSQL error text from the local failed `alembic upgrade` was not captured in this repository, so the report relies on the supplied failure description plus the migration code shape.
- Affected environments should be checked for any partial schema drift before retrying a corrected migration.
