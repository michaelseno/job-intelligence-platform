# Technical Design

## 1. Feature Overview

Add batch run controls to the existing Sources page so users can run all eligible sources or selected eligible sources with confirmation, live progress, bounded concurrency, retries, and an in-session completion summary. Also refresh the Sources table action layout with toolbar-level batch actions and compact accessible row action buttons.

This design uses the existing single-source ingestion path internally and adds a lightweight backend batch orchestration layer. No persisted batch history or database schema migration is required for the current scope.

## 2. Product Requirements Summary

- `Run All` targets all system sources, ignoring table filters/search/sort/pagination, and executes only Healthy eligible sources.
- `Run Selected` uses the current table selection model and is enabled only when at least one selected source is Healthy.
- Non-Healthy or otherwise ineligible sources are skipped and shown in confirmation and completion summaries.
- Confirmation is required before any batch execution starts.
- Batch execution is queued with a maximum of 5 concurrently executing source runs per batch.
- Each eligible source receives up to 3 total attempts, with short backoff between failed attempts.
- A failed source does not stop remaining sources.
- Sources page displays global progress while running and a completion summary after completion.
- Completion summary includes aggregate successes/failures/skipped and per-source result/attempt count.
- Row actions may become compact icon buttons but must remain accessible; delete remains visually destructive.

## 3. Requirement-to-Architecture Mapping

| Requirement | Architecture responsibility |
| --- | --- |
| `Run All` ignores current table state | Backend preview endpoint queries all non-deleted sources directly, not the rendered table or query params. |
| Healthy-only eligibility | Backend batch preview freezes eligibility using `Source.health_state == "healthy"`, plus existing run eligibility (`deleted_at IS NULL`, `is_active = true`). |
| Confirmation counts | Preview endpoint returns eligible and skipped counts/details before execution. |
| Consistent eligibility after confirmation | Preview creates a short-lived `preview_id` snapshot; start endpoint runs the frozen eligible source IDs and carries frozen skipped details into the batch summary. |
| Max concurrency 5 | Backend batch worker uses a fixed concurrency limit of 5. |
| 3 attempts and backoff | Batch orchestration wraps the existing ingestion call with per-source retry state and 1s/2s backoff. |
| Continue after failure | Per-source failures are captured into result records; queue continues until all eligible source tasks reach terminal state. |
| Progress/status | Start endpoint returns `batch_id`; UI polls status endpoint for aggregate and per-source state. |
| Completion summary not persisted | Batch state is stored in process memory with TTL cleanup; existing `source_runs` rows remain the only persisted per-attempt records. |
| Action layout refresh | Sources template and JS add toolbar actions, row selection, compact icon buttons, labels/tooltips, destructive delete styling. |

## 4. Technical Scope

### Current Technical Scope

- Backend preview/start/status API for batch source runs.
- In-process batch state registry for active/recent batch progress and completion summary.
- Batch orchestration service that calls `IngestionOrchestrator.run_source(...)` for each attempt.
- Retry/backoff and concurrency semantics fixed by this design.
- Pydantic request/response schemas for preview, start, status, and result payloads.
- Sources page template, static JS, and CSS updates for toolbar actions, selection, confirmation, progress, summary, and accessible compact row actions.
- Tests for API contracts, orchestration behavior, and UI accessibility/summary rendering hooks.

### Out of Scope

- Persisted batch run history or a new `source_batch_runs` table.
- Cancellation, pause, resume, retry-failed, scheduling, priority, or notifications.
- Cross-page selection unless existing table behavior already supports it. Current Sources page is server-rendered and does not currently provide cross-page selection.
- Changes to source health calculation or new health statuses.
- Changing row-level single-source `Run now` semantics except visual/action layout integration.

### Future Technical Considerations

- Durable queue or scheduler-backed batch processing.
- Persisted batch audit table with correlation to `source_runs`.
- Cross-page/saved-view selected source batches.
- Batch cancellation and retry-failed controls.
- User-configurable concurrency/backoff/retry settings.

## 5. Architecture Overview

### Existing-System Findings

