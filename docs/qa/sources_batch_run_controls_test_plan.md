# Test Plan

## 1. Feature Overview

Feature: Sources Batch Run Controls and Action Layout Refresh.

Classification: New Feature.

The feature adds top-toolbar `Run All` and `Run Selected` controls to the Sources page, with Healthy-only eligibility, confirmation before execution, bounded batch execution, retry handling, progress/status feedback, completion summaries, and compact accessible row actions. Existing single-source `Run now`, source listing, source open/edit/delete, health display, and last-run behavior must not regress.

Primary upstream artifacts:
- Product Spec: `docs/product/sources_batch_run_controls_action_layout_refresh_product_spec.md`
- Architecture: `docs/architecture/sources_batch_run_controls_architecture.md`
- UI/UX Spec: `docs/uiux/sources_batch_run_controls_uiux.md`

Implementation under test is expected to include:
- Backend preview/start/status APIs:
  - `POST /sources/batch-runs/preview`
  - `POST /sources/batch-runs`
  - `GET /sources/batch-runs/{batch_id}`
- In-memory preview and batch state registry.
- Batch executor using existing single-source ingestion with max concurrency 5, max 3 total attempts per source, and 1s/2s retry backoff.
- Sources page toolbar, selection checkboxes, confirmation dialog, progress/status panel, completion summary, and compact accessible row actions.

## 2. Test Strategy

Validation will use layered coverage so eligibility, execution semantics, UI state, accessibility, and regressions are independently proven.

1. **Backend unit/service tests** validate eligibility partitioning, preview snapshots, retry algorithm, concurrency enforcement, continuation after failures, status aggregation, and preview/batch registry behavior using controlled fakes.
2. **API tests** validate endpoint contracts, status codes, side effects, malformed requests, duplicate-start prevention, zero-eligible behavior, and source run creation behavior.
3. **Integration tests** validate source listing/table behavior, filters/search independence for `Run All`, selected-row behavior, row actions, source health/last-run effects, and persisted `SourceRun` attempts through existing ingestion paths.
4. **UI tests** validate toolbar, selection, confirmation, cancel/confirm, progress rendering, completion summary rendering, row action layout, and single-source `Run now` preservation.
5. **Accessibility tests** validate keyboard operation, focus management, dialog semantics, ARIA/live-region/progressbar semantics, accessible names/tooltips, and destructive delete styling.
6. **Regression tests** protect existing Sources page behavior: list/search/filter/pagination/sort, open/edit/delete, health display, and row-level `Run now`.

Testing should use deterministic fake/stub source adapters or orchestrator doubles to force success, partial success, repeated failure, eventual success, slow-running tasks, network/exception failures, and unavailable sources.

## 3. Environment and Data Setup

### 3.1 Required Environment

- Local test environment for FastAPI/SQLAlchemy application.
- `pytest` test runner with existing repository fixtures.
- `fastapi.testclient.TestClient` or equivalent API test client.
- UI/browser automation tool already used by the repository, if present; otherwise add implementation-ready UI tests under `tests/ui/` using the established project convention.
- Accessibility checks with automated assertions where possible, supplemented by keyboard/focus assertions.

### 3.2 Controlled Data Sets

Create factory/fixture data for sources with stable names and states:

| Fixture | Count / State | Purpose |
|---|---:|---|
| `healthy_10_unhealthy_3_filtered_visible_2` | 10 Healthy, 3 Unhealthy; UI filter/search shows only 2 Healthy | Proves `Run All` ignores filters/search/visible rows. |
| `healthy_7_unhealthy_2` | 7 Healthy, 2 Unhealthy | Proves `Run All` confirmation counts. |
| `selected_3_healthy_2_unhealthy` | 5 selected mixed sources | Proves `Run Selected` executes only Healthy selected sources and reports skipped. |
| `selected_4_healthy_1_unhealthy` | 5 selected mixed sources | Proves selected confirmation counts. |
| `eligible_12` | 12 Healthy | Proves max concurrency of 5 and queue drain. |
| `zero_healthy` | 0 Healthy, N Unhealthy/inactive/deleted as applicable | Proves zero-eligible handling and no execution. |
| `retry_matrix` | Sources configured as success-on-1, fail-then-success-on-2, fail-all-3, partial_success | Proves retry/attempt and summary semantics. |
| `unavailable_after_preview` | Healthy at preview, deleted/inactive before execution | Proves frozen preview plus unavailable-source summary behavior. |

