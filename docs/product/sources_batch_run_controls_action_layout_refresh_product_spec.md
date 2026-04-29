# Product Specification

## 1. Feature Overview

Add batch run controls to the Sources page so users can trigger multiple source runs without manually clicking `Run now` for each source. The feature introduces global `Run All` and selection-based `Run Selected` actions, queued execution with limited concurrency, confirmation before execution, global progress feedback, and a completion summary with per-source outcomes.

The feature also refreshes the Sources page action layout by placing batch actions in the top toolbar and allowing row actions to use compact accessible icon buttons while preserving destructive styling for delete actions.

## 2. Problem Statement

Users currently must trigger each source individually from the Sources page. For users with many sources, such as 100 sources, this creates unnecessary repetitive work, increases time to start ingestion, and increases the likelihood of missed sources.

## 3. User Persona / Target User

- Primary user: A platform user or administrator who manages multiple job data sources and needs to refresh source data efficiently.
- Secondary user: A QA or operations user validating source health and ingestion behavior across multiple sources.

## 4. User Stories

- As a source manager, I want to run all healthy sources at once, so that I do not need to trigger each source manually.
- As a source manager, I want to run only selected healthy sources, so that I can refresh a targeted subset of sources.
- As a source manager, I want unhealthy selected sources to be skipped and reported, so that I understand why they were not run.
- As a source manager, I want confirmation before starting a batch run, so that I can verify the number of sources that will run and be skipped.
- As a source manager, I want visible progress during execution, so that I know the batch is active and can monitor completion.
- As a source manager, I want a completion summary with per-source results and attempts used, so that I can identify successes, failures, and skipped sources.

## 5. Goals / Success Criteria

- Users can start a batch run for all healthy sources from the Sources page with one confirmed action.
- Users can select rows and start a batch run for eligible selected sources with one confirmed action.
- Batch execution never starts more than 5 source runs concurrently.
- Each eligible source receives no more than 3 total attempts.
- A failed source does not stop the remaining batch from continuing.
- Users receive clear confirmation, progress, and completion feedback for both `Run All` and `Run Selected` flows.
- Completion feedback includes per-source result, attempts used, aggregate successes, aggregate failures, and skipped sources.
- Row action layout remains accessible, and delete remains visually destructive.

## 6. Feature Scope

### In Scope

- Add a top-toolbar `Run All` action on the Sources page.
- Add row selection support to the Sources table if it is not already present.
- Add a top-toolbar `Run Selected` action on the Sources page.
- Enable `Run Selected` only when at least one selected source is eligible to run.
- Treat Healthy sources as eligible for batch execution.
- Skip Unhealthy or otherwise ineligible sources and include them in confirmation and completion summaries.
- Make `Run All` target all Healthy sources in the system, ignoring current table filters and search.
- Make `Run Selected` target selected rows according to the existing table selection model.
- Require confirmation before starting either batch action.
- Display eligible and skipped counts in the confirmation step.
- Execute batch runs through a queue with a concurrency limit of 5 sources at a time.
- Attempt each eligible source up to 3 total attempts.
- Use short retry backoff between attempts.
- Continue executing the batch when one source fails after max attempts.
- Display global progress/status during batch execution on the Sources page.
- Display a completion summary on the Sources page after completion.
- Include per-source result, attempts used, successes, failures, and skipped sources in the completion summary.
- Allow row actions to be changed to compact icon buttons if accessible labels and/or tooltips are provided.
- Preserve visually destructive styling for delete actions.

### Out of Scope

- Persisted batch run history, unless the existing architecture already persists source run history and the batch summary can use it without adding a new persistence feature.
- `Run Selected` across multiple pages, unless the existing table selection model already supports cross-page selection.
- Changing source health calculation or health state definitions, unless required only to determine eligibility using existing health data.
- Adding new source health statuses.
- Adding scheduling, recurring batch runs, or cron-based execution.
- Adding cancellation, pause, or resume controls for active batch runs.
- Adding priority ordering controls for batch execution.
- Sending batch completion notifications outside the Sources page.
- Changing the individual row-level `Run now` behavior except as needed to fit the refreshed action layout.
- Changing backend source execution semantics beyond batch orchestration, retry handling, and concurrency limiting for this feature.