- Backend stack is FastAPI + SQLAlchemy with server-rendered Jinja templates and small static JS/CSS assets.
- Source management routes live in `app/web/routes.py`.
- Sources page template is `app/templates/sources/index.html`.
- Static JS is centralized in `app/static/js/app.js`; static CSS is `app/static/css/app.css`.
- Source persistence model is `app.persistence.models.Source` with relevant fields:
  - `is_active`
  - `deleted_at`
  - `health_state`
  - `last_run_status`
  - `last_run_at`
- Individual source run endpoint is `POST /sources/{source_id}/run`.
- Individual run logic is `IngestionOrchestrator.run_source(source, preferences, trigger_type="manual")` in `app/domain/ingestion.py`.
- `run_source(...)` creates a persisted `SourceRun` row per invocation, catches ingestion exceptions, updates source health, commits, and returns a terminal `SourceRun` with status such as `success`, `partial_success`, or `failed`.
- Existing run endpoint requires job preferences from JSON or form/local-storage injection. Batch runs must use the same preference contract.
- There is no existing durable task queue. FastAPI `BackgroundTasks` is already used for source delete cleanup; for this feature, an in-process batch registry is acceptable because persisted summary history is out of scope.

### Proposed Design

Add a new backend module, `app/domain/source_batch_runs.py`, containing:

- `SourceBatchRunService`: validates preview/start requests, freezes source eligibility, owns active/recent batch registry access.
- `SourceBatchExecutor`: executes one batch in the background with max concurrency 5 and retry/backoff per source.
- In-memory `SourceBatchRunRegistry`: stores preview snapshots and batch states/results with TTL cleanup.

Add three JSON API endpoints in `app/web/routes.py`:

1. `POST /sources/batch-runs/preview` — compute/freeze eligible and skipped sources for confirmation.
2. `POST /sources/batch-runs` — start a background batch from a confirmed preview.
3. `GET /sources/batch-runs/{batch_id}` — return current progress or final summary.

The frontend calls preview, shows confirmation, starts the batch, then polls status until terminal completion.

## 6. System Components

### Backend Components

- `app/domain/source_batch_runs.py` **(new)**
  - Batch preview creation.
  - Eligibility evaluation.
  - In-memory preview and batch state registry.
  - Background batch execution.
  - Retry/backoff/concurrency enforcement.
  - Summary/result construction.
- `app/web/routes.py` **(update)**
  - Add preview/start/status endpoints.
  - Schedule background execution using `BackgroundTasks`.
  - Avoid reusing request-scoped SQLAlchemy sessions in background workers.
- `app/schemas.py` **(update)**
  - Add request/response schemas for source batch run APIs.
- `app/persistence/db.py` **(used)**
  - Background workers must open independent sessions via existing session factory/session helper.
- `app/domain/ingestion.py` **(used, minimal/no change)**
  - Existing `IngestionOrchestrator.run_source(...)` remains the single source execution implementation.
  - Batch attempts pass `trigger_type="batch_manual"` to distinguish persisted attempt rows from row-level manual runs.

### Frontend Components

- `app/templates/sources/index.html` **(update)**
  - Add toolbar with `Run All` and `Run Selected`.
  - Add row selection checkboxes.
  - Add containers/dialog markup hooks for confirmation, global progress, and completion summary.
  - Change row actions to compact icon buttons/links with accessible names/tooltips.
- `app/static/js/app.js` **(update)**
  - Source page batch controller.
  - Selection state and `Run Selected` enablement.
  - Preview/start/status polling.
  - Confirmation and summary rendering.
  - Duplicate-start prevention while status is `starting` or `running`.
- `app/static/css/app.css` **(update)**
  - Toolbar, compact icon button, progress panel, summary table/list, selected-row, and destructive action styling.

## 7. Data Models

No database migration is required.

### Existing Entity: Source

#### Purpose

Represents a configured job ingestion source.

#### Fields Used

- `id: int` — source identifier.
- `name: str` — display name for confirmation/progress/summary.
- `is_active: bool` — must be true for batch eligibility.
- `deleted_at: datetime | None` — must be null for batch eligibility.
- `health_state: str` — must equal `"healthy"` for batch eligibility.

