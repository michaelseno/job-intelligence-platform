# Design Specification

## 1. Feature Overview

Untracked jobs returned by ingestion must be reviewable only as transient current-runtime results. They must not appear as durable database-backed jobs unless the user assigns a non-null tracking status. Once tracked, the job becomes a normal persisted job and remains available across app restart.

## 2. User Goal

After running ingestion, the user wants to review newly discovered jobs, understand which results are temporary, and intentionally track the jobs they want to keep for their ongoing job-search workflow.

## 3. UX Rationale

The existing app already uses Sources to trigger ingestion and Jobs to review classified opportunities. This design keeps that mental model while adding clear persistence status cues:

- **Tracked jobs** remain normal persisted records.
- **Transient untracked results** are presented as current ingestion results, labeled as temporary, and given an explicit tracking action.
- The UI must not imply that untracked transient results are saved, retained, or restorable after restart.

## 4. User Flow

1. User runs ingestion from `/sources` or `/sources/{source_id}`.
2. Ingestion completes.
3. User sees success/failure feedback. On success, copy includes the count of fetched jobs and, when available, the count of temporary untracked results.
4. User opens `/jobs` to review actionable jobs.
5. `/jobs` shows a combined review list:
   - persisted tracked jobs from the database;
   - current transient untracked ingestion results from runtime/app state.
6. User identifies transient rows/cards by a **Temporary** badge and helper copy.
7. User may open a transient result detail view if detail data exists in runtime/app state.
8. User assigns any non-null tracking status, for example `Saved`.
9. UI enters saving state for that job.
10. On success, the transient result is replaced by the persisted tracked job, the **Temporary** badge is removed, tracking status updates, and navigation uses the normal persisted job URL.
11. If ingestion runs again before the user tracks a transient result, the transient list is replaced by the latest ingestion result set.
12. If the app restarts before tracking, previous transient results are absent.

## 5. Information Hierarchy

1. **Page-level context:** Jobs page title and description must explain that the page can include temporary current-ingestion results.
2. **Result identity:** title, company, source, location, score, and automated bucket remain primary.
3. **Persistence status:** transient status is visually adjacent to bucket/tracking badges.
4. **Tracking action:** assigning status is the primary conversion action for transient results.
5. **Temporal warning:** transient helper text explains that untracked results disappear after app restart or the next ingestion run.
6. **Operational metadata:** source/run history remains secondary and should not overtake job review actions.

## 6. Layout Structure

### Target Screens / Routes / Components

- `/sources`
  - Existing configured sources table.
  - Existing per-source **Run ingestion** forms.
  - Desired: post-run flash/message copy may reference temporary untracked results.
- `/sources/{source_id}`
  - Existing source detail header action **Run ingestion**.
  - Existing run history table.
  - Desired: latest run area may link to `/jobs` with current ingestion results visible.
- `/jobs`
  - Primary target screen for viewing transient untracked results.
  - Existing filters, table view, and mobile card list must support mixed persisted and transient items.
- Job detail surface
  - Existing `/jobs/{job_id}` remains for persisted jobs only.
  - Desired transient detail surface must be detail-compatible but clearly temporary. If implemented as a route, use a runtime-safe transient identifier, not a database id. If no transient detail endpoint is available, transient results should use an expandable inline details panel instead of a broken “View” link.
- Shared components
  - `includes/macros.html` job badge area, tracking form, keep/save action.
  - Jobs list table rows and mobile cards.
  - App-level flash/alert messaging in `base.html`.

### Jobs List Layout

- Add a page-level informational callout above results when transient results are present:
  - Title: **Temporary ingestion results**
  - Body: **Untracked jobs from the latest ingestion run are only available during this app session. Track a job to save it. Running ingestion again replaces this temporary list.**
- Result rows/cards use existing layout with one additional badge in the badge stack:
  - `Temporary` for transient untracked results.
  - No badge for normal persisted tracked jobs.
- The results summary must distinguish counts:
  - Example: **12 jobs shown: 5 tracked, 7 temporary from the latest ingestion run.**
- In desktop table, keep columns unchanged. Add the `Temporary` badge under Tracking or in the Role subtitle area to avoid adding horizontal width.
- In mobile cards, show `Temporary` in the header badge stack before the tracking action.

## 7. Components

1. **Temporary ingestion callout**
   - Type: informational callout.
   - Shows only when at least one transient untracked result is present.
2. **Result count summary**
   - Text summary above table/card list.
   - Must include transient count when non-zero.
3. **Job row/card**
   - Existing job display component extended with transient metadata.
4. **Temporary badge**
   - Label: `Temporary`.
   - Tone: warning or neutral-warning.
   - Adjacent screen-reader text must clarify: `Temporary untracked ingestion result`.
5. **Tracking status form**
   - Existing select + update button.
   - For transient results, primary label should be `Track job` or `Save as tracked`, not `Update` alone.
6. **View details control**
   - Persisted jobs: link to `/jobs/{job_id}`.
   - Transient jobs: link to transient detail route or opens inline details. Must not point to `/jobs/{job_id}` until persistence succeeds.
