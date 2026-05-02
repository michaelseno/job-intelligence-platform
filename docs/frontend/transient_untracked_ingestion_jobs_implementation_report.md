# Implementation Report

## 1. Summary of Changes
- Added transient ingestion jobs to the `/jobs` HTML review surface alongside persisted jobs.
- Added visible temporary callout, `Temporary` badges, accessible screen-reader copy, and count summary separating tracked versus temporary results.
- Added runtime-safe transient detail pages at `/jobs/transient/{transient_job_id}`.
- Wired transient tracking forms to `POST /ingestion/transient-jobs/{transient_job_id}/tracking-status` with progressive saving-state enhancement.
- Added source-run success copy that references temporary untracked results when available.

## 2. Files Modified
- `app/web/routes.py`
- `app/templates/jobs/list.html`
- `app/templates/jobs/transient_detail.html`
- `app/templates/macros/ui.html`
- `app/static/css/app.css`
- `app/static/js/app.js`
- Mirrored duplicate template/static changes under `app/web/...` for repository consistency.
- `tests/ui/test_transient_ingestion_jobs_ui.py`
- `docs/frontend/transient_untracked_ingestion_jobs_implementation_plan.md`

## 3. UI Behavior Implemented
- `/jobs` displays persisted jobs and current runtime transient ingestion jobs for HTML requests.
- JSON `/jobs` remains persisted-only; transient API endpoints remain separate.
- Transient rows link to `/jobs/transient/{transient_job_id}`, not `/jobs/{id}`.
- Transient tracking forms require a non-empty tracking status and submit to the new backend transient tracking endpoint.
- JavaScript disables the transient status select/button on submit, sets `aria-busy="true"`, and changes button text to `Saving…`.
- Missing transient details render a clear unavailable message with `404` status.

## 4. Assumptions Made
- Existing `/jobs` filters apply to transient results where equivalent fields exist.
- Non-empty tracking-status filters exclude transient jobs because transient jobs have no tracking status until saved.
- Existing duplicate template/static trees should remain synchronized.

## 5. Validation Performed
- Passed: `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest tests/ui/test_transient_ingestion_jobs_ui.py tests/unit/test_transient_ingestion_jobs.py`
- Passed: `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest tests/ui/test_transient_ingestion_jobs_ui.py tests/unit/test_transient_ingestion_jobs.py tests/ui/test_hide_rejected_job_openings_ui.py`
- Full suite attempted with `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest`; result: 108 passed, 18 failed. Failures are existing/stale-test or environment-style regressions unrelated to the UI change, primarily tests still expecting ingestion-created untracked jobs in `/jobs` JSON and background cleanup tests using a separate empty in-memory DB connection.
- Initial `pytest`/`python -m pytest` commands could not run because global `pytest`/`python` were unavailable; validation used `uv run`.

## 6. Known Limitations / Follow-Ups
- Full-suite failures require upstream test updates for the new transient-only ingestion behavior and/or test DB configuration cleanup.
- The app has duplicate active/legacy template and static directories; changes were mirrored to reduce drift.

## 7. Commit Status
- Included in the frontend implementation commit for this work.
