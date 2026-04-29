# Design Specification

## 1. Feature Overview

Sources Batch Run Controls and Action Layout Refresh adds batch execution controls to the Sources inventory page and reduces row-action clutter.

The Sources page will support:

- Top toolbar actions: `Run All` and `Run Selected`.
- Checkbox row selection for selected-source batch runs.
- Confirmation dialogs with eligible and skipped counts before execution.
- A global progress/status panel while a batch is running.
- An inline completion summary with aggregate and per-source outcomes.
- Compact accessible icon row actions for Open, Edit source, Run now, and Delete source.

## 2. User Goal

The user wants to refresh multiple job data sources from the Sources page without manually running each source, while understanding which sources will run, which will be skipped, and what happened after the batch completes.

## 3. UX Rationale

### Design goals

- Make batch actions visible at the page/table level instead of repeating them in every row.
- Keep individual source actions available but reduce table clutter through compact icon buttons.
- Prevent accidental large batch execution with explicit confirmation.
- Make eligibility transparent by showing eligible and skipped counts before starting.
- Preserve trust during long-running execution through persistent progress feedback.
- Provide actionable completion details so users can identify failed, retried, or skipped sources.
- Preserve accessibility for keyboard and assistive technology users.

### Approach

Batch actions belong in the Source inventory toolbar because they operate on the table/source collection. Row actions remain per-source controls and are visually compacted. Progress and completion summaries are inline on the Sources page rather than modal after start, because users need ongoing visibility without blocking table review.

## 4. User Flow

### Run All flow

1. User opens the Sources page.
2. User selects `Run All` in the Source inventory toolbar.
3. System disables the initiating button and requests a backend preview for all system sources.
4. System opens a confirmation dialog showing:
   - Eligible Healthy source count.
   - Skipped source count.
   - Statement that current filters/search are ignored.
5. User chooses either:
   - `Cancel`: dialog closes, no runs start, focus returns to `Run All`.
   - `Run eligible sources`: system starts the batch from the preview.
6. System closes the dialog and shows the global progress/status panel.
7. System updates progress as source results change.
8. System replaces/updates the progress panel with a completion summary when the batch reaches a terminal state.

### Run Selected flow

1. User selects one or more source rows using checkboxes.
2. `Run Selected` becomes enabled only if at least one selected source is Healthy.
3. User selects `Run Selected`.
4. System disables the initiating button and requests a backend preview for selected source IDs.
5. System opens a confirmation dialog showing:
   - Selected source count.
   - Eligible Healthy selected source count.
   - Skipped selected source count.
6. User confirms or cancels.
7. On confirm, the same progress and completion pattern as `Run All` is used.

## 5. Information Hierarchy

1. Page title and existing page-level actions remain unchanged.
2. Source inventory card/table toolbar:
   - Primary batch actions: `Run All`, `Run Selected`.
   - Selection status text when rows are selected.
   - Existing table search/filter controls, if present.
3. Global batch status region:
   - Active batch state and progress counts.
   - Aggregate success/failure/skipped counts.
   - Optional per-source progress details.
4. Source inventory table:
   - Selection checkbox column.
   - Existing source details: Name, Adapter, Health, Last run.
   - Compact row actions.
5. Completion summary:
   - Aggregate counts first.
   - Per-source result table second.
   - Skipped sources with reasons.

## 6. Layout Structure

### Layout / placement

- Add a Source inventory toolbar directly above the table and inside the table/card boundary.
- Toolbar left side:
  - `Run All` button.
  - `Run Selected` button.
  - Selection status text, e.g. `3 selected`.
- Toolbar right side:
  - Existing table controls such as search/filter, if currently present.
- Batch progress/status panel appears below the toolbar and above the table.
- Completion summary appears in the same region below the toolbar and above the table after completion.
- Row selection checkboxes appear as the first table column.
- Row actions remain in the last table column as compact icon buttons in one horizontal group.

### Confirmation modal content

Confirmation dialogs use a semantic modal dialog centered in the viewport with a dimmed page overlay.

#### Run All confirmation

