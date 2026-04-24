# Design Specification

## 1. Feature Overview
Add source maintenance UX that lets users edit an existing non-deleted source and safely delete a source from active configuration.

This feature extends the current server-rendered Sources area and must fit existing Jinja template, PRG, and form/error patterns already used in `app/web/templates/sources/index.html` and related pages.

Primary surfaces in scope:
- Sources list page: `GET /sources`
- Source detail page: `GET /sources/{source_id}`
- New edit page: `GET/POST /sources/{source_id}/edit`
- New delete confirmation page: `GET/POST /sources/{source_id}/delete`

Assumptions:
- Deleted sources are soft-deleted and excluded from normal management routes.
- Edit uses a dedicated page, not inline edit and not a modal.
- Delete uses a dedicated confirmation page, not an in-row confirmation.

## 2. User Goal
- Correct source configuration mistakes without recreating the source.
- Change `is_active` without deleting history.
- Remove an unwanted source from active configuration with clear impact messaging.

## 3. UX Rationale
- **Dedicated edit page** is preferred over inline or modal editing because the source form has multiple fields, conditional validation, and must support robust server-side error rendering.
- **Dedicated delete confirmation page** is preferred over a modal because the action is destructive, needs impact details, and should support full page reload/refresh safely.
- **Edit and delete entry points on both list and detail** reduce navigation friction and satisfy product requirements.
- **Inactive and deleted must remain visually distinct**: inactive is manageable; deleted is removed from management UI.

## 4. Information Hierarchy
### Sources list page
1. Page header and existing create/import tools
2. Configured sources table
3. Per-source status and actions

Per row priority:
1. Source name
2. Company name (if present)
3. Source type
4. Status (`Active` / `Inactive`)
5. Health / last run context
6. Actions: `Edit`, `Delete`, `Run ingestion`

### Source detail page
1. Page header with source name and primary actions
2. Source metadata
3. Operational health summary
4. Run history

### Edit page
1. Page title and short instruction
2. Page-level validation summary if present
3. Editable form fields
4. Save / cancel actions

### Delete confirmation page
1. Destructive title naming the source
2. Impact summary
3. Warning copy explaining effect
4. Delete / cancel actions

## 5. Layout Structure
### A. Sources list updates (`/sources`)
- Keep current overall page structure unchanged.
- In the configured sources table:
  - Add a `Status` column after `Type`.
  - Keep `Health`, `Last run`, `Jobs fetched`.
  - Replace single-action cell with an `Actions` stack or wrap row containing:
    - secondary link/button: `Edit`
    - danger-styled link/button: `Delete`
    - secondary button: `Run ingestion`
- For inactive sources, show status badge/text in the new status column and optionally repeat a muted `Inactive` subtitle under the source name on narrow layouts.

Recommended desktop column order:
`Source | Type | Status | Health | Last run | Jobs fetched | Actions`

### B. Source detail updates (`/sources/{id}`)
- Add page-header actions using existing `ui.page_header(..., actions=...)` pattern.
- Header actions order:
  1. `Edit source`
  2. `Delete source`
  3. `Run ingestion`
- In metadata panel, add:
  - `Status: Active/Inactive`
  - `Notes` if present, else `—`
- If inactive, show a non-error warning/callout near the top of the detail page: `This source is inactive. It remains editable but cannot be run for ingestion.`

### C. Edit page (`/sources/{id}/edit`)
- Use a single main panel, reusing current source form field ordering from create.
- Suggested header:
  - Title: `Edit source`
  - Description: `Update source metadata and activation status. Changes apply to future source management and ingestion behavior.`
- Form fields in this order:
  1. Source name
  2. Source type
  3. Company name
  4. Source URL
  5. External identifier
  6. Adapter key
  7. Notes
  8. Active source checkbox
- Footer actions:
  - primary: `Save changes`
  - secondary link/button: `Cancel`
- Cancel returns to `/sources/{id}`.

### D. Delete confirmation page (`/sources/{id}/delete`)
- Use one focused panel, visually narrower than the main list page if feasible, but may reuse standard panel width for simplicity.
- Structure:
  1. Title: `Delete source`
  2. Intro sentence naming the source
  3. Warning callout
  4. Impact summary list/cards
  5. Explicit consequence copy
  6. Action row
- Action row:
  - primary destructive button: `Delete source`
  - secondary link/button: `Cancel`
- Cancel returns to `/sources/{id}`.

## 6. Components
### 6.1 Status badge
Use existing badge system if possible.

Required statuses:
- `Active`
- `Inactive`

Implementation note:
- Current badge macro is value-driven and does not yet include a neutral status family. Frontend may either:
  - extend badge styles for status badges, or
  - render muted inline text if badge support is not added in this pass.
- Preferred outcome: add explicit status badge styling for consistency.

