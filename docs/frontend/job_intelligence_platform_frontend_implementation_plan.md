# Implementation Plan

## 1. Feature Overview

This document defines the frontend implementation plan for the Job Intelligence Platform MVP web experience. Scope is limited to frontend planning for a server-rendered FastAPI + Jinja application, with no SPA architecture and only minimal progressive enhancement where UX benefits are clear.

The frontend must support the full MVP review workflow described in the product, technical design, and UI/UX documents:
- source onboarding by manual form and CSV upload
- dashboard-first job review
- jobs list triage with filters and sorting
- job detail transparency and evidence inspection
- manual save/keep interactions that preserve automated classification
- tracking status management
- source health visibility
- digest, reminders, and workflow follow-up surfaces

The primary frontend goal is a clean, calm dashboard UI that clearly separates three concepts at all times:
- automated classification bucket
- user-managed tracking status
- source health / ingestion reliability

## 2. Technical Scope

### 2.1 Frontend Architecture
- Rendering model: FastAPI route handlers render Jinja templates as the primary UI response type.
- HTML is first-class; JSON endpoints are optional and only used for progressive enhancement where they reduce page friction.
- State-changing interactions remain server-authoritative.
- Filterable list views should prefer GET query parameters so page state is URL-addressable and shareable.
- No frontend classification, parsing, deduplication, or business-rule execution should be implemented in the browser.

### 2.2 Information Flow from Routes to Templates

Recommended route-to-template mapping:

| Route | Purpose | Template | Primary View Model Inputs |
|---|---|---|---|
| `GET /` or `GET /dashboard` | Landing dashboard | `dashboard/index.html` | summary counts, recent matched jobs, recent review jobs, reminders, source warnings, last ingestion summary |
| `GET /jobs` | Triaged jobs list | `jobs/list.html` | jobs rows, filter state, sort state, available sources, result count, empty-state context |
| `GET /jobs/{job_id}` | Job detail and transparency | `jobs/detail.html` | job summary, current automated decision, rule lists, evidence snippets, source metadata, tracking state, reminders metadata |
| `GET /sources` | Source onboarding hub / configured sources | `sources/index.html` | configured source list, health summary, form mode state, flash messages |
| `GET /sources/new` if retained | Manual source entry | `sources/manual_form.html` or shared include in `sources/index.html` | form fields, field errors, helper text |
| `GET /sources/import` if retained | CSV import page | `sources/import.html` or shared include in `sources/index.html` | upload state, import instructions, schema guidance, prior result summary |
| `GET /sources/{source_id}` | Source detail / run history | `sources/detail.html` | source metadata, last run summary, run history rows, warnings, actions |
| `GET /ops/sources` or `GET /source-health` | Source health overview | `ops/source_health.html` | source health rows, counts by health state, warning callouts |
| `GET /ops/runs` | Recent run history | `ops/run_list.html` | run rows, filters, summary counts |
| `GET /ops/runs/{run_id}` | Run detail | `ops/run_detail.html` | run metadata, counts, warning/error summaries, linked source/job context |
| `GET /tracking` | Tracking workflow page | `tracking/index.html` | tracked jobs rows, selected status filter, reminders/follow-up cues |
| `GET /digest/latest` | Daily digest | `notifications/digest.html` | digest metadata, grouped digest items |
| `GET /reminders` | Reminder queue | `notifications/reminders.html` | reminder rows/cards grouped by reminder type/status |

Recommended request flow pattern per page:
1. Route parses query params / form state.
2. Domain services return domain objects or command results.
3. Web-layer view models normalize data for presentation-only concerns.
4. Route renders Jinja template with page data + shared layout context.
5. Shared layout renders flash banners, nav state, and last-ingestion/system summary.

### 2.3 Template and Layout Structure

Recommended Jinja structure:

```text
app/web/templates/
  base.html
  includes/
    nav.html
    flash_messages.html
    page_header.html
    empty_state.html
    alert_banner.html
    badge.html
    stat_card.html
    filter_chip.html
    pagination.html
    sort_select.html
    table_wrapper.html
    form_field.html
    evidence_snippet.html
    decision_rule_row.html
    source_health_badge.html
    tracking_status_control.html
    keep_job_button.html
  dashboard/
    index.html
    _recent_job_list.html
    _reminder_queue.html
    _source_warning_list.html
  jobs/
    list.html
    _job_row.html
    _job_card.html
    detail.html
  sources/
    index.html
    manual_form.html
    import.html
    detail.html
    _source_row.html
    _import_results.html
  ops/
    source_health.html
    run_list.html
    run_detail.html
  tracking/
    index.html
  notifications/
    digest.html
    reminders.html
```

Layout decisions:
- `base.html` should own semantic page shell: header, nav, flash region, main content container, optional footer metadata.
- Shared partials should be used aggressively for badges, tables, alert banners, empty states, rule rows, and repeated job summaries.
- Page templates should stay focused on composition, not formatting logic.
- Repeated domain formatting should be handled in view models or Jinja helpers/filters, not inline template conditionals.

### 2.4 Page and Component Breakdown

#### Dashboard
Sections in implementation order:
1. Page header with Add Source and View Jobs actions
2. Summary stat cards: new matched, new review, saved needing action, applied follow-up
3. Recent matched preview
4. Recent review preview
5. Reminder queue
6. Source health warnings
7. Empty / no-ingestion callout

Reusable components:
- stat card
- compact job preview list/card
- reminder list block
- warning callout banner
- badge set for bucket/tracking/health

#### Jobs List
Components:
- page header
- filter form
- filter chips / segmented bucket controls
- source select
- tracking status select
- search input
- sort select
- reset filters action
- desktop table row partial
- mobile job card partial
- quick actions: View, Save / Keep Job, Update Tracking
- result summary / active filter summary

#### Job Detail
Sections:
1. job summary
2. decision summary
3. matched rules
4. rejected rules / negative signals
5. special handling notes, especially sponsorship ambiguity
6. evidence snippets
7. normalized description excerpt / content summary
8. source metadata and external posting link
9. tracking controls / reminder metadata in secondary column on desktop

Critical components:
- automated classification summary card
- evidence snippet blockquote-style component
- rule row with effect label and explanation
- manual keep action panel
- tracking status control

#### Source Add / Import
Recommended UI shape:
- one Sources hub page with segmented control or tabs for Manual Entry and CSV Import
- configured sources list below or in adjacent section
- forms remain server-rendered and independently submittable

Manual entry components:
- labeled form fields with helper text
- source type selector
- adapter/pattern selector or conditional helper area
- inline validation messages
- top-level error summary

CSV import components:
- upload field
- schema guidance block
- import result summary panel
- row-level validation table / list
- duplicate row summary

#### Source Health
Components:
- source health summary counts
- table with status, last run, fetched count, warning explanation, next action
- warning-highlighted rows
- links to source detail and run history

#### Tracking
Components:
- status chips/tabs
- search input
- optional urgency sort
- table on desktop / cards on mobile
- inline tracking update control
- reminder cue display

#### Digest and Reminders
Components:
- grouped lists by reason/type
- job summary rows/cards with bucket and tracking context
- action links back to job detail or tracking

### 2.5 Form Handling Strategy

General strategy:
- Use standard HTML forms with POST for create/update actions.
- Use PRG (Post/Redirect/Get) after successful mutations to avoid resubmission and preserve clean URLs.
- Use flash banners for success/error feedback.
- Keep server-side validation authoritative.
- Re-render invalid forms with field-level errors and a page-level error summary.

Recommended form handling by use case:

#### Manual Source Form
- Endpoint accepts standard form POST.
- Validation errors should return the same page with field error messages and retained user input.
- Required vs optional fields must be visually explicit.
- Source-type-specific helper text should appear without requiring JS.
- If JS is used, it should only improve field visibility or helper copy; server validation still determines correctness.

