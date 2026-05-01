# Implementation Plan

## 1. Feature Overview
Implement backend/data-layer support for transient untracked ingestion jobs so only jobs with non-null `tracking_status` are persisted.

This remediation pass fixes QA-blocking full-suite failures caused by stale regression tests and in-memory SQLite test harness isolation after the transient untracked ingestion behavior change.

## 2. Technical Scope
- Gate ingestion persistence to existing tracked job matches only.
- Store new untracked ingestion candidates in a process-local transient registry.
- Add persistence-neutral classification previews.
- Add transient list/detail/tracking API paths.
- Persist transient jobs and dependent records when a valid non-null tracking status is assigned.
- Add cleanup migration for existing untracked persisted jobs and dependents.
- Update stale tests that expected ingestion-created untracked jobs to be available from persisted `/jobs` JSON.
- Ensure source-delete background cleanup tests use the shared test session instead of production `SessionLocal` under in-memory SQLite.
- Update UI shell tests to use the repository `client` fixture and seed required test data.
- Stabilize batch concurrency validation so it measures executor concurrency without threaded in-memory SQLite session contention.

## 3. Source Inputs
- `docs/architecture/transient_untracked_ingestion_jobs_technical_design.md`
- `docs/product/transient_untracked_ingestion_jobs_product_spec.md`
- `docs/qa/transient_untracked_ingestion_jobs_test_plan.md`
- `docs/qa/transient_untracked_ingestion_jobs_test_report.md`
- `docs/bugs/transient_untracked_ingestion_jobs_full_suite_failures_bug_report.md`
- `docs/release/transient_untracked_ingestion_jobs_issue.md`

## 4. API Contracts Affected
- `GET /ingestion/transient-jobs?source_id=<int>` returns `{ "items": [...] }` with current runtime transient jobs.
- `GET /ingestion/transient-jobs/{transient_job_id}` returns transient detail or `404`.
- `POST /ingestion/transient-jobs/{transient_job_id}/tracking-status` accepts `tracking_status` and optional `note_text`; returns `201` for newly persisted jobs, `200` for tracked duplicates, `400` invalid status, `404` missing transient ID, `409` legacy untracked DB conflict.
- Existing persisted job endpoints remain unchanged.

No API contract changes in the remediation pass.

## 5. Data Models / Storage Affected
- No schema model changes.
- Runtime-only `TransientIngestionJob` registry added; not durable.
- Alembic cleanup deletes `job_postings.tracking_status IS NULL` and dependent `job_source_links`, `job_decisions`, `job_decision_rules`, `job_tracking_events`, `reminders`, and `digest_items`.

No data model or storage changes in the remediation pass.

## 6. Files Expected to Change
- `app/domain/ingestion.py`
- `app/domain/classification.py`
- `app/domain/transient_ingestion.py`
- `app/domain/tracking.py`
- `app/schemas.py`
- `app/web/routes.py`
- `alembic/versions/20260501_0005_cleanup_untracked_jobs.py`
- Backend tests and fixtures.
- `tests/conftest.py` — shared test-session cleanup hook for background source delete tasks.
- `tests/integration/test_html_views.py` — update ingestion helpers to explicitly track transient jobs before persisted job assertions.
- `tests/ui/test_source_edit_delete_ui_qa.py` — update stale persisted-job setup.
- `tests/ui/test_saas_dashboard_ui_revamp.py` — use shared client fixture and seed required shell data.
- `tests/unit/test_source_batch_run_qa_validation.py` — avoid threaded in-memory SQLite DB access in concurrency-only assertion.

## 7. Security / Authorization Considerations
Existing app has local single-user behavior. Transient IDs are opaque strings and never used for DB lookup. Tracking validates status server-side and persists only server-held transient data, not client-provided job fields.

## 8. Dependencies / Constraints
No new dependencies. Uses existing SQLAlchemy, FastAPI, Alembic, classification, and tracking conventions.

## 9. Assumptions
- Failed ingestion keeps the last successful transient set because replacement occurs only after successful adapter/classification processing.
- `SourceRun.jobs_created_count` remains an ingestion-time persisted-created count and is not incremented when transient jobs are later tracked.
- Source-delete API/UI tests that do not assert cleanup side effects may safely execute cleanup through the fixture session; source cleanup domain behavior remains covered by dedicated unit tests.
- The batch concurrency QA test is intended to validate the `MAX_CONCURRENCY=5` executor contract, not SQLAlchemy/SQLite threading behavior.

## 10. Validation Plan
- `python -m pytest tests/unit/test_transient_ingestion_jobs.py`
- `python -m pytest tests/integration/test_api_flow.py`
- Targeted migration/import validation as needed.
- `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest` for the full suite if feasible.
- At minimum, run all previously failing tests plus transient feature tests from the QA report.
