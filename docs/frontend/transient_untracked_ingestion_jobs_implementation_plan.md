# Implementation Plan

## 1. Feature Overview
Expose backend transient untracked ingestion jobs on the existing Jobs review surface, clearly mark them as temporary, and allow users to assign a non-null tracking status to save them as persisted tracked jobs.

## 2. Technical Scope
- Augment `/jobs` HTML rendering with persisted tracked/actionable jobs plus current transient ingestion jobs from the runtime registry.
- Keep JSON `/jobs` behavior persisted-only; transient API endpoints remain separate.
- Add a runtime-safe transient detail route for HTML review.
- Submit transient tracking forms to `POST /ingestion/transient-jobs/{transient_job_id}/tracking-status`.
- Add progressive enhancement for saving/loading state without requiring JavaScript.

## 3. UI/UX Inputs
- Jobs page must show a Temporary ingestion results callout only when transient results are present.
- Results summary must distinguish tracked and temporary counts.
- Transient rows/cards must show visible `Temporary` text and screen-reader clarification.
- Transient details must not link to persisted `/jobs/{job_id}` until after tracking succeeds.
- Tracking controls must include accessible labels and saving feedback.

## 4. Files Expected to Change
- `app/web/routes.py`
- `app/web/templates/includes/macros.html`
- `app/web/templates/jobs/list.html`
- `app/web/templates/jobs/transient_detail.html`
- `app/web/static/styles.css`
- `app/web/static/app.js`
- `tests/ui/test_transient_ingestion_jobs_ui.py`
- `docs/frontend/transient_untracked_ingestion_jobs_implementation_report.md`

## 5. Dependencies / Constraints
- Backend transient registry and tracking APIs are available on the current branch.
- Transient data is runtime-only and must not be read from persisted untracked rows.
- Existing persisted job tracking and keep behavior must remain unchanged.
- No new primary navigation item is allowed.

## 6. Assumptions
- `/jobs` filters should apply to transient results where equivalent fields exist; a non-empty tracking status filter excludes transient results because their tracking status is null.
- Failed ingestion refresh behavior is backend-owned; UI displays current registry contents and existing flash copy.

## 7. Validation Plan
- Add UI tests for mixed persisted/transient jobs, temporary callout/badge/count summary, runtime-safe links, and transient tracking form action/labels.
- Run focused UI/integration tests plus the existing transient unit tests.
- Run the full pytest suite if time/environment allows.