#### CSV Upload
- Use multipart form POST.
- Server returns import results with counts for imported, skipped, duplicate, invalid rows.
- Invalid rows should be displayed with row number, offending field(s), and human-readable message.
- If architecture later adds preview JSON endpoints, the default HTML upload flow remains the baseline.
- UI copy should explicitly state that CSV import creates new source records and skips duplicates; it does not update existing sources in MVP.

#### Save / Keep Job
- Prefer a small POST form button from list and detail views.
- Success returns to the same view context via redirect and flash message.
- If triggered from list views, preserve current query string when redirecting back.
- Button label/state should reflect whether job is already saved/tracked.
- If the backend reports no tracking status yet, UI should reflect that keep/save initialized tracking to `saved`.
- If a tracking status already exists, keep/save confirmation should avoid implying the tracking status changed.

#### Tracking Status Updates
- Primary no-JS baseline: select + submit button form per row/card.
- Progressive enhancement option: auto-submit on change after initial accessibility-safe version exists.
- Do not navigate user away from the current page after success.
- Preserve filter/sort query parameters on redirect.

#### Filter and Sorting Controls
- Use GET forms for jobs, tracking, source runs, and source health filters.
- Filter values should round-trip in query parameters and be reflected in controls on render.
- Provide explicit reset action that clears all parameters.

### 2.6 Interaction Model for Filtering, Sorting, and Job Actions

#### Filtering and Search
- Jobs list must support combinable filters for bucket, tracking status, source, and text search.
- Tracking page must support status-first filtering, with saved as default emphasized view.
- Source health may support health-state or recent-failure filtering if needed, but baseline can remain unfiltered in MVP.
- Active filters should be summarized near the result count.

#### Sorting
- Jobs list sort options:
  - newest / most recently ingested
  - highest score
  - title A-Z
  - company A-Z
- Tracking page sort options:
  - last updated
  - follow-up urgency (when reminder metadata exists)
- Source health sort options, if added later:
  - latest failure first
  - stale first
  - source name

#### Job Actions
- `View` navigates to job detail.
- `Save / Keep Job` is visible in both list and detail surfaces.
- `Update Tracking` is present in both list and detail surfaces.
- Automated classification remains visible after keep/save or tracking changes.
- Rejected jobs remain accessible, but table/card styling should de-emphasize them relative to matched/review.

#### Feedback Model
- Success: inline banner or flash message after mutation.
- Error: field errors for forms; page-level banner for action failures.
- Warning: source health anomalies, low-text jobs, removed postings, sponsorship ambiguity.

### 2.7 Minimal JavaScript Recommendations

Baseline rule: every key workflow must work without JavaScript.

Recommended JS usage only where it produces meaningful UX value with low complexity:
- auto-submit tracking status changes after accessible no-JS control exists
- preserve/open filter drawer state on mobile
- optional client-side file-name display for CSV upload input
- dismissible flash banners
- optional loading indicator on long-running submit buttons

Avoid for MVP:
- client-rendered routing
- client-side templating
- custom data grids
- heavy form state managers
- optimistic updates for server-authoritative actions

Implementation recommendation:
- if JS is introduced, keep it as a small progressive enhancement layer using vanilla JS or very lightweight utilities
- bind behavior via `data-*` attributes so templates remain readable
- do not make any page dependent on JS for core access or submission

### 2.8 CSS / Styling Approach

Recommended approach for FastAPI + Jinja:
- Use a small application stylesheet organized by layout, components, utilities, and state tokens.
- Prefer plain CSS or a very lightweight preprocessor only if already established; avoid introducing a front-end build-heavy stack unless the repo already mandates one.
- Design for server-rendered templates first: stable class names, reusable component classes, simple spacing and typography rules.

Suggested stylesheet structure:

```text
static/css/
  base.css
  layout.css
  components.css
  forms.css
  tables.css
  states.css
  utilities.css
```

