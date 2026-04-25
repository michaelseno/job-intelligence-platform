# Design Specification

## 1. Feature Overview

Feature: Hide Rejected Job Openings

The main user-facing Jobs display must become an actionable queue that shows jobs whose current display classification is `matched`, `review`, or otherwise not explicitly `rejected`. Jobs classified as `rejected` are hidden from the Jobs list, Jobs filter options, dashboard actionable summaries, and dashboard job preview cards.

Rejected jobs are not deleted, archived, or reclassified by this feature. Direct access to a rejected job detail URL is unchanged: if the job is otherwise visible under existing source-delete rules, `/jobs/{job_id}` may still render the detail page.

Primary affected surfaces:
- `/jobs` HTML Jobs list and its JSON/API equivalent
- Jobs list bucket filter
- Dashboard actionable job summary counts and matched/review preview cards
- Duplicate template paths currently present in the repository:
  - `app/web/templates/jobs/list.html`
  - `app/templates/jobs/list.html`
  - `app/web/templates/dashboard/index.html`
  - `app/templates/dashboard/index.html`

Out of scope:
- A rejected-jobs management page
- A “show rejected” toggle
- Any deletion, archive, restore, or export flow
- Changing classification logic or detail-page access control

## 2. User Goal

As a job seeker reviewing opportunities, I want the main Jobs page and dashboard to show only actionable jobs, so I can focus on matches and jobs that still need review without repeatedly scanning opportunities the system has already rejected.

## 3. UX Rationale

- The main Jobs list is a triage workspace. Rejected jobs are non-actionable in this workflow and should not compete visually with matched or review jobs.
- Hiding rejected jobs at the query/data layer keeps counts, search results, and future pagination consistent with what the user sees.
- Removing the visible `Rejected` bucket option avoids suggesting that rejected jobs are available as a normal main-page filter.
- Existing UI patterns should remain stable: this feature is a visibility and copy change, not a redesign of job cards, tables, badges, or tracking controls.

## 4. Information Hierarchy

### Jobs page
1. Page header: “Jobs” with existing triage description.
2. Filter form:
   - Search jobs
   - Automated bucket / classification filter with actionable options only
   - Tracking status
   - Source
   - Sort
   - Apply and reset controls
3. Results summary count based only on visible actionable jobs.
4. Job table on desktop and job cards on mobile.
5. Empty state when no visible actionable jobs match the current view.

### Dashboard
1. Page header and primary actions remain unchanged.
2. Actionable summary cards/counts:
   - Matched
   - Review / Needs review
   - Other non-job cards such as reminders and sources remain unchanged.
3. Recent matched jobs preview.
4. Recent review jobs / jobs needing attention preview.
5. Existing reminders/source health sections remain outside this feature unless they intentionally reuse the main display query.

## 5. Layout Structure

### Jobs filter panel

Keep the existing form layout and responsive behavior. Only update bucket filter options/copy.

Recommended desktop/web-template structure:

```text
Panel
└─ Filters form
   ├─ Search jobs input
   ├─ Automated bucket select
   │  ├─ All actionable
   │  ├─ Matched
   │  └─ Review
   ├─ Tracking status select
   ├─ Source select
   ├─ Sort select
   └─ Apply filters / Reset filters
```

If minimal copy change is preferred, `All buckets` may remain, but `All actionable` is recommended because the default no longer represents all stored job buckets.

### Jobs results

Keep the existing table/card layouts. Rejected rows/cards should not be rendered in the Jobs list at all, so rejected-specific muted row/card styling should not be observable on this surface after implementation.

Desktop table columns remain unchanged unless the active template differs:
- Role
- Automated bucket / Status
- Tracking
- Score or last updated depending on template
- Reason/source metadata as currently implemented
- Actions

Mobile cards remain unchanged in structure and should show only non-rejected jobs.

### Dashboard summaries

Preferred dashboard structure:
- Do not show a visible `Rejected` stat card in the user-facing dashboard if the card represents the actionable Jobs surface.
- Keep Matched and Review/Needs review cards and link them to `/jobs?bucket=matched` and `/jobs?bucket=review`.
- Existing non-actionable operational cards such as Pending reminders, Active sources, Saved needing action, and Applied follow-up may remain if already present.

Backward-compatible fallback if the API/template contract requires `summary.rejected` temporarily:
- The value must be `0` after main-display filtering.
- Avoid linking users to `/jobs?bucket=rejected` from normal dashboard UI.
- If the card cannot be removed immediately, label it in a way that does not imply a browsable queue, but removal is strongly preferred for this feature.

## 6. Components

### Bucket select

Component: existing native `<select>`.

Required options on main Jobs page:
- `value=""`: “All actionable”
- `value="matched"`: “Matched”
- `value="review"`: “Review”

Do not include:
- `value="rejected"`: “Rejected”

If a bookmarked URL contains `?bucket=rejected`, the select should not display a selected rejected option. Preferred UI state is defaulting the select visually to “All actionable” while the result set remains empty due to backend compatibility behavior. Do not add a hidden or disabled rejected option.