- Title: `Run all healthy sources?`
- Body copy:
  - `This will run all Healthy sources in the system. Current filters, search, sorting, and pagination will not limit this run.`
  - Count summary:
    - `Eligible to run: {eligible_count}`
    - `Skipped: {skipped_count}`
- Optional details disclosure:
  - Label: `View skipped sources`
  - Shows skipped source names and reasons when available.
- Actions:
  - Secondary: `Cancel`
  - Primary: `Run eligible sources`

#### Run Selected confirmation

- Title: `Run selected healthy sources?`
- Body copy:
  - `Only selected sources that are Healthy will run. Selected sources that are not eligible will be skipped.`
  - Count summary:
    - `Selected: {selected_count}`
    - `Eligible to run: {eligible_count}`
    - `Skipped: {skipped_count}`
- Optional details disclosure:
  - `View skipped sources`
- Actions:
  - Secondary: `Cancel`
  - Primary: `Run eligible sources`

If `eligible_count` is `0`, the primary start action is not shown. Show a single primary/secondary close action labeled `Close` and copy: `No sources are eligible to run.`

## 7. Components

- Source inventory toolbar.
- `Run All` button.
- `Run Selected` button.
- Row selection checkbox.
- Select-all-visible checkbox in table header.
- Selection count text.
- Confirmation modal dialog.
- Global batch progress/status panel.
- Progress indicator/counts.
- Completion summary panel.
- Completion summary result table/list.
- Inline alert for preview/start/status errors.
- Compact icon row action group.
- Tooltip for icon-only row actions.

### Row action icon mapping

Use existing icon set if available. If no icon library exists, use text glyphs only with accessible names; do not rely on icon meaning alone.

| Current action | Icon meaning | Accessible label pattern | Tooltip text | Visual treatment |
| --- | --- | --- | --- | --- |
| Open | External/open or eye icon | `Open {source_name} source` | `Open` | Neutral |
| Edit source | Pencil/edit icon | `Edit {source_name} source` | `Edit source` | Neutral |
| Run now | Play/refresh icon | `Run {source_name} now` | `Run now` | Neutral or primary-subtle |
| Delete source | Trash icon | `Delete {source_name} source` | `Delete source` | Destructive danger color/style |

## 8. Interaction Behavior

### Toolbar behavior

#### Run All

- Trigger: user clicks button or activates it by keyboard.
- System response:
  - Set button to loading state.
  - Disable `Run All` and `Run Selected` during preview request.
  - Request `POST /sources/batch-runs/preview` with mode `all`.
- Success behavior:
  - Open Run All confirmation dialog with backend counts.
  - Restore non-initiating controls unless dialog/start state requires disabled controls.
- Failure behavior:
  - Show inline error alert in the batch status region.
  - Re-enable batch actions if no active batch is running.

#### Run Selected

- Trigger: user clicks button or activates it by keyboard.
- Enabled only when at least one selected row has Healthy health state and no batch is starting/running.
- System response:
  - Set button to loading state.
  - Disable batch action buttons during preview request.
  - Request preview with selected source IDs from the current selection model.
- Success/failure behavior matches `Run All`.

### Row selection behavior

- Row checkbox trigger: click, Space key, or associated label activation.
- Selecting a row updates:
  - Row selected visual state.
  - Selection count text.
  - `Run Selected` enabled/disabled state.
- `Run Selected` enablement is based on selected rows with `data-health-state="healthy"` for immediate UI feedback, but backend preview remains authoritative.
- Select-all checkbox selects/deselects visible rows only unless an existing cross-page selection model already supports more.
- Header checkbox state:
  - Unchecked: no visible rows selected.
  - Checked: all visible rows selected.
  - Indeterminate: some visible rows selected.
- Selection is not required for `Run All`.
- During active batch execution, row selection may remain usable for table review, but `Run All` and `Run Selected` remain disabled to prevent duplicate starts.

### Progress/status behavior