#### Ownership Model

The current application has no explicit multi-user authorization model; sources are system-wide.

### Existing Entity: SourceRun

#### Purpose

Persists each individual ingestion attempt.

#### Batch Usage

Each batch attempt creates one normal `source_runs` row through `IngestionOrchestrator.run_source(...)`.

- `trigger_type = "batch_manual"` for batch attempts.
- `status` is interpreted as:
  - success terminal: `success`, `partial_success`
  - failure attempt: `failed`
- A source that fails all 3 attempts will have up to 3 failed `SourceRun` rows.

### In-Memory State: BatchPreview

#### Purpose

Freezes eligibility between confirmation and execution start.

#### Primary Key

`preview_id: string` generated UUID.

#### Fields

- `preview_id: string`
- `mode: "all" | "selected"`
- `eligible_sources: list[SourceBatchSourceRef]`
- `skipped_sources: list[SourceBatchSkippedSource]`
- `created_at: datetime`
- `expires_at: datetime` — recommended 10 minutes after creation.

#### Lifecycle

Created by preview endpoint. Consumed by start endpoint. Expired previews return `410 Gone` or `404 Not Found`.

### In-Memory State: SourceBatchRun

#### Purpose

Tracks progress and completion summary for the current page session without persisted history.

#### Primary Key

`batch_id: string` generated UUID.

#### Fields

- `batch_id: string`
- `mode: "all" | "selected"`
- `status: "starting" | "running" | "completed" | "completed_with_failures" | "failed"`
- `created_at: datetime`
- `started_at: datetime | null`
- `finished_at: datetime | null`
- `eligible_count: int`
- `skipped_count: int`
- `success_count: int`
- `failure_count: int`
- `pending_count: int`
- `running_count: int`
- `completed_count: int`
- `source_results: list[SourceBatchSourceResult]`
- `skipped_sources: list[SourceBatchSkippedSource]`
- `error_message: string | null` — only for batch-level orchestration failure.

#### Lifecycle

Created on start. Updated by background executor. Retained in memory for a short TTL after completion, recommended 30 minutes. Removed on process restart or TTL cleanup.

## 8. API Contracts

### Endpoint: `POST /sources/batch-runs/preview`

#### Purpose

Compute and freeze eligible/skipped source counts/details before confirmation.

#### Authentication / Authorization

Follow existing Sources route access behavior. The current application has no explicit auth layer. Future auth should require the same permission as running an individual source.

#### Request Body

```json
{
  "mode": "all",
  "source_ids": null
}
```

For selected runs:

```json
{
  "mode": "selected",
  "source_ids": [1, 2, 3]
}
```

#### Response Body

```json
{
  "preview_id": "uuid",
  "mode": "selected",
  "eligible_count": 2,
  "skipped_count": 1,
  "eligible_sources": [
    {"source_id": 1, "source_name": "Acme", "health_state": "healthy"}
  ],
  "skipped_sources": [
    {"source_id": 3, "source_name": "Beta", "health_state": "error", "reason": "Source health is error."}
  ],
  "expires_at": "2026-04-28T12:10:00Z"
}
```

#### Success Status Codes

- `200 OK`

#### Error Status Codes

- `400 Bad Request` — invalid mode or malformed request.
- `422 Unprocessable Entity` — invalid field types.

#### Validation Rules

- `mode` must be `all` or `selected`.
- For `selected`, `source_ids` is required and must contain at least one integer.
- For `all`, `source_ids` must be ignored if provided; backend queries all non-deleted sources.
- Duplicate selected IDs should be de-duplicated while preserving first-seen order for display.
- Deleted or missing selected IDs are represented as skipped with `reason` where possible, not fatal errors.

#### Side Effects

- Creates an in-memory preview snapshot only.
- No source runs start from this endpoint.

#### Idempotency / Duplicate Handling

Repeated previews create independent snapshots. This is acceptable because no ingestion side effects occur.

### Endpoint: `POST /sources/batch-runs`

#### Purpose