Styling guidance:
- neutral background, white/near-white surfaces, restrained accent colors
- clear badge styles for classification, tracking, and health with distinct visual systems
- 4px or 8px spacing rhythm
- minimal shadows; rely mainly on borders and spacing
- one sans-serif family, small type scale, strong heading hierarchy
- consistent card and table padding to preserve calm dashboard feel

State styling requirements:
- visible hover, focus, active, disabled states for interactive controls
- text labels in addition to color cues for all badges and warnings
- alert variants for success, warning, error, info
- quoted evidence snippet style with muted background and readable contrast

### 2.9 Accessibility Guidance

Required baseline:
- semantic landmarks: header, nav, main, footer
- one logical `h1` per page; nested headings in order
- proper labels for all form controls
- inline validation tied to fields with `aria-describedby`
- page-level error summary linked to invalid fields where possible
- visible focus ring on all interactive elements
- keyboard-reachable tabs/segmented controls if implemented as real controls
- tables with proper headers and associations
- no reliance on color alone for bucket, tracking, or health state
- sufficiently descriptive button labels, especially for row actions

Specific accessibility notes by feature:
- filter chips should remain keyboard-operable and announced as selected/unselected
- quick-action forms in job rows should have accessible labels containing the job title when needed
- evidence snippets should use readable text contrast and not rely solely on quote styling
- mobile filter drawers, if added, must not create focus traps

### 2.10 Responsiveness Guidance

Desktop:
- use wide content layouts for dashboard, jobs, tracking, and source health
- jobs/tracking/source health default to table presentations
- job detail uses two-column layout when space permits

Tablet:
- summary cards collapse to two columns
- reduce low-priority columns before introducing excessive horizontal scrolling
- secondary metadata stacks below primary content on detail pages

Mobile:
- convert jobs and tracking tables to stacked cards
- collapse filters into expandable filter panel
- keep primary actions near page top and repeat at bottom on long detail pages if needed
- preserve title, bucket, tracking status, score, and primary action longest

Responsive priority order for column removal:
1. secondary source details
2. lower-priority timestamps
3. secondary reason text

### 2.11 Empty, Error, Warning, Loading, and Success States

Empty states to plan explicitly:
- dashboard: no sources yet; sources exist but no ingestion yet; filters produce no visible sections
- jobs: no jobs exist; current filters return none
- tracking: no jobs in selected status
- source health: no sources configured
- digest/reminders: no current digest/reminders available

Error and warning states:
- CSV row validation failures
- manual source form validation errors
- unsupported direct/custom source inputs
- source run failed / partial success / zero jobs warning
- limited source text for evidence generation
- removed or stale source posting retained for tracked job
- sponsorship ambiguity note forcing review treatment

Loading guidance for server-rendered UI:
- use submit-button loading text for long actions where helpful
- if no skeleton system is available, use clear loading copy rather than blank panels
- when showing historical data after a failed refresh, include warning banner explaining stale state

Success states:
- source created/imported successfully
- job saved/kept successfully
- tracking updated successfully
- reminder dismissed successfully

### 2.12 Frontend Testing and Validation Approach

Recommended validation layers:

#### Template and Rendering Validation
- basic route render tests for each page
- verify expected sections appear for core states
- verify badges/labels distinguish automated bucket vs tracking status vs health

#### Form and Interaction Validation
- POST/redirect/flash behavior tests for source create, CSV import, keep/save, and tracking updates
- invalid form submission tests with preserved input and visible errors
- query parameter tests for jobs/tracking filters and sorts

#### Accessibility-Oriented Validation
- template review for heading order, label presence, button text, table semantics, and focus visibility hooks
- optional automated checks if test tooling supports HTML assertions or aXe in end-to-end coverage

#### Responsive and Visual Review
- manual browser checks at desktop, tablet, and mobile widths
- validate table-to-card transitions for jobs/tracking
- verify badge readability and evidence snippet contrast

#### End-to-End Critical Flow Validation
- source add/import -> review success state
- dashboard with empty and populated states
- jobs filter + sort combinations
- save/keep from list and detail
- tracking update from list and detail
- source health warning surfacing