### 6.2 Source actions cluster
- Actions must be keyboard reachable in logical order.
- `Delete` must be visually distinct from non-destructive actions.
- Do not place delete as a plain text link with equal visual weight to `Edit`; it should be recognizable as destructive.

### 6.3 Edit form
- Reuse existing field styling, help text style, validation placement, and grid layout.
- Form should be prefilled from current persisted values.
- For HTML flow, all editable fields are posted on save.

### 6.4 Validation summary
- If `form_errors.__all__` exists, render a top-level alert above the form.
- If multiple field errors exist, page-level summary copy should say `Review the highlighted fields and try again.` before field messages.

### 6.5 Delete impact summary
Required content blocks:
- Source name
- Run history state
- Linked jobs state
- Tracked jobs state if available

Preferred presentation:
- 3 compact stat cards or a structured list:
  - `Runs: <count>`
  - `Linked jobs: <count>`
  - `Tracked jobs: <count>`
- Follow with plain-language summary sentences.

## 7. Interaction Behavior
### 7.1 Entry points
#### From sources list
- `Edit` opens `/sources/{id}/edit`.
- `Delete` opens `/sources/{id}/delete`.
- `Run ingestion` remains a direct form submit.

#### From source detail
- Same actions available in header action group.

### 7.2 Edit flow
1. User opens edit page from list or detail.
2. Page loads with current values.
3. User changes one or more fields.
4. User clicks `Save changes`.
5. On success:
   - server redirects to `/sources/{id}`
   - success flash appears
   - updated values are visible immediately
6. On validation error:
   - same edit page re-renders
   - submitted values remain populated
   - field and/or page-level errors appear

### 7.3 Delete flow
1. User opens delete confirmation page from list or detail.
2. Page shows source name and impact summary.
3. User chooses:
   - `Cancel` -> return to detail page without changes
   - `Delete source` -> submit delete
4. On success:
   - server redirects to `/sources`
   - success flash appears
   - deleted source no longer appears in default source lists or selectors

### 7.4 Not-found / stale interaction handling
- If user opens an edit/delete URL for a nonexistent or already deleted source, show normal 404 behavior.
- If a stale page submits delete after the source was already deleted, backend returns 404; QA should verify app does not render a misleading success state.

### 7.5 Inactive behavior
- User may set `Active source` unchecked and save.
- Inactive source remains visible in list/detail.
- Inactive source shows clear inactive status.
- Run action should be hidden or disabled for inactive sources in HTML surfaces.

Preferred UI decision:
- **Disable or replace Run action for inactive sources rather than leaving it enabled and relying only on backend rejection.**
- If disabled buttons are not ideal inside current table patterns, replace with muted text: `Inactive — cannot run`.

## 8. Component States
### 8.1 Edit / Delete action links or buttons
- **Default:** visible, clearly labeled.
- **Hover:** underline for links or stronger border/background for buttons.
- **Focus:** use existing focus ring.
- **Active:** standard pressed state.
- **Disabled:** only applicable if source is inactive for run, not for edit/delete.

### 8.2 Form fields
- **Default:** prefilled current values.
- **Hover:** browser default acceptable.
- **Focus:** existing visible outline.
- **Active/input:** normal typed state.
- **Disabled:** not expected for editable fields in MVP.
- **Loading:** submit button changes to `Saving...` and becomes temporarily disabled if frontend enhancement is added; otherwise server-rendered postback is acceptable.
- **Empty:** empty optional fields show blank inputs; required fields remain populated unless the saved value is actually blank in edge cases.
- **Success:** redirect with success flash.
- **Error:** field-level message under input; page-level alert for cross-field or duplicate issues.

### 8.3 Delete confirmation CTA
- **Default:** destructive emphasis.
- **Hover:** stronger danger emphasis.
- **Focus:** visible outline with adequate contrast.
- **Active:** pressed state.
- **Disabled:** only during submit if client-side prevention of double-submit is added.
- **Loading:** label may become `Deleting...` if enhanced.
- **Success:** redirect to sources list with success flash.
- **Error:** for 404 after stale submit, standard not-found response; for unexpected failure, show error flash/message if implementation supports it.

### 8.4 Empty and informational states
- **Delete impact with no history:** explicitly state `No run history found.` and `No linked jobs found.` instead of showing ambiguous zeros only.
- **Notes empty on detail:** show `—`.

## 9. Responsive Design Rules
- Reuse current responsive breakpoints in `styles.css`.
- On <=980px:
  - action groups may wrap onto multiple lines
  - edit form keeps two-column layout where available
- On <=720px:
  - edit form becomes single column
  - source detail header actions stack vertically
  - list-page action cell should stack `Edit`, `Delete`, and run control in a readable order
  - avoid requiring horizontal scroll solely to reach edit/delete actions; if table remains scrollable, ensure actions remain within the row and are not visually truncated

