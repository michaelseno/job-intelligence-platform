# Implementation Report

## 1. Summary of Changes
Implemented backend source-delete job cleanup. Deleting a source now queues background cleanup, non-retained deleted-source jobs are hidden immediately from backend surfaces, and cleanup permanently deletes eligible jobs plus dependent records while retaining matched active jobs.

QA remediation update: fixed the nullable cleanup retention predicate so unclassified associated jobs are physically deleted, restored JSON-by-default API behavior for TestClient/API callers, corrected dashboard reminder data shape, and addressed source edit/delete HTML regression copy while keeping cleanup metadata limited to the DELETE source API contract.

## 2. Files Modified
- `app/domain/source_cleanup.py`
- `app/domain/job_visibility.py`
- `app/domain/notifications.py`
- `app/web/routes.py`
- `app/templates/sources/detail.html`
- `app/templates/sources/delete_confirm.html`
- `app/schemas.py`
- `tests/unit/test_source_delete_cleanup.py`
- `tests/unit/test_job_visibility.py`
- `tests/api/test_source_delete_job_cleanup_api.py`
- `tests/integration/test_source_delete_job_cleanup_surfaces.py`
- `docs/backend/source_delete_job_cleanup_implementation_plan.md`
- `docs/backend/source_delete_job_cleanup_implementation_report.md`

## 3. Key Logic Implemented
- `SourceDeleteCleanupService.cleanup_source(source_id)` discovers jobs associated by primary source or source links, retains only matched active jobs, deletes dependents in the design-specified order, and records `source_runs` cleanup status.
- Final job deletion now uses an explicit nullable inverse retention predicate so only rows with both `latest_bucket = "matched"` and `current_state = "active"` survive; `NULL` or any other value is deleted.
- `run_source_delete_cleanup(source_id)` opens a fresh `SessionLocal` session for background execution.
- `visible_job_predicate()` centralizes immediate visibility: jobs associated with deleted sources are hidden unless matched active.
- Source deletion API/HTML routes enqueue cleanup after successful source soft-delete and return/flash cleanup queued messaging.
- Dashboard counts, job list/detail/actions, tracking, reminders, digest latest, digest generation, and reminder generation now exclude pending-cleanup non-retained jobs.
- API/content negotiation now returns JSON for default `*/*` API/TestClient requests and HTML only when requested by `Accept: text/html` or form flows.
- Dashboard HTML now receives `reminder_jobs` as a sliceable list matching the template contract.

## 4. Assumptions Made
- Cleanup failure observability through logs plus `source_runs` is sufficient for MVP.
- No durable retry queue is introduced; retry safety is handled by idempotent cleanup logic.
- Source-linked jobs from a deleted source are cleanup-eligible even when another active source also links to them.

## 5. Validation Performed
- Targeted QA suite passed: `.venv/bin/python -m pytest tests/unit/test_source_delete_cleanup.py tests/unit/test_job_visibility.py tests/api/test_source_delete_job_cleanup_api.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/ui/test_source_edit_delete_ui_qa.py tests/unit/test_source_edit_delete.py tests/api/test_source_edit_delete_qa.py tests/integration/test_source_edit_delete_html.py` → `19 passed`.
- Syntax validation passed: `.venv/bin/python -m compileall app tests/unit/test_source_delete_cleanup.py tests/api/test_source_delete_job_cleanup_api.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/api/test_source_edit_delete_qa.py tests/integration/test_source_edit_delete_html.py tests/ui/test_source_edit_delete_ui_qa.py`.
- Whitespace validation passed: `git diff --check`.

## 6. Known Limitations / Follow-Ups
- FastAPI `BackgroundTasks` are in-process and not durable across process shutdowns; a future sweeper or durable queue could retry failed/missing cleanup runs.
- The route layer now falls back to the existing `app/web/templates/jobs` files for jobs HTML rendering because `app/templates/jobs` is absent. The broader duplicate/deleted template-file hygiene noted by QA remains a frontend/repository cleanup follow-up.

## 7. Commit Status
Not committed per user instruction. No push or PR was created.