Start a confirmed batch run from a preview snapshot.

#### Authentication / Authorization

Same as individual source run.

#### Request Body

```json
{
  "preview_id": "uuid",
  "job_preferences": {
    "schema_version": 1,
    "role_positives": {},
    "role_negatives": [],
    "remote_positives": [],
    "location_positives": [],
    "location_negatives": [],
    "sponsorship_supported": [],
    "sponsorship_unsupported": [],
    "sponsorship_ambiguous": []
  }
}
```

#### Response Body

```json
{
  "batch_id": "uuid",
  "status": "starting",
  "mode": "selected",
  "eligible_count": 2,
  "skipped_count": 1,
  "poll_url": "/sources/batch-runs/uuid"
}
```

If there are zero eligible sources, do not schedule background execution; return a completed summary:

```json
{
  "batch_id": "uuid",
  "status": "completed",
  "mode": "all",
  "eligible_count": 0,
  "skipped_count": 5,
  "poll_url": "/sources/batch-runs/uuid"
}
```

#### Success Status Codes

- `202 Accepted` — batch scheduled.
- `200 OK` — zero eligible sources; completed without execution.

#### Error Status Codes

- `400 Bad Request` — missing/invalid preferences or preview mismatch.
- `404 Not Found` — unknown preview.
- `409 Conflict` — another batch is already starting/running.
- `410 Gone` — preview expired.
- `422 Unprocessable Entity` — schema validation error.

#### Validation Rules

- `preview_id` must reference an unexpired preview.
- `job_preferences` must pass existing `validate_job_filter_preferences(...)` logic.
- Start must consume or invalidate the preview to avoid accidental duplicate starts from double-clicks.

#### Side Effects

- Creates in-memory batch state.
- Schedules background execution for eligible sources.
- Each attempted source writes normal `SourceRun`, `JobPosting`, `JobSourceLink`, classification, and source health updates through existing ingestion logic.

#### Idempotency / Duplicate Handling

- Preview consumption prevents the same `preview_id` from being started twice.
- While any batch has status `starting` or `running`, return `409 Conflict` for a new start. This is intentionally conservative for the current single-user app and satisfies duplicate-start prevention.

### Endpoint: `GET /sources/batch-runs/{batch_id}`

#### Purpose

Return current progress or final summary for a batch.

#### Authentication / Authorization

Same as Sources page access.

#### Response Body

```json
{
  "batch_id": "uuid",
  "mode": "all",
  "status": "running",
  "eligible_count": 12,
  "skipped_count": 3,
  "success_count": 4,
  "failure_count": 1,
  "pending_count": 2,
  "running_count": 5,
  "completed_count": 5,
  "started_at": "2026-04-28T12:00:00Z",
  "finished_at": null,
  "source_results": [
    {
      "source_id": 1,
      "source_name": "Acme",
      "status": "success",
      "attempts_used": 1,
      "source_run_ids": [101],
      "last_error": null
    },
    {
      "source_id": 2,
      "source_name": "Beta",
      "status": "running",
      "attempts_used": 1,
      "source_run_ids": [102],
      "last_error": null
    }
  ],
  "skipped_sources": [
    {"source_id": 9, "source_name": "Old Source", "health_state": "warning", "reason": "Source health is warning."}
  ],
  "error_message": null
}
```

#### Success Status Codes

- `200 OK`

#### Error Status Codes

- `404 Not Found` — unknown or expired batch id.

#### Validation Rules

- `batch_id` must be a known in-memory batch.

#### Side Effects

None.

#### Idempotency / Duplicate Handling

Safe to poll repeatedly.

## 9. Frontend Impact

### Components Affected

- Sources page header/actions: keep `Import CSV` and `Add source`; add table toolbar for batch actions inside source inventory card.
- Source inventory table:
  - Add checkbox column with select-all-visible checkbox.
  - Add `data-source-id`, `data-source-name`, and `data-health-state` hooks per row.
  - Convert row actions to compact buttons/links.
- New batch UI regions:
  - Confirmation dialog or inline modal.
  - Global progress/status panel.
  - Completion summary panel.

### API Integration