### 3.3 Execution Instrumentation

Backend execution tests must collect:
- Attempt start/end timestamps per source.
- Maximum simultaneous active source runs.
- Attempts used per source.
- `SourceRun` row IDs/statuses/trigger types.
- Batch status payloads before, during, and after execution.
- Error messages for forced failures.

UI tests should use stable DOM hooks if implemented, such as:
- `data-testid="source-batch-toolbar"`
- `data-testid="run-all-button"`
- `data-testid="run-selected-button"`
- `data-testid="batch-confirmation-dialog"`
- `data-testid="batch-progress-panel"`
- `data-testid="batch-completion-summary"`
- `data-testid="source-row-checkbox"`
- `data-testid="source-row-action-*"`

## 4. Acceptance Criteria Mapping

| AC | Requirement | Planned Coverage |
|---|---|---|
| AC-1 | `Run All` ignores filters and runs all Healthy sources. | API preview/start tests with active filters/search/pagination in UI; integration asserts all Healthy system sources are eligible/executed and Unhealthy skipped. |
| AC-2 | `Run All` confirmation shows eligible/skipped counts. | UI confirmation rendering test and API preview response test for 7 Healthy / 2 Unhealthy. |
| AC-3 | Canceling `Run All` prevents execution. | UI test asserts cancel/dismiss does not call start API and no `SourceRun` rows are created. |
| AC-4 | `Run Selected` disabled with no Healthy selected sources. | UI selection-state tests for no selection and only Unhealthy selected. |
| AC-5 | `Run Selected` enabled with at least one Healthy selected. | UI selection-state test with mixed Healthy/Unhealthy selected. |
| AC-6 | `Run Selected` skips selected Unhealthy sources. | API and UI/integration tests with 3 Healthy + 2 Unhealthy selected; assert only Healthy executed and skipped appear in summary. |
| AC-7 | `Run Selected` confirmation shows selected eligible/skipped counts. | UI/API preview tests with 4 Healthy + 1 Unhealthy selected. |
| AC-8 | Batch concurrency limited to 5 active source runs. | Service-level controlled slow-task test asserts max active count never exceeds 5 for 12 eligible sources. |
| AC-9 | Batch continues after a source fails. | Service/API test with one source failing all attempts and remaining sources completing. |
| AC-10 | Each source receives no more than 3 total attempts. | Retry matrix test asserts exactly 3 attempts for persistent failure and no fourth attempt. |
| AC-11 | Source succeeds before max attempts. | Retry matrix test asserts fail-on-1/success-on-2 reports success with 2 attempts and no third attempt. |
| AC-12 | Progress visible during execution. | UI/status polling test asserts progress panel and aggregate counts update while batch is running. |
| AC-13 | Completion summary includes aggregate counts. | UI/status API test asserts successes, failures, skipped counts. |
| AC-14 | Completion summary includes per-source details. | UI/API test asserts per-source result, attempts used, skipped status/reason. |
| AC-15 | Duplicate batch start prevented while running. | API 409 test and UI disabled-controls test during starting/running states. |
| AC-16 | Icon row actions are accessible. | Accessibility/UI test asserts accessible names/tooltips and keyboard focus for Open/Edit/Run now/Delete. |
| AC-17 | Delete remains visually destructive. | UI/CSS assertion and visual/state test for danger class or equivalent destructive styling. |

## 5. Functional Test Cases

### 5.1 `Run All` Eligibility and Confirmation

1. **Run All ignores active table state**
   - Input: 10 Healthy + 3 Unhealthy; table filtered/searched so only 2 Healthy visible.
   - Steps: Apply filter/search/sort/pagination; click `Run All`; confirm.
   - Expected: Preview reports 10 eligible, 3 skipped; execution attempts all 10 Healthy sources only; no Unhealthy source is attempted.

2. **Run All confirmation count accuracy**
   - Input: 7 Healthy + 2 Unhealthy.
   - Steps: Click `Run All`.
   - Expected: Confirmation appears before start; displays `Eligible to run: 7` and `Skipped: 2`; no `SourceRun` exists before confirmation.