### Results summary

Component: existing `.results-summary` paragraph when present.

Recommended copy:
- `{{ jobs|length }} actionable job(s) found.`

Acceptable existing copy may remain if it does not imply rejected jobs are included. Avoid “all jobs found” wording.

### Job rows/cards

Component: existing table rows and `.job-card` mobile cards.

Behavior:
- Render matched, review, null, and unknown non-rejected jobs according to backend eligibility rules.
- Do not render rejected rows/cards on the main Jobs page.
- Existing rejected badge tone may remain available for detail/admin/debug surfaces; do not remove global badge styling.

### Dashboard stat cards

Component: existing `ui.stat_card` or `.stat-card`.

Expected user-facing cards:
- Matched: count of visible actionable matched jobs.
- Review / Needs review: count of visible actionable review jobs.
- Non-job workflow cards unchanged.

Do not present a clickable Rejected dashboard card that routes to `/jobs?bucket=rejected`.

### Empty state

Component: existing `ui.empty_state`.

Jobs page preferred copy:
- Title: “No actionable jobs found”
- Body: “Matched and review jobs that meet your filters will appear here. Rejected jobs are hidden from this main view.”
- CTA: existing `/sources` action such as “Open Sources” or “Manage sources” when appropriate.

If product prefers not to mention rejected jobs in empty states, the existing copy is acceptable:
- “No jobs match the current view”
- “Either ingestion has not produced jobs yet, or the current filters narrow the list to zero results.”

Dashboard all-hidden/no-actionable state preferred copy:
- Title: “No actionable jobs yet”
- Body: “Matched and review jobs will appear here after ingestion. Rejected jobs are hidden from the dashboard queue.”

## 7. Interaction Behavior

### Default Jobs page load
1. User opens `/jobs`.
2. Bucket select defaults to “All actionable”.
3. List contains eligible non-rejected jobs only.
4. Results summary count equals the number of rendered jobs.
5. Rejected jobs are not visible and cannot be selected through the bucket filter.

### Filtering
- Search, tracking status, source, and sort operate only within the non-rejected main-display set.
- Selecting “Matched” shows matched jobs only, excluding rejected jobs regardless of other filters.
- Selecting “Review” shows review jobs only, excluding rejected jobs regardless of other filters.
- Reset filters returns to `/jobs` with “All actionable”.
- A manually entered `/jobs?bucket=rejected` URL returns an empty list/no-results state and should not reveal rejected jobs.

### Dashboard summaries and previews
- Matched and review counts use the same actionable main-display eligibility as `/jobs`.
- Recent matched/review preview cards must not include rejected jobs.
- Links from dashboard should target only supported visible filters: `/jobs`, `/jobs?bucket=matched`, `/jobs?bucket=review`, and existing tracking/source routes.

### Classification changes
- If a visible review or matched job is reclassified as rejected, it remains on a currently loaded server-rendered page until refresh/reload unless an existing real-time mechanism already updates it.
- After refresh/reload, the job disappears from Jobs list and dashboard actionable summaries.
- If a rejected job is later reclassified as review or matched, it appears after refresh/reload when it satisfies other active filters.

### Detail access
- Clicking from the main list cannot navigate to a rejected job because rejected jobs are absent.
- Direct navigation to `/jobs/{job_id}` for a rejected job is unchanged by this feature. If the detail route currently allows the job under source-delete visibility rules, show the detail page as before.
- The detail page may continue to show a Rejected badge/status for that job. This is not a main-page filter option.

## 8. Component States

### Bucket select
- Default: “All actionable” selected; Matched and Review available.
- Hover: native browser hover behavior; no custom visual change required.
- Focus: visible focus ring using existing form control focus styles; label must remain associated with select.
- Active/open: native select menu displays only actionable options.
- Disabled: not disabled under normal conditions.
- Loading: no special loading state for server-rendered form; page reload is acceptable.
- Error: if backend rejects an invalid bucket in the future, display normal form/list error handling. Current technical design prefers empty results for `bucket=rejected`, not a 400.

### Jobs list
- Default: renders eligible non-rejected jobs.
- Empty: use empty state; do not show an error when all stored jobs are rejected.
- Loading: full page reload only; no skeleton required.
- Success: results and counts match current filters after refresh.
- Error: use existing page-level error handling; do not expose query internals.

### Job row/card
- Default: normal row/card styling for matched/review/non-rejected jobs.
- Hover/focus: existing link/button hover and focus states.
- Active: existing button/form active states.
- Disabled: existing disabled state for form actions if present.
- Rejected state: not rendered in the main list. Rejected muted row/card styling may remain dead code or be used elsewhere, but visual regression tests should expect no rejected row/card on `/jobs`.

### Dashboard cards
- Default: matched/review counts exclude rejected jobs.
- Empty: matched/review cards may display `0`; preview sections show existing muted/empty messages.
- Hover/focus: stat card links follow existing link focus/hover behavior.
- Error/loading: no new state required.

