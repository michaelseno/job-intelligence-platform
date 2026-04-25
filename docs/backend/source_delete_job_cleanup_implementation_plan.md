# Implementation Plan

## 1. Feature Overview
Implement backend cleanup for deleted sources so associated jobs are asynchronously removed unless they are both `latest_bucket = matched` and `current_state = active`, while pending-cleanup non-retained jobs are hidden immediately.

## 2. Technical Scope
- Add source-delete cleanup domain service.
- Add centralized job visibility predicate.
- Queue cleanup from API and HTML source deletion routes using FastAPI background tasks.
- Apply visibility filtering to dashboard, jobs, job detail/actions, tracking, reminders, digest display, and notification generation.
- Add backend tests for retention matrix, idempotency, API response, and immediate visibility.

## 3. Files Expected to Change
- `app/domain/source_cleanup.py`
- `app/domain/job_visibility.py`
- `app/domain/notifications.py`
- `app/web/routes.py`
- `app/schemas.py`
- `tests/unit/test_source_delete_cleanup.py`
- `tests/unit/test_job_visibility.py`
- `tests/api/test_source_delete_job_cleanup_api.py`
- `tests/integration/test_source_delete_job_cleanup_surfaces.py`

## 4. Dependencies / Constraints
- No schema migration is required; cleanup status uses `source_runs`.
- Source deletion remains a soft delete via `sources.deleted_at`.
- Physical job deletion must explicitly remove dependent rows before deleting `job_postings`.
- Background cleanup must open its own session and not reuse request-scoped sessions.

## 5. Assumptions
- `JobPosting.latest_bucket` and `JobPosting.current_state` are authoritative for retention.
- Jobs associated through any deleted source are subject to cleanup, even if also linked to an active source.
- FastAPI in-process background tasks are sufficient for MVP async behavior.

## 6. Validation Plan
- Run targeted unit, API, and integration tests for source-delete cleanup.
- Run existing source edit/delete API tests for regression coverage.
- Run Python compile validation for modified app/test modules if needed.