### Future Considerations

- Persisted batch run history and audit trail.
- Cross-page or saved-view selection for `Run Selected`.
- Batch cancellation, pause, resume, or retry-failed controls.
- User-configurable concurrency and retry settings.
- Exportable batch summaries.
- Notifications for long-running batch completion.

## 7. Functional Requirements

### FR-1: `Run All` Toolbar Action

- The Sources page top toolbar must include a `Run All` action.
- `Run All` must target all sources in the system whose current health status is Healthy.
- `Run All` must ignore active table filters, search terms, sorting, pagination, and visible rows.
- Unhealthy or otherwise ineligible sources must not be executed.
- Skipped sources must be counted before confirmation and listed in the final completion summary.

### FR-2: Row Selection and `Run Selected`

- The Sources table must support row selection.
- The Sources page top toolbar must include a `Run Selected` action.
- `Run Selected` must use the selected rows provided by the table selection model.
- `Run Selected` must be disabled when no selected source is Healthy.
- `Run Selected` must be enabled when at least one selected source is Healthy.
- When selected rows include unhealthy or otherwise ineligible sources, those sources must be skipped and included in confirmation and completion summaries.

### FR-3: Eligibility Rules

- A source is eligible for batch execution only when its current health status is Healthy.
- Sources that are not Healthy must be skipped.
- Eligibility must be evaluated before showing confirmation.
- If source health changes between confirmation and execution start, the system must use a consistent eligibility decision for the batch and report the resulting behavior in the completion summary.

### FR-4: Confirmation Before Execution

- Both `Run All` and `Run Selected` must show a confirmation step before any source run is started.
- The confirmation must include the number of eligible sources that will run.
- The confirmation must include the number of skipped sources.
- The batch must start only after the user confirms.
- If the user cancels or dismisses confirmation, no source runs may be started.

### FR-5: Batch Queue and Concurrency

- Batch execution must use queued or limited-concurrency processing.
- No more than 5 source runs may be actively executing at the same time for a single batch.
- The batch must continue scheduling remaining eligible sources as active runs complete.
- A source failure must not stop execution of other sources in the batch.

### FR-6: Retry Behavior

- Each eligible source must receive up to 3 total attempts.
- The initial run counts as attempt 1.
- A failed attempt may be retried until the source succeeds or reaches 3 total attempts.
- Retries must use a short backoff between attempts.
- A source that fails after 3 total attempts must be marked failed in the completion summary.
- A source that succeeds before 3 attempts must not be retried further.

### FR-7: Progress and Status Feedback

- The Sources page must display global batch progress/status while a batch is running.
- Progress/status must allow the user to distinguish at minimum: pending/queued, running, completed successfully, failed after retries, and skipped sources.
- Progress must update as source runs complete or fail.
- The UI must prevent ambiguous duplicate starts for the same batch action while a batch is already starting or running.

### FR-8: Completion Summary

- After batch completion, the Sources page must display a completion summary.
- The completion summary must include aggregate counts for successes, failures, and skipped sources.
- The completion summary must include per-source result.
- The completion summary must include attempts used per executed source.
- Skipped sources must be included with a skipped status and the available reason, such as Unhealthy or ineligible.
- The completion summary only needs to remain visible on the Sources page for the current user session/view after completion.

### FR-9: Action Layout Refresh

- Batch actions must be placed in the top toolbar.
- Existing row actions may be represented as compact icon buttons.
- Icon-only row actions must provide accessible labels and/or tooltips that identify the action.
- Delete actions must remain visually destructive compared with non-destructive actions.

## 8. Acceptance Criteria

### AC-1: `Run All` ignores filters and runs all Healthy sources