If frontend automation is established later, prioritize:
1. route rendering tests
2. form workflow integration tests
3. end-to-end smoke tests for key triage paths

### 2.13 Milestone-Level Frontend Execution Plan

This sequence aligns with the architecture implementation plan and keeps frontend dependencies realistic.

#### Milestone 0: Frontend Shell and Design Foundation
- create base layout, nav model, page header partial, flash banner partial
- establish CSS tokens, surface styles, badge system, table/card primitives
- define shared Jinja partial conventions and route-template contract

Frontend acceptance target:
- placeholder pages render within shared layout
- nav reflects main information hierarchy
- global feedback and empty-state patterns exist

#### Milestone 1: Source Management UI
- implement Sources page structure
- implement manual source form UX
- implement CSV import page/section with result summary design
- implement configured source list with basic health summary labels

Frontend acceptance target:
- source onboarding paths are clear and visually separated
- row-level import feedback pattern is defined
- validation/error patterns are usable without JS

#### Milestone 2: Dashboard Foundation
- implement summary cards and dashboard section layout
- implement recent matched/review preview components
- implement reminder and source-warning preview blocks
- define dashboard empty-state variants

Frontend acceptance target:
- dashboard works as daily command center
- no-data and no-ingestion states are understandable

#### Milestone 3: Jobs Triage UI
- implement jobs list filters, sort controls, result summary, and reset action
- implement desktop table row and mobile job card variants
- implement quick actions for view, save/keep, and tracking update

Frontend acceptance target:
- jobs can be triaged by bucket, source, tracking status, and search
- rejected jobs remain accessible but de-emphasized

#### Milestone 4: Job Detail Transparency UI
- implement detail header actions
- implement decision summary, matched rules, rejected rules, evidence, special handling notes
- implement source metadata and secondary action column

Frontend acceptance target:
- automated decision is always visible
- transparency content is readable, structured, and auditable
- sponsorship ambiguity presentation is explicit

#### Milestone 5: Tracking Workflow UI
- implement tracking page with status-first view
- standardize inline tracking controls across list/detail/tracking pages
- surface follow-up/reminder cues

Frontend acceptance target:
- tracking status is clearly distinct from automated classification
- saved jobs are easy to identify and act on

#### Milestone 6: Digest and Reminders UI
- implement digest view grouped by new matched/review items
- implement reminders page grouped by reminder type/status
- connect reminder dismissal feedback pattern

Frontend acceptance target:
- digest and reminder pages feel actionable, not log-like

#### Milestone 7: Source Health and Operational Hardening UI
- implement source health overview and run history/detail views
- refine warning, stale, failed, and partial-data presentation
- polish cross-page error/warning states and resilience messaging

Frontend acceptance target:
- source reliability issues are understandable without raw logs
- source health states are visually and textually distinct

## 3. UI/UX Inputs

Primary source documents used:
- `docs/architecture/job_intelligence_platform_mvp_technical_design.md`
- `docs/uiux/job_intelligence_platform_mvp_uiux_spec.md`
- `docs/architecture/job_intelligence_platform_implementation_plan.md`
- `docs/product/job_intelligence_platform_mvp_product_spec.md`

Key UX directives carried into this plan:
- clean dashboard-oriented UI, not admin-console density
- transparency by default for classification evidence
- manual user judgment must override workflow visibility without rewriting automated outcomes
- source health must be understandable in plain language
- JS usage must remain minimal and optional
- filters should be GET-driven and URL-addressable
- tables on desktop, cards on mobile for dense list views

No direct conflict requiring override was identified across the referenced docs. One implementation choice clarified here is consolidating source add/import into a single Sources hub page with segmented sections, while still allowing separate routes internally if the web layer prefers them.

## 4. Files Expected to Change

This planning artifact assumes future frontend implementation work will likely touch files in paths such as:

```text
app/web/routes/
app/web/templates/base.html
app/web/templates/includes/*
app/web/templates/dashboard/*
app/web/templates/jobs/*
app/web/templates/sources/*
app/web/templates/ops/*
app/web/templates/tracking/*
app/web/templates/notifications/*
app/web/view_models/*
app/web/forms/*
app/static/css/*
app/static/js/* (only if minimal progressive enhancement is added)
tests/unit/web/*
tests/integration/web/*
tests/end_to_end/*
```

Current implementation pass is expected to change:
- `app/main.py`
- `app/web/routes.py`
- `app/web/templates/base.html`
- `app/web/templates/includes/macros.html`
- `app/web/templates/dashboard/index.html`
- `app/web/templates/jobs/list.html`
- `app/web/templates/jobs/detail.html`
- `app/web/templates/sources/index.html`
- `app/web/templates/sources/detail.html`
- `app/web/templates/ops/source_health.html`
- `app/web/templates/ops/run_list.html`
- `app/web/templates/ops/run_detail.html`
- `app/web/templates/tracking/index.html`
- `app/web/templates/notifications/digest.html`
- `app/web/templates/notifications/reminders.html`
- `app/web/static/styles.css`
- `app/web/static/app.js`
- `tests/integration/test_html_views.py`
- `docs/frontend/job_intelligence_platform_frontend_implementation_plan.md`
- `docs/frontend/job_intelligence_platform_frontend_implementation_report.md`

## 5. Dependencies / Constraints

Dependencies:
- stable route set and web-layer module structure
- final view-model shapes for dashboard, jobs, sources, tracking, and operations pages
- confirmed list of supported `common_pattern` adapter keys and custom adapters
- confirmed source-type helper text and adapter labels
- backend availability of health, decision, evidence, reminder, and tracking data projections
- reminder threshold defaults for saved inactivity and applied follow-up

Constraints:
- frontend is server-rendered FastAPI + Jinja
- no auth flows in MVP local mode
- business logic remains server-side
- minimal JS only
- no real-time/websocket dependence
- source and job content must be safely rendered; plain-text-first job description rendering is preferred

## 6. Assumptions

1. The application will keep HTML-first route handlers and use JSON only for optional progressive enhancement.
2. The main navigation will include Dashboard, Jobs, Sources, Source Health, and Tracking, with Digest and Reminders accessible from dashboard links or secondary navigation.
3. The Sources experience can be delivered as one page with manual-entry and CSV-import sections while preserving dedicated routes if useful for handler simplicity.
4. Tracking updates will begin with a fully accessible select-and-submit interaction before any auto-submit enhancement is added.
5. CSS can be implemented with lightweight project stylesheets without requiring a heavy frontend build system.
6. Desktop jobs/tracking/source-health views will use semantic tables; mobile variants will use stacked cards.
7. Save/Keep actions should preserve current page context through redirect query-string retention.
8. The frontend will present evidence primarily as normalized text snippets rather than rendering arbitrary scraped HTML.
9. Pagination is not specified in the upstream docs; list views should be structured so pagination can be added later without changing page architecture.
10. Unsupported `common_pattern` and `custom_adapter` source families should remain visible in the UI with explicit unsupported messaging rather than being hidden.

## 7. Validation Plan

For the planning artifact itself:
- confirm alignment with technical design route inventory and HTML-first assumptions
- confirm coverage of all required MVP views and interactions from the UI/UX spec
- confirm plan includes frontend information flow, template structure, page/component breakdown, form strategy, minimal JS guidance, styling approach, accessibility, responsiveness, state handling, testing approach, and milestone execution plan

For future frontend implementation work based on this plan:
- run route/template render tests for each page
- run form submission and validation tests for source add/import, save/keep, tracking updates, and reminder dismissal
- run lint/type/template checks available in the repo
- perform manual responsive checks at desktop/tablet/mobile widths
- verify empty/error/warning/success states on each main page
- verify keyboard accessibility and visible focus behavior for filters, forms, and row actions

Implementation pass validation target:
- `python3 -m compileall app tests`
- `.venv/bin/python -m pytest`
- route smoke coverage for HTML dashboard, jobs, and form redirect flows