- On confirmed start, close modal and show global progress panel.
- Poll batch status once per second while status is `starting` or `running`.
- Panel content while running:
  - Heading: `Batch run in progress`
  - Mode label: `Run All` or `Run Selected`.
  - Counts: `{completed_count} of {eligible_count} completed`, `{running_count} running`, `{pending_count} queued`, `{success_count} succeeded`, `{failure_count} failed`, `{skipped_count} skipped`.
  - Progress bar based on `completed_count / eligible_count`; if `eligible_count` is 0, render completed empty state instead of a progress bar.
  - Text note: `Up to 5 sources run at the same time. Failed sources may retry up to 3 attempts.`
- Per-source running details may be shown in a compact list/table below aggregate counts when data is available.
- No cancel/pause/resume controls are shown because they are out of scope.
- On polling failure:
  - Show non-destructive inline error: `Unable to refresh batch status. Retrying…`
  - Continue polling unless backend reports terminal/unknown failure.
- On `404` unknown/expired batch:
  - Stop polling.
  - Show error: `Batch status is no longer available. Completed source attempts may still appear in source run history.`
  - Re-enable batch actions.

### Completion summary design

- Completion summary appears inline below the toolbar and above the table.
- Heading variants:
  - `Batch run completed` when no failures.
  - `Batch run completed with failures` when one or more source failures occurred.
  - `Batch run failed` for batch-level orchestration failure.
- Aggregate cards/chips:
  - `Succeeded: {success_count}`
  - `Failed: {failure_count}`
  - `Skipped: {skipped_count}`
  - `Eligible: {eligible_count}`
- Detail table columns:
  - Source.
  - Result.
  - Attempts used.
  - Reason or last error.
- Result labels:
  - `Succeeded`
  - `Failed after retries`
  - `Skipped`
  - `Queued` / `Running` only while progress details are shown before terminal completion.
- Attempts display:
  - Executed sources: `{attempts_used} of 3`.
  - Skipped sources: `—`.
- Include a `Dismiss summary` button. Dismissing hides the current in-session summary only.

### Row action behavior

- Icon action buttons/links must maintain existing destinations or form behavior.
- Tooltips appear on hover and keyboard focus.
- Delete continues to use the existing delete confirmation/route behavior and danger styling.
- Row-level `Run now` remains a single-source action and must not trigger batch confirmation.

## 9. Component States

### Run All button

- Default: enabled, label `Run All`.
- Hover: visible hover treatment matching existing button system.
- Focus: visible focus ring with at least 3:1 contrast against adjacent colors.
- Active: pressed visual state.
- Disabled: disabled while preview/start/running batch is active if required by duplicate prevention.
- Loading: label may be `Preparing…`; include spinner with accessible text.
- Success: no persistent button success state; progress panel communicates start success.
- Error: button returns to enabled if no active batch; error alert explains failure.
- Empty: if no Healthy sources exist, button may remain enabled to allow confirmation/zero-eligible explanation; start action in modal is disabled/removed.

### Run Selected button

- Default: disabled when no selected Healthy rows; enabled when at least one selected Healthy row exists.
- Hover/focus/active: same button standards as `Run All` when enabled.
- Disabled: include accessible reason via surrounding text or `title`, e.g. `Select at least one Healthy source to run selected sources.`
- Loading: label may be `Preparing…`.
- Success: progress panel communicates start success.
- Error: button returns to selection-derived state if no active batch.
- Empty: disabled when zero rows selected or selected rows are all ineligible.

### Row checkbox

- Default: unchecked.
- Hover: row or checkbox hover affordance.
- Focus: visible focus ring on checkbox.
- Active: checked state toggles immediately.
- Disabled: only if table row is not selectable due to existing table constraints; otherwise all rows are selectable, including unhealthy rows.
- Loading/success/error: not applicable; selection is client-side.
- Empty: no checkboxes rendered in an empty table body.

### Select-all-visible checkbox

- Default unchecked.
- Checked when all visible rows are selected.
- Indeterminate when some visible rows are selected.
- Focus/hover/active: native checkbox behavior with visible focus.
- Disabled when no visible rows exist.

### Confirmation modal

- Default: hidden.
- Loading: modal not shown until preview succeeds; initiating toolbar button shows loading.
- Open: focus moves to modal title or first focusable control.
- Focus: focus is trapped within modal.
- Active: primary/secondary buttons show pressed states.
- Disabled: primary start button disabled/absent when `eligible_count` is 0 or start request is pending.
- Success: modal closes and progress panel appears.
- Error: inline modal error if start fails; keep dialog open when user can retry or close.
- Empty: zero eligible state shows `No sources are eligible to run.` and no start action.