3. **Run All cancellation and dismissal**
   - Input: Any non-zero eligible set.
   - Steps: Open confirmation; cancel, close, and Escape-dismiss in separate cases.
   - Expected: Dialog closes; focus returns to `Run All`; no start API call; no source run starts.

4. **Run All zero eligible**
   - Input: 0 Healthy, multiple Unhealthy/inactive sources.
   - Steps: Click `Run All`.
   - Expected: Confirmation communicates 0 eligible and skipped count; no execution start action is available or start returns completed without execution; no `SourceRun` rows created.

### 5.2 `Run Selected` Eligibility and Confirmation

1. **Run Selected disabled with no selected rows**
   - Input: Any source list.
   - Expected: `Run Selected` is disabled and communicates selection requirement.

2. **Run Selected disabled with only Unhealthy selected rows**
   - Input: Selected rows all non-Healthy.
   - Expected: Button remains disabled; no preview request can be initiated.

3. **Run Selected enabled with mixed selected rows**
   - Input: One Healthy + one Unhealthy selected.
   - Expected: Button enabled because at least one selected source is Healthy.

4. **Run Selected executes selected Healthy only**
   - Input: 3 selected Healthy + 2 selected Unhealthy.
   - Steps: Click `Run Selected`; confirm.
   - Expected: Only 3 Healthy selected source IDs are executed; 2 selected Unhealthy sources are skipped and appear in completion summary.

5. **Run Selected confirmation count accuracy**
   - Input: 4 selected Healthy + 1 selected Unhealthy.
   - Expected: Confirmation shows selected count 5, eligible 4, skipped 1 before execution starts.

6. **Selected duplicate IDs are de-duplicated**
   - Input: Preview request with repeated selected source IDs.
   - Expected: Backend de-duplicates while preserving first-seen order; attempts are not duplicated.

### 5.3 Batch Execution, Retry, and Status

1. **Concurrency limit of 5**
   - Input: 12 eligible sources with blocking fake runs.
   - Expected: Observed max active source tasks is 5; remaining sources stay pending/queued until slots free.

2. **Fewer than 5 eligible sources**
   - Input: 1, 4, and exactly 5 eligible sources in separate cases.
   - Expected: No extra executions; max active count never exceeds eligible count or 5.

3. **Persistent failure does not stop batch**
   - Input: Multiple sources where one fails all 3 attempts.
   - Expected: Failed source is marked failed after retries; all remaining eligible sources are attempted according to queue.

4. **Retry stops after success**
   - Input: Source fails attempt 1 and succeeds on attempt 2.
   - Expected: Result is success with `attempts_used = 2`; no third attempt.

5. **Retry cap**
   - Input: Source fails repeatedly.
   - Expected: Exactly 3 total attempts; failed summary with attempts used 3; no fourth source run.

6. **Short backoff applied**
   - Input: Controlled retry source.
   - Expected: Backoff occurs after failed attempt 1 and failed attempt 2 only; use fake clock or monkeypatch sleep to avoid slow tests and assert requested delays of 1s/2s if implementation follows architecture.

7. **Partial success counts as success**
   - Input: Orchestrator returns `partial_success`.
   - Expected: Source result contributes to success count and no retry occurs.

8. **Source unavailable after preview**
   - Input: Healthy at preview, deleted/inactive before execution.
   - Expected: Source is reported failed or skipped per backend response with reason; batch continues.

### 5.4 Progress and Completion Summary

1. **Progress appears after confirmed start**
   - Expected: Global status panel is shown with mode, completed/eligible, running, pending, success, failure, skipped counts.

2. **Progress updates during polling**
   - Input: Mock status sequence: starting -> running -> running with increased completed count -> terminal.
   - Expected: UI updates counts and progressbar values; polling stops at terminal status.

3. **Completion summary aggregate counts**
   - Input: Terminal batch with 8 successes, 2 failures, 3 skipped.
   - Expected: Summary displays exactly those aggregate counts.

4. **Completion summary per-source details**
   - Expected: Each executed source shows result and attempts used as `{n} of 3`; skipped sources show skipped status and reason; failures show last error/reason.

5. **Dismiss summary**
   - Expected: Dismiss hides current in-session summary only; no persisted history is promised.