Frontend sequence:

1. User clicks `Run All` or enabled `Run Selected`.
2. JS reads job preferences using existing `JobPreferencesStore.read()`.
   - If preferences are missing, redirect to preferences setup using existing behavior.
3. JS calls `POST /sources/batch-runs/preview`.
4. JS displays confirmation with `eligible_count` and `skipped_count`.
5. If user cancels/dismisses, do nothing further.
6. If user confirms, JS calls `POST /sources/batch-runs` with `preview_id` and `job_preferences`.
7. JS disables batch actions and starts polling `poll_url` every 1 second while status is `starting`/`running`.
8. JS renders progress updates.
9. On terminal status, JS renders completion summary and re-enables batch actions.

### UI States

- Idle:
  - `Run All` enabled unless a batch is active.
  - `Run Selected` enabled only when at least one selected row has `health_state == "healthy"` and no batch is active.
- Preview loading:
  - Disable initiating action and show loading indicator.
- Confirmation:
  - Show eligible and skipped counts.
  - If `eligible_count == 0`, confirmation must indicate no source runs will start; confirm button should be disabled or relabeled to close. No execution should start.
- Running:
  - Show aggregate progress: completed/eligible, running, pending, successes, failures, skipped.
  - Show per-source state labels: pending/queued, running, succeeded, failed after retries, skipped.
- Error:
  - Show actionable message for preview/start/status failure.
  - Re-enable actions unless a known active batch is still running.
- Completed:
  - Show aggregate success/failure/skipped counts.
  - Show per-source result and attempts used for executed sources.
  - Show skipped sources with reason.

### Accessibility Requirements

- Toolbar buttons must be keyboard-focusable native buttons.
- Confirmation dialog must be keyboard accessible, focus-trapped if modal, and closable via Escape/cancel.
- Progress region should use `aria-live="polite"` for aggregate updates.
- Completion errors should use `role="alert"` when blocking.
- Icon-only row actions must have visible tooltip and accessible name, for example `aria-label="Open Acme source"`.
- Delete action must retain `btn--danger` or equivalent destructive visual styling.

## 10. Backend Logic

### Responsibilities

- Evaluate eligibility consistently for preview/start.
- Start at most one active batch at a time in the current process.
- Execute eligible sources with max 5 concurrent source tasks.
- Retry each source up to 3 total attempts.
- Capture source-level success/failure/skipped details for polling and final summary.
- Use existing single-source ingestion logic for actual job fetching/classification/persistence.

### Eligibility Rules

A source is eligible for batch execution only when all are true at preview time:

- Source exists.
- `Source.deleted_at is None`.
- `Source.is_active is True`.
- `Source.health_state == "healthy"`.

Skip reasons should be stable and human-readable:

- `not_found`: selected source no longer exists.
- `deleted`: source is deleted.
- `inactive`: source is inactive.
- `unhealthy`: health state is not `healthy`; include actual state.
- `ineligible`: fallback for unexpected validation failure.

For `Run All`, evaluate all non-deleted sources in the system, not the rendered rows. Non-healthy/inactive sources are included as skipped.

### Validation Flow

- Preview validates mode and selected IDs.
- Start validates preview status/expiration and job preferences.
- Executor reloads source by ID before each attempt using a fresh session.
  - If the source disappeared or became inactive/deleted after preview, mark that source `skipped` or `failed` with reason `Source became unavailable before execution.` This handles the product edge case without re-running eligibility for health changes.
  - Do not recheck `health_state` for frozen eligible sources; this preserves preview consistency when health changes between confirmation and execution.

### Business Rules

- `partial_success` from an individual source run counts as a batch success because ingestion completed with warnings and existing row-level run treats it as success for user messaging.
- `failed` counts as failed attempt; retry until success or 3 attempts.
- Batch terminal status:
  - `completed` when all eligible sources succeeded or there were zero eligible sources.
  - `completed_with_failures` when at least one eligible source failed after max attempts or became unavailable.
  - `failed` only for batch-level orchestration failure that prevents normal queue processing.

### Persistence Flow

