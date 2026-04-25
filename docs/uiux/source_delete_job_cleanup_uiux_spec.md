# Design Specification

## 1. Feature Overview

Source deletion now starts asynchronous cleanup of jobs associated with the deleted source. The UI must communicate that deletion is immediate, cleanup may continue briefly in the background, and only jobs that are both `matched` and `active` can remain visible.

This specification applies to the existing server-rendered Jinja UI surfaces:
- Source list, source detail, and source delete confirmation
- Jobs list and source filter
- Dashboard stat cards and recent job cards
- Job detail source evidence
- Standard flash/alert, empty state, badge, button, and callout patterns

Assumption: backend/query changes will hide pending-deletion jobs immediately; frontend should not add client-side filtering or polling unless a future product decision adds explicit cleanup status.

## 2. User Goal

As a job seeker, when I delete a source, I want stale jobs from that source removed from my working views immediately while important matched active opportunities are preserved, so my dashboard and job list stay trustworthy without making me wait for physical cleanup.

## 3. UX Rationale

- Deleting a source is a data lifecycle action, not only a configuration action. The confirmation must warn that most linked jobs will be permanently removed.
- The user should not need to understand background workers. The UI should confirm that cleanup has started and that working views already exclude stale jobs.
- Retained matched active jobs should remain useful, but their deleted source must not feel actionable or available for ingestion.
- Existing UI patterns are intentionally lightweight: server-rendered pages, stat cards, tables/cards, callouts, and global flash alerts. This feature should extend copy and states rather than introduce a new dashboard subsystem.

## 4. Information Hierarchy

### Source delete confirmation page
1. Page title: “Delete source”
2. Source name being deleted
3. Destructive warning and permanent cleanup rule
4. Impact summary cards
5. Plain-language retention/deletion explanation
6. Primary destructive action: “Delete source”
7. Secondary action: “Cancel”

### Post-delete global feedback
1. Success alert that source was deleted
2. Cleanup status statement: queued/started in background
3. Immediate outcome statement: non-retained jobs are removed from dashboard/jobs views now

### Jobs and dashboard after deletion
1. Counts/cards reflect only visible eligible jobs
2. Deleted-source non-retained jobs are absent
3. Retained matched active jobs may remain with normal bucket/tracking/status controls
4. Deleted source is not present in source filters or source actions

### Job detail for retained jobs
1. Job content remains accessible
2. Source evidence may show deleted source as historical/deleted/retired provenance if available
3. No edit/run/source-management action is offered for the deleted source

## 5. Layout Structure

### Source deletion confirmation
Use the existing `panel panel-narrow` layout.

Recommended structure:
```text
Page header
└─ Title: Delete source
└─ Description: Review cleanup impact before removing this source.

Panel
├─ Intro sentence: You are about to delete <source name>.
├─ Danger callout: permanent cleanup warning
├─ Impact stat cards
│  ├─ Linked jobs
│  ├─ Will be removed (if count available)
│  └─ Matched active retained (if count available)
├─ Cleanup explanation copy
└─ Action row
   ├─ Delete source
   └─ Cancel
```

If backend cannot provide precomputed removal/retention counts, keep current stat cards but update copy to describe the rule without exact numbers.

### Dashboard
No new persistent cleanup widget is required. Existing stat cards and recent job sections must update to exclude non-retained jobs from deleted sources immediately after the delete response. If the delete action redirects to dashboard or sources with a flash message, use the existing `.alert-success` or `.alert-info` pattern.

### Jobs list
Keep existing filter panel and table/mobile card layouts. The source dropdown must include active/configured non-deleted sources only. Do not show deleted sources as filter options.

### Job detail retained source evidence
Within the existing “Source evidence” panel, if provenance for a deleted source is shown, label it as historical/deleted inline near the source name.

Recommended row format:
```text
<Source name>  [Deleted source]
External job id: … · Last seen …
Open posting
```

The “Deleted source” label should be informational and non-actionable.

## 6. Components

### Danger callout: source cleanup warning
- Component: existing `.callout.callout-danger`
- Recommended copy:
  - Heading: “This permanently removes most jobs from this source”
  - Body: “Deleting this source removes it from source management and future ingestion immediately. Jobs linked to this source will be cleaned up in the background. Only jobs that are both Matched and Active will be retained.”

### Impact stat cards
- Component: existing `ui.stat_card`
- Required if data is available:
  - “Linked jobs” = all jobs associated with source
  - “Will be removed” = associated jobs not both matched and active
  - “Retained” = associated jobs both matched and active
- If exact counts are unavailable, do not fabricate counts. Use existing “Linked jobs”, “Tracked jobs”, and “Runs” cards with updated explanatory text.