## 6. API and Service Test Cases

Recommended files:
- `tests/unit/test_source_batch_runs.py`
- `tests/api/test_source_batch_run_api.py`
- `tests/integration/test_sources_batch_run_html.py`

### 6.1 Preview API

1. `POST /sources/batch-runs/preview` with `mode=all` returns all non-deleted system sources partitioned into eligible/skipped and ignores supplied source IDs/filter-like inputs.
2. `mode=selected` requires non-empty integer `source_ids`.
3. Selected preview handles Healthy, Unhealthy, inactive, deleted, and missing IDs as eligible/skipped according to architecture.
4. Invalid mode returns `400` or validation error per implementation contract.
5. Preview creates no `SourceRun` rows and starts no ingestion.

### 6.2 Start API

1. Valid preview with eligible sources returns `202 Accepted`, `batch_id`, `status=starting`, counts, and `poll_url`.
2. Zero eligible preview returns completed response without scheduling execution or creating `SourceRun` rows.
3. Missing/unknown preview returns `404`; expired preview returns `410` if implemented as specified.
4. Invalid/missing job preferences returns `400`/`422` and does not consume/start batch.
5. Starting the same consumed preview twice fails and creates no duplicate batch.
6. Starting a second batch while one is `starting` or `running` returns `409 Conflict`.
7. Batch attempts use existing ingestion path with `trigger_type="batch_manual"`.

### 6.3 Status API

1. Known active batch returns aggregate counts, source results, skipped sources, timestamps, and null/non-null error fields as appropriate.
2. Terminal completed batch returns stable aggregate and per-source summary.
3. Unknown/expired batch ID returns `404`.
4. Polling status is side-effect free.

### 6.4 Service/Registry

1. Preview eligibility freezes source IDs and skipped details at preview time.
2. Health-only changes after preview do not alter frozen eligible set; deleted/inactive changes before execution are reported as unavailable.
3. Registry updates are thread-safe under concurrent source task completion.
4. TTL cleanup removes expired previews/batches without breaking active batches.
5. Batch-level orchestration exception marks batch failed where possible and exposes error details without leaking raw preferences or payloads.

## 7. UI and Accessibility Test Cases

Recommended file:
- `tests/ui/test_sources_batch_run_controls_ui.py`

### 7.1 Toolbar and Selection UI

1. Toolbar renders `Run All` and `Run Selected` inside the Source inventory table/card area.
2. `Run Selected` enablement updates when row checkboxes are toggled by mouse and Space key.
3. Header select-all selects/deselects visible rows only and supports checked/unchecked/indeterminate states.
4. Selection count text updates accurately.
5. Batch buttons are disabled during preview loading, start pending, and active batch execution.

### 7.2 Confirmation Dialog

