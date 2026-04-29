# Implementation Report

## 1. Summary of Changes
Implemented backend source-health cleanup fixes for invalid configured sources, duplicate source prevention/cleanup, and Lever parser robustness.

Follow-up remediation added a startup schema guardrail so migrated PostgreSQL databases behind repository Alembic head fail fast with an actionable `alembic upgrade head` message instead of route-level `UndefinedColumn` errors.

Second follow-up added 13 newly validated ATS sources through an idempotent Alembic seed migration.

## 2. Files Modified
- `app/domain/sources.py` — added normalized company/provider key generation and duplicate validation.
- `app/persistence/models.py` — added `Source.company_provider_key` and active unique index metadata.
- `app/domain/source_health_cleanup.py` — added idempotent soft-delete cleanup for removed sources and duplicate active company/provider sources.
- `app/domain/source_seed.py` — added the validated source catalog and idempotent seed function.
- `app/persistence/schema_guard.py` — added Alembic revision guardrail helpers and actionable stale-schema error.
- `app/main.py` — runs the schema guardrail during startup for non-SQLite databases.
- `app/adapters/lever/adapter.py` — made Lever list-content parsing tolerant of strings, list strings, and dict entries.
- `alembic/versions/20260429_0003_source_company_provider_key.py` — added migration to backfill keys, run cleanup, and create the active unique index.
- `alembic/versions/20260429_0004_add_validated_sources.py` — added migration to seed 13 validated sources idempotently.
- `tests/unit/test_sources.py` — added duplicate prevention coverage.
- `tests/unit/test_source_health_cleanup.py` — added cleanup behavior coverage.
- `tests/adapter_contract/test_lever_adapter.py` — added Lever parser robustness coverage.
- `tests/integration/test_source_health_migrations.py` — asserted the new migration column/index.
- `tests/unit/test_schema_guard.py` — added stale/current/no-version guardrail coverage.
- `tests/unit/test_source_seed.py` — added validated source seed/idempotency/no-notes coverage.
- `README.md` — documented that source health cleanup requires migration `20260429_0003` / `alembic upgrade head` before server use.
- `docs/backend/source_health_cleanup_implementation_plan.md` — documented implementation plan.

## 3. API Contract Implementation
No API contract changes. Existing create/update/import flows now reject duplicate active company/provider sources through existing validation behavior.

Startup behavior now fails before serving PostgreSQL-backed routes if the connected migrated database is behind Alembic head.

## 4. Data / Persistence Implementation
Added nullable `sources.company_provider_key` plus a partial unique index on active non-deleted rows. Migration backfills this key, soft-deletes confirmed removed sources, soft-deletes duplicate active company/provider rows, then creates the unique index.

The application does not auto-run migrations. Operators must run `alembic upgrade head` against the server `DATABASE_URL`. Migration `20260429_0004` seeds the validated sources and skips existing active company/provider or dedupe-key matches.

## 5. Key Logic Implemented
- Duplicate key: normalized company name when present, otherwise source name, plus provider.
- Built-in providers use `source_type`; adapter-key providers include `adapter_key`.
- Cleanup removes confirmed invalid/requested sources and chooses duplicate keepers by healthy status, successful last run, recency, then id.
- Insider Lever remains valid; parser no longer calls `.get()` on string content.
- PostgreSQL startup checks compare the connected DB `alembic_version` to repository head and raise a clear stale-schema error when behind.
- Added validated sources: Point Wild Greenhouse, Fundraise Up Greenhouse, Shift Technology Greenhouse, The Economist Group Greenhouse, Tailscale Greenhouse, HighLevel Lever, Cloaked Lever, Drivetrain Lever, Celara Lever, Fullscript Lever, Panopto Lever, dLocal Lever, and Coderio Lever.
- Validation context/role text is not persisted; seeded source `notes` are `None`.

## 6. Security / Authorization Implemented
No new endpoint or auth surface. Existing source service validation is reused; cleanup uses soft-delete only and does not log or expose sensitive data.

## 7. Error Handling Implemented
Duplicate source attempts continue to return the existing `Duplicate source already exists.` validation error path. Lever parser skips unexpected list shapes instead of failing ingestion with `AttributeError`.

Stale migrated databases now fail fast with: `Database schema is out of date... Run alembic upgrade head...`.

## 8. Observability / Logging
No new logging added; no external call behavior changed.

## 9. Assumptions Made
- Provider identity is `source_type` for built-in ATS providers and `source_type + adapter_key` for adapter-key based providers.
- Soft-delete (`deleted_at` set and `is_active=False`) is the existing project convention for source removal.

## 10. Validation Performed
- `python -m pytest ...` failed because `python` is unavailable in this environment.
- `python3 -m pytest ...` failed because pytest is not installed for the system Python.
- `python3 -m compileall app alembic` passed.
- `PYTHONPATH=. uv run --with-editable . pytest tests/unit/test_sources.py tests/unit/test_source_health_cleanup.py tests/adapter_contract/test_lever_adapter.py tests/integration/test_source_health_migrations.py` passed: `13 passed in 1.16s`.
- `PYTHONPATH=. uv run --with-editable . pytest tests/unit/test_schema_guard.py tests/unit/test_sources.py tests/unit/test_source_health_cleanup.py tests/adapter_contract/test_lever_adapter.py tests/integration/test_source_health_migrations.py` passed after guardrail remediation: `17 passed, 4 warnings in 1.24s`.
- `python3 -m compileall app alembic` passed after guardrail remediation.
- `PYTHONPATH=. uv run --with-editable . pytest tests/unit/test_source_seed.py tests/unit/test_schema_guard.py tests/unit/test_sources.py tests/unit/test_source_health_cleanup.py tests/adapter_contract/test_lever_adapter.py tests/integration/test_source_health_migrations.py` passed after source additions: `20 passed, 4 warnings in 1.25s`.
- `python3 -m compileall app alembic` passed after source additions.

## 11. Known Limitations / Follow-Ups
- No frontend changes were required.
- Manual local recovery/source seeding is still required for already-stale PostgreSQL databases: run `alembic upgrade head` using the same `DATABASE_URL` as the server, then restart the app.
- The bug report file is present as an untracked upstream artifact and was not modified.

## 12. Commit Status
Commit was not created per user instruction: “Do not commit, push, or create a PR.”
