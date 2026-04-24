# Implementation Plan

## 1. Feature Overview
Implement backend support for editing and soft deleting sources while preserving historical job, run, and provenance references.

## 2. Technical Scope
- Add tombstone-aware source persistence behavior.
- Extend `SourceService` for partial update merge, duplicate-safe validation, delete impact summaries, and soft delete state transitions.
- Add JSON update/delete/delete-impact endpoints.
- Enforce deleted-source filtering in operational source reads and run eligibility checks.
- Add regression coverage for update, delete, filtering, and inactive-run behavior.

## 3. Files Expected to Change
- `app/persistence/models.py`
- `app/schemas.py`
- `app/domain/sources.py`
- `app/domain/operations.py`
- `app/web/routes.py`
- `tests/unit/test_sources.py`
- `tests/integration/test_api_flow.py`
- `docs/backend/source_edit_delete_implementation_report.md`

## 4. Dependencies / Constraints
- Must follow `docs/architecture/source_edit_delete_technical_design.md`.
- Soft delete must preserve historical foreign-key relationships.
- Deleted sources must be excluded from normal operational views but still remain resolvable for historical reads.
- No frontend/template work beyond existing backend route compatibility.

## 5. Assumptions
- Existing HTML templates and routes may already be in progress elsewhere; backend work will focus on data/service/API behavior.
- Partial unique dedupe behavior is modeled at the ORM metadata layer for fresh schema creation in local/test environments.
- Update JSON payloads are partial and merged onto persisted state before validation.

## 6. Validation Plan
- Run targeted source unit/integration tests.
- Run the full pytest suite after backend changes land.