- No new batch rows are persisted.
- Each attempt calls `IngestionOrchestrator.run_source(source, preferences, trigger_type="batch_manual")`.
- The ingestion orchestrator commits per attempt and updates source health exactly as existing single-source runs do.
- Batch state registry stores only IDs, names, counts, status, run IDs, and error summaries; do not store raw job payloads or preferences beyond what is needed to execute the background task.

### Error Handling

- Individual source attempt exceptions should normally be converted to failed `SourceRun` rows by `IngestionOrchestrator.run_source(...)`.
- If an exception escapes the orchestrator or session setup, capture it as the attempt error, rollback/close that session, and retry according to the same rules.
- If all attempts fail, mark source result `failed` with `attempts_used = 3` and continue.
- If the whole executor crashes, mark batch `failed` when possible and log the exception.

## 11. File Structure

Recommended implementation changes:

```text
app/
  domain/
    source_batch_runs.py      # new preview registry, batch registry, executor/service
    ingestion.py              # use existing run_source; no required semantic change
    sources.py                # optional helper for eligibility queries
  web/
    routes.py                 # add batch preview/start/status endpoints
  schemas.py                  # add batch request/response models
  templates/
    sources/
      index.html              # toolbar, selection, progress/summary hooks, compact row actions
  static/
    js/
      app.js                  # source batch UI controller
    css/
      app.css                 # toolbar/progress/summary/icon styles
  unit/
    test_source_batch_runs.py
  api/
    test_source_batch_run_api.py
  integration/
    test_sources_batch_run_html.py
  ui/
    test_sources_batch_run_controls_ui.py
```

## 12. Security

- Follow existing route access behavior; current app has no explicit auth/session permission model.
- Future auth should require the same permission as individual source run for all batch endpoints.
- Validate all source IDs as integers through Pydantic/FastAPI.
- Do not trust client-side health state for eligibility; backend preview is authoritative.
- Do not accept arbitrary concurrency or retry settings from the client.
- Do not log full `job_preferences`, raw job payloads, job descriptions, or adapter responses.
- Logs and summaries may include source IDs, source names, statuses, attempt counts, run IDs, and concise error messages.
- Row delete action must remain visually destructive and must continue to use existing delete confirmation route.

## 13. Reliability

- In-process background execution is not durable across process crashes/restarts. This is acceptable because persisted batch history is out of scope, but individual completed attempts remain represented by `source_runs`.
- Use fresh DB sessions per concurrently executing source task; never share one SQLAlchemy session across worker threads.
- Recommended execution implementation:
  - One background task owns the batch.
  - A `ThreadPoolExecutor(max_workers=5)` or equivalent bounded worker pool runs source tasks.
  - Each worker opens/closes its own DB session and registry instance.
- Polling interval should default to 1 second. Avoid sub-second polling.
- Backoff is fixed:
  - after failed attempt 1: wait 1 second
  - after failed attempt 2: wait 2 seconds
  - no wait after success or final failed attempt
- A source worker holds its concurrency slot during retry backoff. This keeps the number of in-flight source tasks bounded to 5 and simplifies concurrency validation.
- Add structured logs for:
  - preview created: `preview_id`, mode, eligible/skipped counts
  - batch started: `batch_id`, mode, eligible/skipped counts
  - source attempt started/finished: `batch_id`, `source_id`, `attempt`, `source_run_id`, status
  - source final result
  - batch completed/failed
- Registry updates must be thread-safe, e.g. protected by a `threading.Lock`.
- TTL cleanup should run opportunistically on preview/start/status calls to prevent unbounded in-memory growth.

## 14. Dependencies

- Existing source health data in `Source.health_state`.
- Existing `IngestionOrchestrator.run_source(...)` behavior and adapter registry.
- Existing job preference validation and local-storage frontend preference flow.
- FastAPI `BackgroundTasks` and Python standard library concurrency primitives.
- Existing UI macros/styles for buttons, badges, alerts, and table layout.

## 15. Assumptions