7. **Flash/alert messages**
   - Success, error, and warning copy for ingestion and tracking outcomes.

## 8. Interaction Behavior

### Viewing Transient Ingestion Results

- **Trigger:** User completes ingestion and navigates to `/jobs`.
- **System response:** Jobs list receives persisted tracked jobs plus current transient untracked results from runtime/app state.
- **UI feedback:** Temporary callout appears if transient count > 0; each transient result has a `Temporary` badge.
- **Success behavior:** User can review transient result title, company, source, bucket, score, reason summary, location, and available source link/classification evidence.
- **Failure behavior:** If transient runtime data is unavailable, the UI shows the normal empty or filtered-empty state and must not show stale persisted untracked jobs.

### Running Ingestion Again

- **Trigger:** User starts another ingestion run from `/sources` or `/sources/{source_id}`.
- **System response:** Current transient untracked result set is replaced when the new run completes.
- **UI feedback:** Jobs page count and temporary result rows/cards reflect only the latest current-runtime result set.
- **Success behavior:** Previously visible untracked transient results disappear unless returned again or already tracked.
- **Failure behavior:** If ingestion fails, keep the previous transient result set only if backend/app state explicitly keeps it for the current runtime. Show alert: **Ingestion failed. Temporary results were not refreshed.** If backend clears on failure, show: **Ingestion failed. No temporary results are available from this run.**

### Tracking / Saving a Transient Job

- **Trigger:** User selects a non-empty tracking status and submits the tracking form for a transient result.
- **System response:** Persist job, source link, latest classification result, and ingestion metadata; then return the persisted job representation.
- **UI feedback while saving:**
  - Disable that row/card tracking select and submit button.
  - Button text: **Saving…**
  - Row/card sets `aria-busy="true"`.
- **Success behavior:**
  - Remove `Temporary` badge.
  - Show selected tracking status badge.
  - Replace transient identifier with persisted job id for future actions.
  - Detail link changes to `/jobs/{job_id}`.
  - Flash/inline status: **Job tracked and saved.**
- **Failure behavior:**
  - Keep transient row/card visible if still present in runtime state.
  - Re-enable controls.
  - Show inline row error and page alert: **Job could not be saved. Try again before running ingestion again or restarting the app.**

### Existing Tracked Jobs Matched During Ingestion

- **Trigger:** Ingestion returns a job matching an existing persisted tracked job.
- **System response:** Existing update behavior continues.
- **UI feedback:** Job appears as a normal tracked job with no `Temporary` badge.
- **Success behavior:** User can manage it through existing tracking/detail views.
- **Failure behavior:** Existing ingestion error handling applies.

## 9. Component States

### Temporary Ingestion Callout

- Default: visible when transient count > 0.
- Hover: none; static component.
- Focus: callout itself is not focusable unless used as an alert target after ingestion; if focused, use standard focus ring.
- Active: not applicable.
- Disabled: not applicable.
- Loading: not shown during ingestion loading unless current transient state is known.
- Success: shown with informational tone after successful ingestion with transient results.
- Error: use danger alert, not info callout, when transient data cannot load.
- Empty: hidden when transient count is 0.

### Temporary Badge

- Default: displays `Temporary` with warning/neutral-warning styling.
- Hover: no tooltip required; optional `title` must duplicate visible meaning only.
- Focus: not focusable.
- Active: not applicable.
- Disabled: not applicable.
- Loading: not applicable.
- Success: removed after tracking persistence succeeds.
- Error: remains visible if save fails.
- Empty: absent for persisted tracked jobs.

### Tracking Status Form

- Default: select shows `Select status`; submit button disabled until a non-empty status is selected, if client-side enhancement is present. Without JS, server validates empty status.
- Hover: button uses existing secondary/primary hover styles.
- Focus: select and button use visible `:focus-visible` outline.
- Active: button appears pressed only during click/submission.
- Disabled: select/button disabled while save is in progress or when job is already in a terminal UI state that cannot be changed.
- Loading: button text `Saving…`; row/card `aria-busy="true"`.
- Success: selected status displayed; transient badge removed; success message announced.
- Error: inline error below form; controls re-enabled.
- Empty: empty selection is not a valid tracking submission.

### View Details Control

- Default: visible when detail data or persisted detail route is available.
- Hover: existing link/button hover state.
- Focus: visible focus outline.
- Active: native link/button active behavior.
- Disabled: if transient detail is unavailable, replace control with muted text **Details unavailable for temporary result**; do not render disabled anchor.
- Loading: if inline detail loads async, show **Loading details…** with `aria-busy="true"`.
- Success: detail content displays.
- Error: show **Temporary details are no longer available. Run ingestion again or track the job from the list if it is still visible.**
- Empty: hidden when neither persisted nor transient detail is available.

### Run Ingestion Button

- Default: enabled for active sources.
- Hover/focus/active: existing button behavior.
- Disabled: disabled for inactive sources and during in-flight submission if enhanced.
- Loading: button text may change to **Running…**; form `aria-busy="true"`.
- Success: flash indicates ingestion completed and temporary results may be available.
- Error: existing ingestion failure flash.
- Empty: when run returns zero jobs, show zero-result copy.

