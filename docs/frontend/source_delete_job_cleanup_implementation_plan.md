# Implementation Plan

## 1. Feature Overview
Source deletion UI must explain that deleting a source immediately removes it from active configuration and queues asynchronous cleanup for associated jobs. Only jobs that are both Matched and Active may remain visible.

## 2. Technical Scope
- Update the existing server-rendered source delete confirmation copy.
- Update the HTML delete success flash copy to align with the backend cleanup behavior.
- Mark retained deleted-source provenance as historical/non-actionable where source names are displayed in job list/detail templates.
- Add/update UI tests for copy, flash messaging, deleted source filter exclusion, provenance labeling, and normal not-found handling for non-retained deleted-source jobs.

## 3. UI/UX Inputs
- `docs/architecture/source_delete_job_cleanup_technical_design.md`
- `docs/uiux/source_delete_job_cleanup_uiux_spec.md`
- `docs/product/source_delete_job_cleanup_product_spec.md`
- `docs/backend/source_delete_job_cleanup_implementation_report.md`
- `docs/qa/source_delete_job_cleanup_test_plan.md`

## 4. Files Expected to Change
- `app/web/templates/sources/delete_confirm.html`
- `app/web/templates/jobs/list.html`
- `app/web/templates/jobs/detail.html`
- `app/web/routes.py`
- `tests/ui/test_source_edit_delete_ui_qa.py`
- `docs/frontend/source_delete_job_cleanup_implementation_plan.md`
- `docs/frontend/source_delete_job_cleanup_implementation_report.md`

## 5. Dependencies / Constraints
- Backend visibility filtering and async cleanup are treated as the source of truth.
- No progress bars, polling, undo/restore, retry controls, or configurable retention UI should be introduced.
- Source filters should continue to use only non-deleted sources.

## 6. Assumptions
- Exact retained/removal counts are not currently available in `DeleteImpactSummary`, so confirmation copy remains rule-based while preserving existing linked/tracked/run stat cards.
- Deleted-source provenance can be represented with the existing muted badge pattern.

## 7. Validation Plan
- Run targeted UI tests for source delete UI behavior.
- Run Python compile validation for changed app/test files if pytest is unavailable.