- `Source.health_state == "healthy"` is the authoritative Healthy state for eligibility; all other values are skipped.
- `Source.is_active == false` makes a source otherwise ineligible even if its health state is `healthy`.
- `partial_success` should count as a successful batch source result with warnings because the existing row-level run treats it as successful enough for user messaging.
- A single active batch per application process is acceptable for the current single-user app and satisfies duplicate-start prevention.
- In-memory preview/batch state is sufficient because product explicitly excludes persisted summary history.
- Existing individual source execution can be safely orchestrated in batches as long as each concurrent source uses its own DB session.

## 16. Risks / Open Questions

- **In-process durability:** Active progress is lost on process restart. Mitigation: persisted `source_runs` still show completed attempts; durable history is out of scope.
- **SQLite write contention:** Concurrent ingestion may cause DB locking in local SQLite. Mitigation: limit to 5, independent sessions, short transactions as already used by ingestion. If failures occur, retries may absorb transient lock errors.
- **No global distributed lock:** In multi-process deployment, each process would allow one active batch. Current app appears local/single-process; future production deployment should use DB-backed locks/queue.
- **Preview expiration UX:** If user waits longer than preview TTL, start returns expired and UI must ask user to preview again.
- **Health changes after preview:** Design freezes health eligibility. If source becomes inactive/deleted before attempt, execution cannot proceed and source is reported unavailable; health-only changes are not re-evaluated.
- **Long-running adapter calls:** There is no cancellation in current scope; stuck adapter calls can occupy a worker until existing adapter/network timeouts fire.
- **Exact summary component:** Product did not prescribe modal vs inline panel. This design recommends an inline Sources page panel below the toolbar to satisfy in-session visibility with minimal disruption.

## 17. Implementation Notes

### Backend Handoff

- Implement `source_batch_runs.py` without schema migrations.
- Reuse `validate_job_filter_preferences(...)`; do not duplicate preference schema logic.
- Use `IngestionOrchestrator.run_source(..., trigger_type="batch_manual")` for every attempt.
- Treat run statuses `success` and `partial_success` as source success; treat `failed` as retryable until max attempts.
- Ensure worker sessions are isolated and closed.
- Protect registry state with a lock.
- Return deterministic response fields so frontend and QA can assert progress/summary behavior.
- Add tests with fake/stub adapters to force success, partial success, repeated failure, and eventual success on retry.

### Frontend Handoff

- Add source batch controller guarded by a Sources-page root data attribute so it does not affect other pages.
- Use backend preview response for confirmation counts; do not compute final eligibility in the browser.
- Maintain selected IDs from visible rows only unless an existing cross-page selection model is later introduced.
- Disable `Run Selected` unless a selected row has `data-health-state="healthy"` and no batch is active.
- Disable both batch buttons while preview is loading, start is pending, or a batch is running.
- Render skipped sources in both confirmation and completion summary.
- Keep row-level `Run now` form behavior, including `data-requires-job-preferences-submit="true"`.
- For icon row actions, use text visually hidden or `aria-label` plus `title`; delete keeps `btn--danger`.

### Testing Strategy Hooks

- Unit test eligibility partitioning:
  - healthy active source -> eligible
  - warning/error/unknown -> skipped unhealthy
  - inactive -> skipped inactive
  - deleted/missing selected -> skipped
- Unit test retry algorithm:
  - succeeds first attempt
  - fails once then succeeds
  - fails three times and stops
  - queue continues after one source fails
- Concurrency test with a controlled fake executor to assert no more than 5 active source tasks.
- API tests:
  - `Run All` preview ignores table/query filters because endpoint accepts no filter inputs and queries all sources.
  - selected preview de-duplicates IDs and returns mixed eligible/skipped.
  - start consumes preview and rejects duplicate start.
  - zero eligible start returns completed without creating `SourceRun` rows.
  - status returns required aggregate and per-source fields.
- Integration/UI tests:
  - toolbar buttons render.
  - `Run Selected` disabled/enabled based on selected healthy rows.
  - confirmation cancel makes no start request.
  - progress panel updates from mocked status responses.
  - completion summary includes successes, failures, attempts, skipped.
  - row icon buttons have accessible names/tooltips and delete styling.
