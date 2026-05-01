# Implementation Report

## 1. Summary of Changes
Implemented backend/data-layer support for transient untracked ingestion jobs. Ingestion now persists only existing tracked matches, stores newly discovered untracked jobs in runtime memory, exposes transient API endpoints, and persists transient jobs plus related artifacts when tracked.

Remediated QA-blocking full-suite failures by updating stale tests/fixtures to align with transient untracked ingestion behavior and by stabilizing in-memory SQLite test harness boundaries.

## 2. Files Modified
- `app/domain/ingestion.py` — split tracked-match persistence from transient capture and added ingestion logging.
- `app/domain/classification.py` — extracted persistence-neutral classification snapshots and reused them for persisted decisions.
- `app/domain/transient_ingestion.py` — added thread-safe runtime transient registry and dataclasses.
- `app/domain/tracking.py` — added transient tracking persistence flow for job/source link/decision/rules/event.
- `app/schemas.py` — added transient list response schemas.
- `app/web/routes.py` — added transient list/detail/tracking routes.
- `alembic/versions/20260501_0005_cleanup_untracked_jobs.py` — added idempotent cleanup migration for untracked jobs and dependents.
- `tests/conftest.py` — clears transient registry between tests.
- `tests/unit/test_transient_ingestion_jobs.py` — added transient ingestion and tracking coverage.
- `tests/integration/test_api_flow.py` — updated ingestion flow expectations to track transient jobs before persisted-job operations.
- `docs/backend/transient_untracked_ingestion_jobs_implementation_plan.md` — implementation plan.
- `tests/conftest.py` — routes source-delete background cleanup through the shared fixture session during client tests so in-memory SQLite schema/data are visible.
- `tests/integration/test_html_views.py` — tracks transient jobs before persisted `/jobs` JSON and persisted tracking-route assertions.
- `tests/ui/test_source_edit_delete_ui_qa.py` — tracks transient jobs before source-delete UI assertions that need a persisted job.
- `tests/ui/test_saas_dashboard_ui_revamp.py` — uses the shared `client` fixture instead of a module-level `TestClient(app)` and seeds required persisted job/source data.
- `tests/unit/test_source_batch_run_qa_validation.py` — keeps the concurrency assertion but avoids threaded in-memory SQLite session access by faking per-source execution at the executor seam.

## 3. API Contract Implementation
Added:
- `GET /ingestion/transient-jobs` with optional integer `source_id` filter.
- `GET /ingestion/transient-jobs/{transient_job_id}` returning runtime detail or `404`.
- `POST /ingestion/transient-jobs/{transient_job_id}/tracking-status` returning `201` for new persistence, `200` for duplicate tracked match, `400` invalid status, `404` missing transient ID, and `409` legacy untracked conflict.

Existing persisted job endpoints remain unchanged.

No API contract changes were made in the remediation pass.

## 4. Data / Persistence Implementation
No schema changes. Added cleanup migration for `tracking_status IS NULL` jobs and dependent rows. New ingestion of unmatched jobs creates only `SourceRun`; no `JobPosting`, `JobSourceLink`, `JobDecision`, or `JobDecisionRule` rows are created for transient candidates.

No data model or storage changes were made in the remediation pass.

## 5. Key Logic Implemented
- Tracked = `tracking_status IS NOT NULL`; `manual_keep` is not used for persistence gating.
- Existing tracked matches are updated and classified through the persisted path.
- Newly discovered untracked candidates are classified with a persistence-neutral preview and stored in the transient registry.
- Registry replaces per-source results on successful ingestion, deduping by source/external ID, normalized URL, or canonical key.
- Tracking a transient job re-runs DB matching, persists or updates the tracked job, writes source link and classification records, emits tracking event, commits, then consumes the transient entry.
- Stale regression helpers now explicitly track transient jobs before asserting persisted job list/detail/tracking behavior.
- UI shell tests now receive normal test dependency overrides and schema setup via the repository fixture.
- The batch executor concurrency test now validates the five-worker cap without relying on unsafe threaded access to one in-memory SQLite connection.

## 6. Security / Authorization Implemented
Follows existing local single-user routing. Transient IDs are opaque runtime IDs. Tracking validates status server-side and ignores any client-provided job data beyond status/note.

Remediation changes are test/fixture-only and do not alter authentication, authorization, or production input handling.

## 7. Error Handling Implemented
- Invalid transient tracking status raises `400`.
- Missing/expired transient IDs raise `404`.
- Legacy persisted untracked DB matches during transient tracking raise `409`.
- Tracking transaction rolls back on exceptions and consumes the transient entry only after commit.

No production error handling changes were made in the remediation pass.

## 8. Observability / Logging
Ingestion logs fetched, persisted created/updated/unchanged, and transient capture counts.

No logging or monitoring changes were made in the remediation pass.

## 9. Assumptions Made
- Failed ingestion leaves the previous successful transient set unchanged because registry replacement happens only after successful candidate processing.
- `SourceRun.jobs_created_count` remains ingestion-time persisted effects only; later transient tracking does not mutate run counters.
- Source-delete API/UI tests that do not assert cleanup side effects may safely execute cleanup through the fixture session; source cleanup domain behavior remains covered by dedicated unit tests.
- The batch concurrency QA test is intended to validate the executor concurrency limit, not SQLite/threading behavior.

## 10. Validation Performed
- `python -m pytest tests/unit/test_transient_ingestion_jobs.py tests/integration/test_api_flow.py` — failed: `python` command unavailable.
- `python3 -m pytest tests/unit/test_transient_ingestion_jobs.py tests/integration/test_api_flow.py` — failed: `pytest` is not installed in the environment.
- `python3 -m compileall app tests` — passed; application and test Python files compiled successfully.
- `python3 -m compileall alembic/versions/20260501_0005_cleanup_untracked_jobs.py` — passed.
- Backend import validation attempted with `python3`; blocked because runtime dependency `sqlalchemy` is not installed in the environment.
- `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest tests/integration/test_html_views.py tests/ui/test_source_edit_delete_ui_qa.py tests/ui/test_saas_dashboard_ui_revamp.py tests/api/test_source_edit_delete_qa.py tests/integration/test_api_flow.py::test_source_patch_delete_and_delete_impact_flow tests/integration/test_api_flow.py::test_deleted_sources_are_removed_from_html_filters_and_inactive_sources_cannot_run tests/integration/test_source_edit_delete_html.py::test_source_delete_html_flow_hides_deleted_source_from_management_surfaces tests/unit/test_source_batch_run_qa_validation.py::test_batch_executor_never_exceeds_five_concurrent_source_runs` — passed: `23 passed in 0.64s`.
- `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest tests/unit/test_transient_ingestion_jobs.py tests/api/test_transient_untracked_ingestion_jobs_qa.py tests/integration/test_transient_untracked_cleanup_migration_qa.py tests/ui/test_transient_ingestion_jobs_ui.py tests/ui/test_hide_rejected_job_openings_ui.py` — passed: `15 passed in 0.38s`.
- `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest` — passed: `130 passed, 4 warnings in 3.22s`.
- `python3 -m compileall app tests` — passed.

## 11. Known Limitations / Follow-Ups
- Full suite is green locally. Remaining warnings are existing Alembic deprecation warnings in schema guard tests.

## 12. Commit Status
Original backend implementation committed in `2e16944` (`feat(backend): implement transient untracked ingestion jobs`). Remediation commit pending at report update time.
