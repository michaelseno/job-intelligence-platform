# Implementation Plan

## 1. Feature Overview
Fix the `/source-health` regression caused by runtime soft-delete queries expecting `sources.deleted_at` before Alembic-managed databases create that column.

## 2. Technical Scope
- Rewrite revision `20260424_0002` so PostgreSQL uses in-place DDL on `sources`.
- Introduce the missing nullable `deleted_at` column without recreating `sources`.
- Replace the legacy unconditional `dedupe_key` uniqueness with an active-row-only unique index.
- Add regression coverage that verifies the migrated schema still preserves `sources` foreign-key dependents and `/source-health` queryability.

## 3. Files Expected to Change
- `alembic/versions/20260424_0002_sources_soft_delete_schema.py`
- `tests/integration/test_source_health_migrations.py`
- `docs/backend/source_health_deleted_at_schema_mismatch_implementation_plan.md`
- `docs/backend/source_health_deleted_at_schema_mismatch_implementation_report.md`

## 4. Dependencies / Constraints
- Must remain aligned with the existing `Source` ORM contract.
- Must preserve existing `sources` rows, `sources_pkey`, and dependent foreign keys during upgrade.
- Must avoid changing unrelated frontend or runtime behavior.
- Must not modify unrelated untracked files or create a git commit.

## 5. Assumptions
- The tracked Alembic history in this branch is the authoritative migration chain for the affected environments.
- SQLite-based regression coverage remains useful for the migration chain, while live PostgreSQL rerun will be used to validate the PostgreSQL-specific DDL path.

## 6. Validation Plan
- Run the migration regression pytest coverage.
- Re-run Alembic against the confirmed local PostgreSQL database target.
- Confirm the upgraded schema adds `deleted_at`, removes `uq_sources_dedupe_key`, creates `ix_sources_dedupe_key_active_unique`, and preserves foreign keys to `sources.id`.
- Perform practical smoke checks for `/source-health`, `/sources`, and `/dashboard` against the migrated database.