Given the system has 10 Healthy sources and 3 Unhealthy sources, and the Sources table is filtered so only 2 Healthy sources are visible  
When the user selects `Run All`, confirms the action, and the batch starts  
Then all 10 Healthy sources are included for execution, and the 3 Unhealthy sources are skipped.

### AC-2: `Run All` confirmation shows eligible and skipped counts

Given the system has 7 Healthy sources and 2 Unhealthy sources  
When the user selects `Run All`  
Then the confirmation shows 7 eligible sources and 2 skipped sources before any source run starts.

### AC-3: Canceling `Run All` prevents execution

Given the `Run All` confirmation is displayed  
When the user cancels or dismisses the confirmation  
Then no source run is started.

### AC-4: `Run Selected` is disabled with no Healthy selected sources

Given no rows are selected, or only Unhealthy rows are selected  
When the Sources page toolbar is displayed  
Then `Run Selected` is disabled.

### AC-5: `Run Selected` is enabled with at least one Healthy selected source

Given one Healthy source and one Unhealthy source are selected  
When the Sources page toolbar is displayed  
Then `Run Selected` is enabled.

### AC-6: `Run Selected` skips selected Unhealthy sources

Given 3 selected sources are Healthy and 2 selected sources are Unhealthy  
When the user selects `Run Selected`, confirms the action, and the batch starts  
Then only the 3 Healthy selected sources are executed, and the 2 Unhealthy selected sources are skipped and included in the completion summary.

### AC-7: `Run Selected` confirmation shows selected eligible and skipped counts

Given 4 selected sources are Healthy and 1 selected source is Unhealthy  
When the user selects `Run Selected`  
Then the confirmation shows 4 eligible sources and 1 skipped source before any source run starts.

### AC-8: Batch concurrency is limited to 5 active source runs

Given a confirmed batch contains 12 eligible sources  
When the batch is executing  
Then no more than 5 source runs are active at the same time for that batch.

### AC-9: Batch continues after a source fails

Given a confirmed batch contains multiple eligible sources  
And one source fails all allowed attempts  
When the batch continues  
Then remaining eligible sources are still attempted according to the queue.

### AC-10: Each source receives no more than 3 total attempts

Given a source in a batch fails repeatedly  
When the source has failed 3 total attempts  
Then the system does not attempt that source again and marks it failed in the completion summary.

### AC-11: Source succeeds before max attempts

Given a source fails on attempt 1 and succeeds on attempt 2  
When the batch records the source result  
Then the source is marked successful with 2 attempts used and is not attempted a third time.

### AC-12: Progress is visible during execution

Given a user has confirmed a batch run  
When the batch is running  
Then the Sources page displays global progress/status indicating batch execution is active and updates as source results change.

### AC-13: Completion summary includes required aggregate counts

Given a batch has completed with 8 successful sources, 2 failed sources, and 3 skipped sources  
When the completion summary is displayed  
Then it shows 8 successes, 2 failures, and 3 skipped sources.

### AC-14: Completion summary includes per-source details

Given a batch has completed  
When the completion summary is displayed  
Then each eligible source has a per-source result and attempts used, and each skipped source has a skipped status with the available skip reason.

### AC-15: Duplicate batch start is prevented while running

Given a batch is starting or running  
When the user views the Sources page toolbar  
Then the UI prevents starting another ambiguous duplicate batch action for the same Sources page context.

### AC-16: Icon row actions are accessible

Given row actions are displayed as compact icon buttons  
When a user navigates the row actions using assistive technology or keyboard focus  
Then each icon action exposes an accessible action name and/or tooltip describing the action.

### AC-17: Delete remains visually destructive

Given row actions include delete and non-delete actions  
When the actions are displayed  
Then the delete action is visually distinguishable as destructive.

## 9. Edge Cases