### Progress panel

- Default: hidden when no active/recent batch exists.
- Loading/starting: show `Starting batch run…`.
- Running: show live counts and progress bar.
- Success: transitions to completion summary.
- Error: show alert for status polling/start failures.
- Empty: zero eligible batch shows completed summary with skipped count and no progress bar.
- Disabled/hover/focus/active: only applicable to contained controls such as `Dismiss summary`.

### Completion summary

- Default: hidden before batch completion.
- Success: visible with aggregate and per-source results.
- Error: visible as `Batch run failed` for batch-level failure.
- Empty: if no eligible sources ran, show skipped sources and reason list.
- Focus: when summary appears after completion, do not steal focus if user is interacting elsewhere; announce via live region. If completion follows a confirmed modal action and focus has no meaningful target, move focus to summary heading.
- Dismiss active/hover/focus/disabled states follow standard button behavior.

### Icon row actions

- Default: compact icon with tooltip/accessibility label.
- Hover: visible hover background/border.
- Focus: visible focus ring; tooltip appears.
- Active: pressed/clicked state.
- Disabled/loading/success/error: preserve existing behavior for row-level actions; if an action becomes async, show busy state and prevent duplicate submit.
- Delete destructive: default, hover, focus, and active states use danger styling distinct from neutral actions.

## 10. Responsive Design Rules

### Desktop

- Toolbar uses horizontal layout with batch actions on the left and table utilities on the right.
- Row actions display as a horizontal icon group.
- Progress and summary detail tables use full table layout.

### Tablet

- Toolbar may wrap to two rows.
- Batch action group remains first in reading order.
- Search/filter controls move below batch controls if space is constrained.
- Completion detail table remains tabular if columns fit; otherwise reduce nonessential column width and allow horizontal overflow within the summary panel.

### Mobile

- Toolbar stacks vertically:
  1. Batch action buttons full width or two-column if width allows.
  2. Selection status text.
  3. Existing search/filter controls.
- Source table may use existing responsive table behavior. If the table becomes horizontally scrollable, keep the selection checkbox and row actions reachable without overlapping content.
- Confirmation modal uses near-full-width dialog with max height and internal scrolling.
- Progress counts stack in a single column or two-column grid.
- Completion summary details may switch from table rows to cards:
  - Source name.
  - Result badge.
  - Attempts.
  - Reason/error.

## 11. Visual Design Tokens

Use existing project tokens/classes where available. Do not introduce a conflicting design system.

- Spacing:
  - Toolbar gap: 8–12px.
  - Panel padding: 16px desktop, 12px mobile.
  - Row action icon hit target: minimum 36px by 36px; prefer 40px by 40px on touch.
- Status colors:
  - Success: existing success/healthy token.
  - Failure/error: existing danger/error token.
  - Skipped/warning: existing muted or warning token.
  - Running/info: existing primary/info token.
- Typography:
  - Panel headings use existing card heading style.
  - Count labels use body text; numeric values may be semibold.
- Contrast:
  - Text and controls must meet WCAG AA contrast.
  - Danger delete control must remain distinguishable by color and icon/label, not color alone.

## 12. Accessibility Requirements

### Keyboard operation

- `Run All`, `Run Selected`, checkboxes, modal controls, disclosure controls, row actions, and summary dismiss are keyboard reachable.
- Checkboxes toggle with Space.
- Buttons activate with Enter and Space.
- Modal can be dismissed with Escape and `Cancel`.
- Focus order follows visual/reading order: toolbar, status/summary, table header, table rows.

### Focus management

- On confirmation open, move focus into the dialog.
- Trap focus inside the dialog until it closes.
- On cancel/dismiss, return focus to the initiating button.
- On confirm/start, move focus to the progress panel heading or keep focus on a stable status region if implemented as an announced live region.

### ARIA and semantics