1. Dialog uses `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `aria-describedby`.
2. Focus moves into dialog on open and is trapped while open.
3. Escape and Cancel close dialog and return focus to the initiating button.
4. `Run All` dialog copy states filters/search/sort/pagination do not limit the run.
5. Zero-eligible dialog shows `No sources are eligible to run` and no active start control.

### 7.3 Progress and Announcements

1. Progress panel uses `role="status"` or `aria-live="polite"`.
2. Progressbar uses native `<progress>` or valid `role="progressbar"` with min/max/now when eligible count is greater than 0.
3. Aggregate progress text is rendered as text, not visual badges only.
4. Blocking start/preview/status errors use `role="alert"`.
5. Polling failure shows `Unable to refresh batch status. Retrying…` and continues polling unless terminal/unknown failure occurs.

### 7.4 Row Action Layout

1. Open, Edit source, Run now, and Delete source are compact icon buttons/links with keyboard focus rings.
2. Icon-only actions expose accessible names, e.g. `Open Acme source`, `Edit Acme source`, `Run Acme now`, `Delete Acme source`.
3. Tooltips appear on hover and keyboard focus, but are not the only accessible name.
4. Delete action retains danger/destructive visual treatment distinct from neutral actions and is not conveyed by color alone.
5. Row-level `Run now` remains single-source and does not open batch confirmation.

## 8. Regression Test Cases

1. Sources list renders all expected active/non-deleted sources with existing columns intact.
2. Source search/filter/sort/pagination behavior remains unchanged outside `Run All` eligibility.
3. Source health display still shows correct Healthy/Unhealthy states and badges.
4. Source `last_run_at` and `last_run_status` update after single-source `Run now` and after applicable batch attempts if existing behavior updates those fields.
5. Open source action navigates to the existing source detail/URL.
6. Edit source action opens existing edit flow and saves changes without layout regression.
7. Delete source action follows existing confirmation/delete route and danger styling.
8. Existing individual `POST /sources/{source_id}/run` behavior remains available, preference validation still works, and trigger type/semantics are not changed by batch orchestration.
9. Existing CSV import/add-source/page-level actions remain visible and functional.
10. Sources page empty state remains understandable; select-all and `Run Selected` disabled when no rows exist.

## 9. Negative and Edge Cases

1. No Healthy sources exist for `Run All`: no execution starts; skipped sources appear in zero-eligible summary/confirmation.
2. All selected sources are Unhealthy: `Run Selected` disabled.
3. Selected source ID is missing/deleted/inactive by preview time: preview returns skipped with reason where possible.
4. Preview expires before start: start fails; UI asks user to prepare batch again.
5. Backend returns `409 Conflict` because another batch is active: UI shows active-batch error and prevents duplicate start.
6. Start API network failure: no ambiguous success messaging; user can retry if safe and preview remains valid.
7. Status API transient failure: UI displays retrying message and continues polling.
8. Status API `404`: UI stops polling, reports status unavailable, and re-enables actions.
9. A source adapter raises an uncaught exception: source attempt is recorded failed/retried; batch continues.
10. Source fails all retries: summary shows `Failed after retries`, 3 attempts used, and last error.
11. Source succeeds after retry: summary shows success and actual attempts used.
12. Active table filters/search/pagination are present during `Run All`: execution still targets all system Healthy sources.
13. Paginated table with selected rows: `Run Selected` only uses the existing selection model; no new cross-page selection is assumed.
14. Completion summary dismissed/page refreshed/navigated away: persisted summary history is not required.
15. Raw job preferences, adapter payloads, or job descriptions are not leaked in logs or API error summaries.

## 10. Automation Recommendations

Prioritize automation in this order:

1. **Service/unit automation** for eligibility, retry, continuation after failure, and max concurrency. These are critical and most deterministic with fakes.
2. **API automation** for preview/start/status contracts, zero eligible, duplicate start, invalid input, and status summary shape.
3. **UI automation** for toolbar/selection/confirmation/progress/summary flows using mocked API responses where full background execution would be slow or flaky.
4. **Accessibility automation** for semantic assertions plus keyboard traversal/focus management checks.
5. **Regression automation** for source list and row actions, especially single-source `Run now`.

Avoid slow real-time retry sleeps in automated tests. Monkeypatch or fake sleep/backoff while asserting intended backoff durations. Use controlled barriers/events to test concurrency rather than relying on timing alone.

## 11. Evidence Required During Execution

When this plan is executed, collect and attach to the QA report:

- Test command(s) executed.
- Full pass/fail output.
- API request/response samples for preview, start, and terminal status.
- Concurrency measurement evidence showing max active source runs.
- Retry attempt logs/source run records proving max 3 attempts and eventual-success behavior.
- UI screenshots or DOM snapshots for confirmation, progress, completion summary, and row actions where applicable.
- Accessibility assertion output and any manual keyboard/focus observations.
- Failure logs, stack traces, and classification for any failing test.

## 12. Sign-Off Criteria

QA sign-off is not part of this planning task. Future approval may be granted only if all of the following are true:

- All critical Functional, API/service, UI, accessibility, and regression tests pass.
- Concurrency is proven not to exceed 5 active source runs per batch.
- Retry behavior is proven to cap at 3 total attempts per eligible source.
- Failed sources are proven not to block remaining batch execution.
- Confirmation cancellation and zero-eligible paths are proven to start no executions.
- Completion summary is proven to include aggregate counts, per-source results, attempts used, and skipped reasons.
- Existing single-source `Run now`, open/edit/delete, listing, health display, and last-run behavior do not regress.
- No unresolved blocking or major defects remain.
- Evidence in `docs/qa/sources_batch_run_controls_test_report.md` supports the result.