### Cleanup explanation block
- Component: existing `.stack-list.delete-impact-copy` or paragraphs inside panel
- Recommended copy variants:
  - With counts: “{N} job(s) will be removed from Jobs, Dashboard, reminders, and digests immediately after deletion while physical cleanup finishes in the background.”
  - With retained jobs: “{N} matched active job(s) will remain visible if they match your filters. Their source will be treated as deleted and cannot be run again.”
  - No linked jobs: “No linked jobs were found. Deleting this source only removes the source configuration and future ingestion access.”

### Success alert after deletion
- Component: existing `ui.alert(level, message)` with `level='success'` or `level='info'`
- Recommended copy:
  - “Source deleted. Job cleanup has started; non-retained jobs from this source are hidden from Dashboard and Jobs now. Matched active jobs may remain.”

### Deleted source badge/label for retained job provenance
- Component: existing badge pattern or muted text
- Recommended label: “Deleted source”
- Tone: muted/neutral, not danger, because retained jobs are intentionally preserved.
- Do not make the badge clickable.

## 7. Interaction Behavior

### Expected delete flow
1. User opens Sources list or Source detail.
2. User selects “Delete” / “Delete source”.
3. Confirmation page opens.
4. User reviews cleanup warning and impact summary.
5. User clicks “Delete source”.
6. Button enters submitting/loading state if supported by current form behavior.
7. Server confirms deletion and redirects to an appropriate page, preferably Sources list.
8. A success alert appears with cleanup messaging.
9. Deleted source disappears from active source list, source filter dropdowns, source health action lists, and run actions.
10. Dashboard and Jobs list exclude non-retained jobs immediately.
11. Matched active retained jobs remain visible when they match active filters.

### Filters
- If a user had a deleted source selected in the URL (`/jobs?source_id=<deleted>`), the source filter must not retain that deleted option.
- Preferred behavior: ignore the deleted source filter and show current valid results with either:
  - an info alert: “That source was deleted, so the source filter was cleared.”, or
  - source select reset to “All sources”.
- Do not show a disabled deleted source option in normal filters.

### Direct navigation to deleted job detail
- Use normal not-found behavior. Do not render stale job content or a custom recovery flow.

### Cleanup in progress
- The UI may mention cleanup is in progress/queued via flash after deletion.
- Do not require the user to monitor cleanup or manually retry from normal product surfaces.
- Do not block navigation while cleanup is pending.

## 8. Component States

### Delete confirmation page
- Default: source name, warning, impact summary, Delete and Cancel actions visible.
- Hover: existing button/link hover behavior.
- Focus: existing `:focus-visible` outline; Delete and Cancel must be keyboard reachable.
- Active/submitting: if implemented, disable the Delete button after submit and update text to “Deleting…” to prevent duplicate submission.
- Disabled: Delete button should only be disabled while submit is in progress, not because cleanup counts are unavailable.
- Loading: no full-page loader required. Server-rendered form submission is acceptable.
- Empty/no linked jobs: show “No linked jobs found. No job cleanup is needed.”
- Success: redirect with success alert; source removed from lists.
- Error: if source deletion fails, stay on/return to confirmation or source detail with `.alert-error`: “Source could not be deleted. No jobs were changed.”

### Dashboard
- Default: stat cards and recent job lists exclude non-retained jobs from deleted sources.
- Loading: existing page load only; no skeleton required.
- Empty after cleanup: use existing empty states. If all jobs were removed but sources remain, “No jobs yet” copy is acceptable, but preferred contextual copy is “No reviewable jobs remain after source cleanup. Run an active source to add new jobs.”
- Error: if dashboard query fails, use existing error handling; do not expose cleanup internals to the end user.

### Jobs list
- Default: source filter lists non-deleted sources only; table/cards exclude non-retained jobs from deleted sources.
- Empty after source deletion/filter reset: existing empty state is acceptable. Preferred copy if a cleanup flash is present: “No jobs match the current view. Jobs from the deleted source were removed unless they were matched and active.”
- Retained job row: displays as a normal matched active job. If source name is displayed and refers to the deleted source, append neutral text “Deleted source” where feasible.
- Error: stale bookmarked job detail returns normal not-found.

### Retained job source evidence
- Default: show source provenance as historical information.
- Hover/focus: external posting link follows existing link styling.
- Disabled/no action: no edit/run/source details link for deleted source.
- Empty: if source links were cleaned up, show existing “No source provenance records available.”

## 9. Responsive Design Rules

- Preserve existing breakpoints:
  - `max-width: 980px`: grids reduce to two columns.
  - `max-width: 720px`: grids reduce to one column; jobs table hides and mobile cards show.