Mobile order recommendation for action stack:
1. `Edit`
2. `Delete`
3. run state/action

## 10. Visual Design Tokens
Use existing tokens in `app/web/static/styles.css`.

### Existing tokens to reuse
- Background: `--bg`
- Surface: `--surface`
- Border: `--border`
- Primary action: `--primary`
- Warning/review: `--review`
- Destructive/error: `--rejected`
- Text: `--text`
- Muted text: `--text-muted`
- Radius: `--radius`
- Shadow: `--shadow`

### New/extended styling guidance
- Delete button/link should use the destructive color family (`--rejected`).
- Inactive status should not reuse destructive red; prefer muted or warning-adjacent styling to avoid conflating inactive with deleted/error.
- Success and validation flashes should keep existing alert styling.

## 11. Accessibility Requirements
- All actions must have explicit text labels; do not use icon-only edit/delete controls in this pass.
- Keyboard tab order must follow reading order and keep destructive action after edit.
- Focus indicators must remain visible on links, buttons, inputs, and checkbox.
- Field errors must be programmatically associated where practical:
  - add `aria-invalid="true"` on invalid fields
  - connect errors/help text with `aria-describedby` when implemented
- Page-level alert for validation should be announced clearly; use existing alert pattern and ensure error summary is near the top of the form.
- Delete page title and warning copy must be understandable out of context for screen-reader users.
- Do not rely on color alone for inactive/destructive distinctions; use text labels like `Inactive` and `Delete source`.
- If run action is disabled for inactive sources, provide explanatory text in adjacent copy so the reason is available to all users.
- External base URL on detail page should keep accessible link text by showing the full URL or a descriptive label paired with visible URL.

## 12. Edge Cases
- Editing only `notes` succeeds.
- Editing only `is_active` succeeds.
- Changing `source_type` triggers different required fields and may show new validation errors.
- Duplicate detection error appears when dedupe identity matches another non-deleted source.
- Source has no runs: delete page should still feel complete, not empty.
- Source has linked jobs and/or tracked jobs: delete page must surface counts and warning language.
- Stale edit form overwrites a newer change because MVP is last-write-wins; frontend should not invent unsaved-conflict UI.
- Deleted source should not appear in jobs source filter dropdown after deletion.
- Historical job pages may still show deleted source names, but must not expose edit/delete/run actions there.

## 13. Developer Handoff Notes
### Screen inventory
- Update: `app/web/templates/sources/index.html`
- Update: `app/web/templates/sources/detail.html`
- Add: `app/web/templates/sources/edit.html`
- Add: `app/web/templates/sources/delete_confirm.html`

### Copy guidance
#### Buttons / links
- List row: `Edit`, `Delete`, `Run ingestion`
- Detail header: `Edit source`, `Delete source`, `Run ingestion`
- Edit submit: `Save changes`
- Edit cancel: `Cancel`
- Delete submit: `Delete source`
- Delete cancel: `Cancel`

#### Success flashes
- Edit success: `Source updated successfully.`
- Delete success: `Source deleted. It has been removed from active configuration and future ingestion.`

#### Edit helper / validation copy
- Page intro: `Update source metadata and activation status.`
- Generic validation summary: `Source update failed. Review the highlighted fields and try again.`
- Duplicate error: `Another active source already uses this configuration. Update the fields or delete the other source first.`
- Inactive helper: `Inactive sources remain visible in source management but cannot be run.`

#### Delete confirmation copy
- Intro: `You are about to delete <source name>.`
- Warning body: `Deleting a source removes it from active configuration, hides it from default source lists and filters, and prevents future ingestion runs. Historical jobs and run records are preserved.`
- No history variant: `This source has no recorded runs and no linked jobs.`
- Has history variant: `This source has existing history that will remain visible in historical views.`
- Linked jobs warning: `Jobs already linked to this source will keep their historical source reference.`
- Tracked jobs warning: `Tracked jobs linked to this source are preserved, but the source itself cannot be restored from this flow.`

### Frontend behavior notes
- Reuse the existing create form markup structure for edit wherever possible to minimize divergence.
- For checkbox handling, preserve current HTML convention where checked means active.
- Add explicit inactive status rendering in both list and detail.
- Hide or disable run controls when `is_active` is false.
- Add a destructive button style if one does not already exist.
- Keep PRG on successful edit and delete.

### QA notes
- Verify edit and delete are available from both list and detail.
- Verify edit form prepopulation for all editable fields.
- Verify field errors, duplicate errors, and type-dependent required-field errors.
- Verify inactive sources remain visible but not runnable.
- Verify delete confirmation content for zero/non-zero runs, linked jobs, and tracked jobs.
- Verify deleted sources disappear from `/sources`, jobs source filter options, and future run flows.
- Verify job detail and run history remain stable for historical records referencing deleted sources.