## 10. Responsive Design Rules

### Desktop

- Preserve existing table layout.
- Add temporary status inside existing Role/Tracking cell to avoid new columns.
- Temporary callout spans full content width above results.

### Tablet

- Preserve table scroll behavior.
- Keep callout and filters stacked according to existing responsive rules.
- Badge stack may wrap; do not truncate `Temporary`.

### Mobile

- Use existing mobile card list.
- Place `Temporary` badge in card header badge stack.
- Put tracking form below primary metadata with full-width select and button if space is constrained.
- Inline errors appear immediately below the tracking form.

## 11. Visual Design Tokens

Use existing tokens from `app/static/css/app.css`:

- Text: `--text-primary`, `--text-secondary`, `--text-tertiary`.
- Borders: `--border-default`, `--border-strong`.
- Warning/temporary: `--warning-50`, `--warning-600`.
- Success saved state: `--success-50`, `--success-600`.
- Error: `--danger-50`, `--danger-600`.
- Focus: `--brand-600` outline.
- Spacing/radius: existing `--radius-md`, `--radius-lg`, panel and table spacing.

Copy must use plain language. Avoid “persist”, “database”, or “runtime state” in user-facing UI except developer/debug contexts. Prefer “temporary”, “saved”, and “tracked”.

## 12. Accessibility Requirements

- Temporary callout uses `role="status"` when inserted after ingestion completion; static server-rendered callout may be a normal section with heading.
- Error alerts use `role="alert"`.
- Tracking select label must include job title, e.g. **Tracking status for Senior Backend Engineer**.
- For transient rows, include screen-reader-only text: **This is a temporary untracked ingestion result. Track it to save it.**
- Keyboard order in each row/card: job title/details, source posting link if present, tracking select, submit button.
- Focus after successful transient tracking:
  - If staying on list, move focus to the success message or the updated job row heading.
  - If redirecting to persisted detail, focus page `<h1>` on load.
- Focus after save failure moves to inline error message.
- Color must not be the only indicator of transient state; the visible `Temporary` text is required.
- All button text must communicate action without relying on icon-only affordances.

## 13. Edge Cases

- Ingestion returns zero jobs: show success/empty copy, no temporary callout.
- Ingestion returns only new untracked jobs: `/jobs` shows temporary results with callout; no tracked count required beyond summary.
- Ingestion returns mixed tracked and transient jobs: show both; only transient items get `Temporary` badge.
- Same job appears from multiple sources before tracking: display one deduplicated transient result if backend deduplicates; otherwise display source labels clearly and avoid implying persistence.
- User tracks after another ingestion run refreshes results: if transient id is no longer valid, show error: **This temporary result is no longer available. Run ingestion again or track a currently visible result.**
- App restarts before tracking: previous transient results are absent; do not show persisted untracked jobs.
- Existing persisted untracked jobs removed by cleanup: they must not appear in Jobs, Tracking, source-linked job counts, or job details.
- `manual_keep=true` with no tracking status: do not display as saved/tracked and do not use Keep copy to imply retention.

## 14. Developer Handoff Notes

- Do not add a new primary navigation item for transient results; use the existing Jobs review surface.
- Persisted job detail route `/jobs/{job_id}` must remain database-backed only.
- Transient result actions must use a runtime-safe identifier supplied by backend/app state, not a fake database id.
- Do not render stale untracked database rows as a fallback.
- Update user-facing copy currently saying “Save / Keep preserves…” where needed so transient jobs are tracked by assigning a non-null tracking status, not by `manual_keep` semantics.
- Maintain progressive enhancement: server-rendered form submission must work without JavaScript; JS may improve disabled/loading states.
- Ensure QA can distinguish transient and persisted items through visible text, not only styling.

## Acceptance Criteria Mapping Relevant to UI Behavior

- AC-03: `/jobs` shows current transient untracked results with `Temporary` labeling before another ingestion run or restart.
- AC-04: After a new ingestion run, `/jobs` reflects the latest transient result set only.
- AC-05: After app restart, previous transient untracked results are not shown.
- AC-06: Matched existing tracked jobs appear as normal tracked jobs with no temporary badge.
- AC-10: Assigning a non-null tracking status from a transient result shows saving feedback and converts it to a persisted tracked job on success.
- AC-11: Success UI must only appear after persistence of related source/classification/ingestion context completes.
- AC-12: Tracked transient jobs continue to appear after restart as normal tracked jobs.
- AC-13/AC-14: Removed persisted untracked jobs do not appear in Jobs, details, Tracking, or source-linked job surfaces.

## Explicit Non-Goals

- No new tracking status values.
- No archive, restore, or “recover temporary jobs” flow.
- No promise that untracked transient results survive restart.
- No redesign of classification scoring, bucket logic, source adapters, or ingestion matching.
- No use of `manual_keep` as a persistence or retention signal.
- No multi-user synchronization or cloud retention behavior.