- Delete confirmation impact cards should follow `.import-summary-grid` behavior: 4 columns desktop, 2 columns tablet, 1 column mobile.
- Action rows must wrap using `.button-row-wrap`; destructive and cancel buttons should remain full tap targets.
- Do not add horizontal-only cleanup status content. All explanatory text must wrap within the panel.
- On mobile job cards, if a retained deleted-source label is shown, place it in the muted metadata line after source name or in the existing badge stack.

## 10. Visual Design Tokens

Use existing tokens from `app/web/static/styles.css`:

- Background: `--bg #f5f7fb`
- Surface: `--surface #ffffff`
- Muted surface: `--surface-muted #eef2f7`
- Text: `--text #162032`
- Muted text: `--text-muted #5d6b82`
- Border: `--border #d7dfeb`
- Primary/info: `--primary #3157d5`
- Matched/success: `--matched #1f8f5f`
- Review/warning: `--review #a66a00`
- Rejected/danger: `--rejected #b53737`
- Radius: `--radius 14px`
- Shadow: `--shadow 0 10px 28px rgba(15, 23, 42, 0.06)`

Tone guidance:
- Confirmation warning: danger callout (`callout-danger`) because deletion is permanent.
- Post-delete success: success alert with explanatory text.
- Cleanup-in-progress information: info alert/callout if shown separately.
- Retained deleted-source provenance: muted or neutral badge, not red.

## 11. Accessibility Requirements

- Destructive warning must be text, not color-only. Include explicit words such as “permanently removes” and “Only matched active jobs are retained.”
- Global deletion success message should use existing alert role behavior (`role="status"`) so screen reader users receive feedback after redirect.
- If an error occurs, use `.alert-error`; error copy must state that no jobs were changed if delete failed.
- Delete and Cancel controls must be reachable by keyboard and have visible focus outlines.
- The Delete button label must remain explicit: “Delete source”; avoid ambiguous labels like “Confirm”.
- If submit-loading is added, expose the state via button text (“Deleting…”) and `disabled` to prevent duplicate submissions.
- Source filter reset after a deleted-source URL must be communicated with visible text or alert; do not silently leave screen reader users with changed results and no context.
- Badge/label “Deleted source” must have sufficient contrast and should not rely on color alone.
- External posting links on retained jobs must preserve `target="_blank"` and `rel="noreferrer"` patterns where already used.

## 12. Edge Cases

- Source has zero linked jobs: deletion succeeds; show no cleanup error; confirmation says no job cleanup is needed.
- Source has only matched active jobs: source disappears from source management/filters; jobs remain visible; source provenance may be labeled deleted.
- Source has mixed classifications/states: only matched active jobs remain; all others disappear immediately from dashboard/jobs/counts.
- Source has tracked jobs that are not matched active: tracking/reminder status does not protect them; avoid copy implying tracked jobs are always preserved.
- Job linked to multiple sources: if it is not matched active and is associated with the deleted source, it should not appear in normal surfaces after deletion per product assumption.
- Stale browser submits deletion twice: show normal not-found/already-deleted behavior; do not show duplicated cleanup UI.
- Cleanup fails after source deletion: source remains deleted; normal user surfaces continue hiding non-retained jobs. No normal-user retry control.
- User opens dashboard/jobs immediately after deletion: stale non-retained jobs must already be absent.
- User opens bookmarked deleted job detail: normal not-found response.
- Deleted source in source filters: remove from dropdown; clear/ignore stale filter parameter.

## 13. Developer Handoff Notes

- Update existing copy in `app/web/templates/sources/delete_confirm.html`; do not introduce a modal unless product later requests one.
- Replace current preservation-oriented copy (“Historical jobs… are preserved”, “Tracked jobs… are preserved”) because it conflicts with the new cleanup rule.
- Recommended success flash copy: “Source deleted. Job cleanup has started; non-retained jobs from this source are hidden from Dashboard and Jobs now. Matched active jobs may remain.”
- Do not implement client-side filtering as the source of truth. Server queries must suppress non-retained pending-deletion jobs for dashboard counts, dashboard job previews, jobs list, reminders, digests, and job detail access.
- Do not add deleted sources to normal source filters, ingestion controls, source health actions, or run buttons.
- Do not show a progress bar, cleanup queue monitor, undo, restore, archive option, or configurable retention policy; these are out of scope.
- If pre-delete retention/removal counts are expensive or unavailable, avoid exact count promises and use rule-based copy.
- Retained matched active jobs should keep normal job actions (view, save/keep if applicable, tracking status) unless other business rules disable them.
- If provenance for a deleted source is shown on retained job detail, it is historical only. Do not link to source edit/run/delete actions for that source.
