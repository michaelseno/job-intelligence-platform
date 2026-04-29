# Implementation Plan

## 1. Feature Overview
Fix backend source health noise caused by invalid configured ATS sources, duplicate active source records, and a Lever payload parsing error.

## 2. Technical Scope
- Enforce one active source per normalized company/provider key while still allowing the same company on different providers.
- Add idempotent source-health cleanup logic to soft-delete requested invalid/removed sources and duplicate active sources.
- Add the 13 newly validated ATS sources through an idempotent migration/seed path.
- Make Lever parsing tolerate `lists[].content` values that are strings, lists of strings, or lists of dicts.
- Add a startup schema guardrail for migrated PostgreSQL databases so stale Alembic revisions fail fast with an `alembic upgrade head` recovery message.
- Add focused backend tests for duplicate prevention, cleanup behavior, source removal rules, and Lever parser robustness.

## 3. Source Inputs
- `docs/bugs/source_health_cleanup.md`
- Existing source service, source soft-delete, ingestion, adapter, and migration patterns.

## 4. API Contracts Affected
No API contract changes. Existing source create/update/import endpoints retain their response formats but reject active duplicate company/provider sources earlier.

## 5. Data Models / Storage Affected
- `sources.company_provider_key` added as a nullable persisted normalized business key.
- Active unique index added on `company_provider_key` where `deleted_at IS NULL`.
- Data cleanup soft-deletes known removed sources and active duplicates according to existing `deleted_at`/`is_active` conventions.

## 6. Files Expected to Change
- `app/domain/sources.py`
- `app/domain/source_health_cleanup.py` or equivalent cleanup module
- `app/domain/source_seed.py`
- `app/persistence/schema_guard.py`
- `app/main.py`
- `app/persistence/models.py`
- `app/adapters/lever/adapter.py`
- `alembic/versions/*.py`
- Focused tests under `tests/unit/` and `tests/adapter_contract/`
- `docs/backend/source_health_cleanup_implementation_report.md`

## 7. Security / Authorization Considerations
No new endpoint or authorization surface is introduced. User-controlled source values are normalized before uniqueness checks. Cleanup uses existing soft-delete behavior and does not expose sensitive data.

## 8. Dependencies / Constraints
No new dependencies. Cleanup and source additions must be safe/idempotent and compatible with SQLite test databases and PostgreSQL production/local databases. PostgreSQL startup now requires the connected DB Alembic revision to be at repository head; operators should run `alembic upgrade head` before server use. Validated source additions are applied by migration `20260429_0004`.

## 9. Assumptions
- Provider identity is `source_type` for built-in ATS providers and `source_type + adapter_key` for adapter-key based providers.
- When selecting duplicate keepers, healthy or successful sources are preferred, then the most recent run/update/create timestamp.

## 10. Validation Plan
- `python -m pytest tests/unit/test_sources.py tests/unit/test_source_health_cleanup.py tests/adapter_contract/test_lever_adapter.py`
- `python -m pytest tests/unit/test_schema_guard.py`
- `python -m pytest tests/unit/test_source_seed.py`
- `python -m compileall app alembic`