- Confirmation uses `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `aria-describedby`.
- Progress/status panel uses `role="status"` or `aria-live="polite"` for aggregate updates.
- Blocking errors use `role="alert"`.
- Progress bar uses native `<progress>` or `role="progressbar"` with `aria-valuemin`, `aria-valuemax`, and `aria-valuenow` when eligible count is greater than 0.
- Icon-only actions use accessible names, e.g. `aria-label="Delete Acme source"`.
- Tooltips must not be the only accessible name; use `aria-label` or visually hidden text.
- Header select-all checkbox includes a clear label such as `Select all visible sources`.
- Row checkbox label pattern: `Select {source_name}`.

### Screen reader compatibility

- Announce preview/start errors immediately.
- Announce progress changes politely and avoid overly frequent verbose per-source announcements.
- Completion summary heading is announced when the batch finishes.
- Counts must be rendered as text, not only visual badges.

## 13. Edge Cases

### Empty / disabled / error states

- No sources in table: show existing empty table message; disable select-all and `Run Selected`; `Run All` may remain enabled if backend can explain zero eligible, otherwise disable with helper text.
- No Healthy sources for `Run All`: confirmation shows `Eligible to run: 0`; no start action is available; no execution starts.
- Selected rows are all Unhealthy/ineligible: `Run Selected` remains disabled.
- Mixed selected Healthy and Unhealthy rows: `Run Selected` enabled; confirmation and summary include skipped count/details.
- Active search/filter with `Run All`: confirmation explicitly states filters/search are ignored.
- Paginated table: selected rows are limited to the existing selection model; do not add cross-page selection UX in this scope.
- Preview request fails: show inline alert `Could not prepare batch run. Try again.`; no modal opens.
- Preview expires before start: show modal or inline error `This confirmation expired. Prepare the batch run again.`
- Start returns conflict due to active batch: show `Another batch run is already active. Wait for it to finish before starting another.`
- Batch-level failure: show completion/error panel with available details and re-enable batch actions.
- Source unavailable after confirmation: show as failed or skipped according to backend response with reason.
- Completion summary dismissed: hide summary for current view; persistence is not required.
- Page refresh/navigation: active in-memory summary may be unavailable; do not promise persisted history.

## 14. Developer Handoff Notes

### Frontend handoff notes

- Add UI under `app/templates/sources/index.html`, `app/static/js/app.js`, and `app/static/css/app.css` per architecture.
- Use backend preview response as source of truth for eligible/skipped counts; client-side health only controls immediate button enablement.
- `Run All` preview must send mode `all` and must not include filter/search/sort/page state.
- `Run Selected` preview sends selected source IDs from the existing selection model only.
- Disable both batch action buttons during preview loading, start pending, and active batch execution.
- Poll status every 1 second while status is `starting` or `running`; stop on terminal status.
- Do not add cancel, pause, resume, retry-failed, schedule, export, notification, or persisted history controls.
- Preserve existing row-level `Run now` job preference behavior.
- Delete row action must keep the existing destructive visual class/confirmation behavior.
- Add stable DOM hooks for tests, e.g. `data-testid` or existing project convention for:
  - batch toolbar
  - run all button
  - run selected button
  - confirmation dialog
  - progress panel
  - completion summary
  - row selection checkboxes
  - row action buttons

### Copy guidelines

- Use `Healthy` when referring to eligible health state.
- Use `skipped` for sources not executed because they are not eligible.
- Use `failed after retries` for sources that exhausted all attempts.
- Avoid ambiguous copy such as `some sources failed`; include counts and source-level details.
- State that `Run All` ignores filters/search anywhere the user is about to confirm the action.
- Keep button labels action-oriented:
  - `Run All`
  - `Run Selected`
  - `Run eligible sources`
  - `Cancel`
  - `Close`
  - `Dismiss summary`

### QA-visible acceptance hooks

- Verify `Run Selected` enables only with at least one selected Healthy row.
- Verify confirmation cancellation does not call start.
- Verify zero eligible confirmation cannot start execution.
- Verify progress counts update and are announced through a live region.
- Verify completion summary includes successes, failures, skipped sources, and attempts used.
- Verify icon-only row actions expose accessible names and keyboard tooltips.
- Verify delete remains visually destructive.
