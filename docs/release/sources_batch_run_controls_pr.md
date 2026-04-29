# Pull Request

## 1. Feature Name
Sources Batch Run Controls and Action Layout Refresh

## 2. Summary
Adds Sources page batch run controls so users can run all Healthy sources or selected Healthy sources with confirmation, live progress, and completion summaries. Refreshes row actions into compact accessible icon controls while preserving destructive styling for delete.

## 3. Related Documents
- Product Spec: docs/product/sources_batch_run_controls_action_layout_refresh_product_spec.md
- Technical Design: docs/architecture/sources_batch_run_controls_architecture.md
- UI/UX Spec: docs/uiux/sources_batch_run_controls_uiux.md
- QA Test Plan: docs/qa/sources_batch_run_controls_test_plan.md
- QA Report: docs/qa/sources_batch_run_controls_qa_report.md
- Backend Implementation: docs/backend/sources_batch_run_controls_backend.md
- Frontend Implementation: docs/frontend/sources_batch_run_controls_frontend.md

## 4. Changes Included
- Adds backend preview, start, and status APIs for source batch runs.
- Executes Healthy-only source batches with fixed concurrency of 5, up to 3 total attempts per eligible source, short retry backoff, skipped-source handling, and continuation after per-source failures.
- Adds Sources toolbar actions for Run All and Run Selected, row selection, confirmation modal, active progress panel, completion summary, and duplicate-start prevention.
- Refreshes source row actions into accessible icon buttons/links while keeping delete visually destructive.
- Adds automated unit, API, integration, and QA validation coverage for batch behavior and UI rendering hooks.

## 5. QA Status
- Approved: YES
- QA Evidence: 130 automated checks passed, 0 unresolved failures.
- QA Report: docs/qa/sources_batch_run_controls_qa_report.md

## 6. Test Coverage
- Backend unit/service coverage validates Healthy-only eligibility, skipped-source reporting, duplicate selected ID handling, zero-eligible no-execution behavior, preview consumption, active batch conflicts, retries, and concurrency.
- API coverage validates preview/start/status contracts and error handling.
- Integration/UI-static coverage validates toolbar, selection, confirmation, progress/summary hooks, row action accessibility labels, route preservation, and destructive delete styling.
- Regression coverage includes full Python regression suite and JavaScript helper regression suite.

## 7. Risks / Notes
- Batch preview and status state is process-local and intentionally not persisted; state can be lost on process restart or may need redesign for multi-worker deployments.
- Cross-page selection is out of scope unless already supported by the current table selection model.
- Browser screenshot and full browser accessibility automation were limited in this environment; validation used server-rendered HTML/integration assertions and JavaScript/static review.

## 8. Linked Issue
- Closes #14