## 9. Responsive Design Rules

- Preserve existing breakpoints and server-rendered behavior.
- Desktop Jobs page continues to use table layout where currently implemented.
- Mobile Jobs page continues to use card layout where currently implemented.
- Removing the Rejected option must not change filter wrapping behavior; the filter row should simply have a shorter select menu.
- Empty-state copy must wrap cleanly within the existing panel/surface width.
- Dashboard stat grid should reflow using existing grid behavior. If removing the Rejected card creates an uneven row, do not add placeholder cards; allow the grid to naturally reflow.

## 10. Visual Design Tokens

Use existing design tokens and component styles. No new colors, spacing scales, or typography are required.

Known existing token guidance from current UI specs/styles:
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

Rejected/danger styling may continue to exist for detail pages and non-main surfaces, but it should not appear in the main Jobs list or dashboard actionable summaries as part of this feature.

## 11. Accessibility Requirements

- The bucket select must retain an accessible label:
  - Visible label `Automated bucket` in `app/web/templates/jobs/list.html`, or
  - `.sr-only` label in `app/templates/jobs/list.html`.
- Do not rely on color alone to communicate status; matched/review badges must retain text labels.
- Removing Rejected from the select must not leave an orphaned selected value or blank unlabeled control for screen reader users.
- Empty states must use plain, non-alarming language. All-rejected data is a valid no-results condition, not an error.
- Keyboard users must be able to tab through search, bucket, tracking, source, sort, Apply, and Reset in the existing logical order.
- Dashboard stat card links must remain keyboard focusable and have descriptive text, e.g., “Matched” and “Review”.
- If a rejected job detail page is directly accessed, its status badge should remain text-based so assistive technology can identify the job state.

## 12. Edge Cases

- All stored jobs are rejected: Jobs page shows empty state; dashboard matched/review counts are `0`; no error language.
- Search term matches only rejected jobs: Jobs page shows empty state; rejected matches remain hidden.
- Active source/company/location/tracking filters match only rejected jobs: empty state; do not reveal rejected jobs.
- User manually enters `/jobs?bucket=rejected`: rejected jobs remain hidden; UI does not show Rejected as a selectable option.
- Null/missing classification: per technical design, remains visible for MVP unless product later decides strict matched/review-only display.
- Unknown non-`rejected` classification: remains visible for backward compatibility per technical design; badge rendering should use existing fallback tone.
- Multiple classification records: UI uses the backend-provided current/latest display classification; do not infer status client-side.
- Classification changes while viewing list: server-rendered UI may remain stale until refresh/reload.
- Rejected tracked jobs or reminders: outside this feature unless they are rendered through the main Jobs display/dashboard actionable query. Do not silently change reminder/tracking-specific surfaces without product confirmation.
- Rejected job detail URL: direct access unchanged if existing detail visibility permits it.

## 13. Developer Handoff Notes

- Do not implement client-side hiding as the primary behavior. The backend/query layer must exclude rejected jobs before counts and any future pagination.
- Update both Jobs list template paths if both remain in use or tests cover both:
  - `app/web/templates/jobs/list.html`
  - `app/templates/jobs/list.html`
- Remove/suppress `Rejected` from the main Jobs bucket selector in both template variants.
- Prefer changing the all-option label from “All buckets” to “All actionable”. If this is too broad for the current release, keep “All buckets” only if tests/product accept that wording.
- Dashboard actionable summaries/previews should use the same non-rejected eligibility as `/jobs`.
- Remove the clickable dashboard Rejected stat card from user-facing UI where feasible. If retained for contract compatibility, it must show `0` and should not link to `/jobs?bucket=rejected`.
- Do not remove global rejected badge styles because rejected status may still appear on detail, admin, debug, audit, or historical surfaces.
- Visual regression expectations:
  - Jobs filter menu contains All actionable/Matched/Review only.
  - No row/card with rejected badge, `.row-muted`, or `.job-card-muted` appears on `/jobs` for rejected data.
  - Jobs empty state appears when fixtures contain only rejected jobs.
  - Dashboard matched/review counts exclude rejected fixtures.
  - Dashboard previews contain no rejected cards.
  - Direct rejected job detail, if tested, still renders according to existing detail behavior.
- Content regression expectations:
  - Counts should describe visible/actionable jobs, not total stored jobs.
  - Empty states should not imply records were deleted or that an error occurred.
  - Avoid adding “deleted” language for rejected jobs; they are hidden from the main display only.

### Explicit assumptions

- `JobPosting.latest_bucket` or equivalent backend-provided current/latest classification is the source of truth for display status.
- Null/unknown non-rejected jobs remain visible for MVP, matching the technical design.
- Main display means `/jobs` and dashboard actionable job summaries/previews, not every route that can show a job.
- Direct detail access for rejected jobs is unchanged by this feature.
