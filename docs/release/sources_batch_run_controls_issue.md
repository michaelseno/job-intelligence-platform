# GitHub Issue

## 1. Feature Name
Sources Batch Run Controls and Action Layout Refresh

## 2. Problem Summary
Users currently need to trigger each source individually from the Sources page. For installations with many sources, this creates repetitive work, increases time to begin ingestion, and increases the chance that a source is missed.

This feature adds Sources page batch execution controls so users can run all healthy sources or a selected set of healthy sources with confirmation, bounded concurrency, retry handling, live progress, and a completion summary. It also refreshes the row action layout by moving batch actions to the top toolbar and allowing compact accessible row action buttons while preserving destructive styling for delete actions.

## 3. Linked Planning Documents
- Product Spec: `docs/product/sources_batch_run_controls_action_layout_refresh_product_spec.md`
- Technical Design: `docs/architecture/sources_batch_run_controls_architecture.md`
- UI/UX Spec: `docs/uiux/sources_batch_run_controls_uiux.md`
- QA Test Plan: `docs/qa/sources_batch_run_controls_test_plan.md`

## 4. Scope Summary
In scope:
- Add top-toolbar `Run All` and `Run Selected` actions on the Sources page.
- Add row selection support for selected-source batch runs.
- Treat Healthy sources as eligible for batch execution; skip Unhealthy, inactive, deleted, or otherwise ineligible sources.
- Make `Run All` target all Healthy system sources, ignoring current table filters, search, sorting, pagination, and visible rows.
- Make `Run Selected` target selected rows according to the existing table selection model.
- Require confirmation before any batch execution starts, including eligible and skipped counts.
- Execute batch runs through a queue with no more than 5 active source runs at a time.
- Attempt each eligible source up to 3 total attempts with short retry backoff.
- Continue the batch when an individual source fails after max attempts.
- Display global batch progress/status on the Sources page while running.
- Display an in-session completion summary with aggregate successes, failures, skipped sources, per-source results, and attempts used.
- Refresh row actions as compact accessible icon buttons/links where appropriate.
- Preserve visually destructive styling for delete actions.

Out of scope:
- Persisted batch run history or a new source batch run table.
- Scheduling, recurring batch runs, cancellation, pause, resume, retry-failed controls, priority controls, or notifications.
- Cross-page selection unless already supported by the existing table selection model.
- Changing source health calculation, adding new health statuses, or changing source execution semantics beyond batch orchestration, retry, and concurrency handling.
- Changing row-level `Run now` behavior except as needed for the refreshed action layout.

## 5. Implementation Notes
- Add backend batch APIs:
  - `POST /sources/batch-runs/preview`
  - `POST /sources/batch-runs`
  - `GET /sources/batch-runs/{batch_id}`
- Use a preview snapshot with a short-lived `preview_id` so eligibility is frozen between confirmation and execution start.
- Use an in-memory preview and batch state registry with TTL cleanup; no database migration is expected.
- Execute each source through the existing `IngestionOrchestrator.run_source(...)` path and persist normal `SourceRun` rows for each attempt.
- Use `trigger_type="batch_manual"` for batch attempts.
- Enforce fixed execution limits from the planning artifacts: max concurrency 5 and max 3 total attempts per eligible source.
- Treat `success` and `partial_success` as successful terminal source results.
- Avoid reusing request-scoped SQLAlchemy sessions in background workers; background execution must open independent sessions.
- Batch start must use the same job preference contract as existing individual source runs.
- UI should add toolbar actions, row checkboxes, confirmation modal, progress/status panel, completion summary, duplicate-start prevention, and accessible compact row actions.
- `Run Selected` may use client-side health state for immediate enablement, but backend preview remains authoritative.

## 6. QA Section
QA coverage must verify:
- All acceptance criteria in the Product Spec are covered.
- `Run All` ignores filters/search/sort/pagination and runs all eligible Healthy system sources only.
- `Run All` and `Run Selected` confirmation dialogs show accurate eligible and skipped counts before execution.
- Canceling or dismissing confirmation starts no source runs.
- `Run Selected` is disabled when no Healthy selected source exists and enabled when at least one selected Healthy source exists.
- Selected Unhealthy/ineligible sources are skipped and included in confirmation and completion summaries.
- Batch execution never exceeds 5 concurrent active source runs.
- Each eligible source receives no more than 3 total attempts, and retries stop after success.
- Failed sources do not stop remaining source execution.
- Progress/status feedback is visible and updates while the batch is running.
- Completion summary includes aggregate counts, per-source results, attempts used, skipped sources, and reasons/errors where available.
- Duplicate batch starts are prevented while another batch is starting or running.
- Compact row actions have accessible names/tooltips and keyboard support.
- Delete action remains visually destructive.
- Existing single-source `Run now`, source listing, search/filter/sort/pagination, open/edit/delete, health display, and last-run behavior do not regress.

Expected test layers include backend unit/service tests, API tests, integration tests, UI tests, accessibility checks, and regression tests as described in `docs/qa/sources_batch_run_controls_test_plan.md`.

## 7. Risks / Open Questions
- In-memory preview and batch state will be lost on process restart; persisted batch history is intentionally out of scope.
- In-process background execution may not be suitable for future multi-worker or distributed deployments without durable queue support.
- Frozen preview eligibility can diverge from source state before execution; deleted/inactive/unavailable sources must be reported clearly in the summary.
- Existing job preference requirements for source runs must be preserved for batch start requests.
- UI/browser automation conventions may require adaptation if no established browser test harness exists.
- Cross-page selection is out of scope unless already supported, so selected batch behavior should be clearly limited to the current table selection model.

## 8. Definition of Done
- Sources page renders top-toolbar `Run All` and `Run Selected` controls.
- Sources table supports row selection for selected-source batch runs.
- `Run All` previews and executes all Healthy system sources independent of current table state.
- `Run Selected` previews and executes only selected Healthy sources while reporting skipped selected sources.
- Confirmation is required before execution and accurately displays eligible/skipped counts.
- Cancel/dismiss confirmation starts no runs.
- Batch execution enforces max concurrency 5 and max 3 total attempts per eligible source.
- Individual source failures do not stop remaining batch execution.
- Progress/status panel updates while a batch is active.
- Completion summary shows aggregate counts, per-source results, attempts used, skipped sources, and reasons/errors.
- Duplicate batch starts are blocked while a batch is starting or running.
- Compact row actions are accessible and delete remains visually destructive.
- Existing individual source run and source management workflows remain functional.
- Planned unit, API, integration, UI, accessibility, and regression coverage is implemented/executed.
- QA sign-off and HITL validation are completed before any PR/release progression.