- No Healthy sources exist for `Run All`: confirmation must indicate 0 eligible sources and the action must not start executions.
- All selected sources are Unhealthy: `Run Selected` remains disabled.
- A selected source becomes unavailable before execution: it must be reported as failed or skipped according to existing source run error handling and included in the summary.
- A source succeeds after one or more retries: the summary must show success and the actual attempts used.
- A source fails after all retries: the summary must show failure and 3 attempts used.
- The number of eligible sources is fewer than 5: concurrency must not create unnecessary extra executions; only eligible sources run.
- The user has active table filters/search during `Run All`: filters/search must not reduce the source set considered for execution.
- The table is paginated during `Run Selected`: selected rows are limited to the existing selection model; cross-page behavior is not added unless already supported.
- The completion summary is dismissed, the page is refreshed, or the user navigates away: summary persistence is not required unless already provided by existing architecture.
- The backend returns partial failures or network errors: each affected source must be reflected as failed or retried according to retry rules.

## 10. Constraints

- Concurrency limit is fixed at 5 active source runs per batch for this feature.
- Retry limit is fixed at 3 total attempts per eligible source for this feature.
- Retry backoff must be short; exact duration may follow existing retry/backoff conventions if present.
- Eligibility must use existing source health data and must not redefine health logic.
- `Run All` must operate on all system sources, not only the current table viewport.
- Completion summary persistence is not required beyond the Sources page unless already supported.
- UI controls must remain accessible for keyboard and assistive technology users.
- Destructive delete styling must be preserved.

## 11. Non-Functional Requirements

- The batch execution mechanism must avoid overwhelming the system by enforcing the concurrency limit.
- UI feedback must remain responsive while a batch is running.
- Progress and completion states must be deterministic enough for QA to validate using controlled source outcomes.
- The feature must be resilient to individual source failures and continue processing remaining sources.
- Accessibility must not regress for existing row actions when changing action layout.

## 12. Dependencies

- Existing Sources page and Sources table implementation.
- Existing source health status data, specifically the Healthy vs Unhealthy distinction.
- Existing individual source run mechanism or API used by `Run now`.
- Existing table selection model, if present, for determining whether selected rows can span pages.
- Existing UI component patterns for toolbar actions, confirmation dialogs, progress/status display, summaries, buttons, tooltips, and destructive actions.
- Existing retry/backoff utilities, if available.

## 13. Assumptions

- Requires confirmation: The product team should confirm whether existing source health statuses are exactly `Healthy` and `Unhealthy`, or whether additional statuses exist that must be treated as ineligible.
- Requires confirmation: The product team should confirm whether a single active batch at a time is required globally or only duplicate starts from the Sources page must be prevented.
- Requires confirmation: The technical team may use existing retry/backoff conventions for the definition of “short backoff” if such conventions exist.
- Requires confirmation: The existing individual source run operation can be safely orchestrated in batches without changing source-specific execution logic.

## 14. Open Questions

- What exact UI component should display the completion summary: inline panel, modal, toast with expandable details, or existing notification component?
- Should `Run All` be disabled when there are 0 Healthy sources, or should it remain enabled and show a confirmation with 0 eligible sources? The current requirement only mandates confirmation counts and no executions.
- If source health changes after confirmation but before an individual source starts, should eligibility be rechecked per source or frozen at confirmation time?
- Should active batch progress survive route changes within the application if the user returns to the Sources page before completion?
- What is the exact retry backoff duration if no existing convention is available?

## 15. QA Notes

- Test `Run All` with filters, search, sorting, and pagination applied to verify all Healthy system sources are considered.
- Test mixed Healthy and Unhealthy data sets for both `Run All` and `Run Selected`.
- Test 0 eligible, 1 eligible, fewer than 5 eligible, exactly 5 eligible, and more than 5 eligible sources.
- Use controlled failures to verify retry counts, backoff invocation, continuation after failure, and final failed status.
- Instrument or mock source execution to verify no more than 5 concurrent active runs.
- Verify confirmation cancellation produces zero source run calls.
- Verify completion summary includes aggregate counts and per-source details, including attempts used.
- Verify row action icon buttons expose accessible labels and/or tooltips.
- Verify delete retains destructive visual treatment after layout refresh.
