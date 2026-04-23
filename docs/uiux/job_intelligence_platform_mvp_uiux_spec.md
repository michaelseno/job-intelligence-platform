# Design Specification

## 1. Feature Overview
The Job Intelligence Platform MVP is a single-user, local/self-hosted web dashboard for collecting job postings from configured sources, classifying them into matched / review / rejected buckets, explaining those decisions, and tracking applications through lightweight status management.

This UI/UX spec covers the core web experience for the MVP, with the dashboard as the primary interaction surface and the daily digest treated as a secondary notification surface.

### Assumptions
- No authentication is required in MVP.
- Frontend is server-rendered with Jinja templates and lightweight progressive enhancement where needed.
- MVP CSV import uses a baseline schema of `name`, `source_type`, `base_url`, `external_identifier`, `adapter_key`, `company_name`, `is_active`, and `notes`, with source-type-specific requiredness.
- Manual override means the user can keep/save a job without changing or deleting the original automated classification record.
- In-app digest and reminder pages are the required MVP delivery surface.

### Design Principles
- **Clarity over density:** prioritize scanability and actionability over admin-style data density.
- **Transparency by default:** never hide why a job was bucketed.
- **User judgment wins:** automated decisions inform; they do not block manual retention or tracking.
- **Operational visibility without engineering jargon:** source health should be understandable without logs.
- **Fast, server-rendered UX:** favor simple components, predictable layouts, and minimal JS dependence.
- **Accessible first:** semantic structure, keyboard usability, contrast, and state visibility are required.

## 2. User Goal
Help a single job seeker move through the MVP workflow efficiently:

1. Add sources by CSV or manual entry.
2. Run or review ingestion outcomes.
3. Review new jobs by decision bucket.
4. Understand exactly why each job was classified.
5. Keep valuable edge cases via manual override.
6. Track applications from saved through offer.
7. Notice broken or stale sources quickly.

## 3. UX Rationale
The product is not a generic admin console. The UX should feel like a focused personal workbench:
- the dashboard surfaces the most important jobs and reminders first
- the jobs list is optimized for triage
- the job detail page is optimized for trust and decision inspection
- source management is separated from day-to-day review work but still easy to access
- operational health is visible without dominating the main workflow

The interface should balance three distinct concepts without conflating them:
- **classification bucket** = system decision
- **tracking status** = user workflow state
- **source health** = ingestion reliability

## 4. Information Hierarchy
### Primary Navigation
Top-level navigation should be persistent and minimal:
- Dashboard
- Jobs
- Sources
- Source Health
- Tracking

### Secondary Navigation / Local Filters
- Dashboard: quick links to matched, review, rejected, reminders, recent source issues
- Jobs: bucket filters, tracking filters, source filters, search, sort
- Sources: tabs or segmented controls for Add Source and Import CSV
- Tracking: status tabs or filter chips for saved, applied, interview, rejected, offer

### Page Inventory
- Dashboard
- Jobs List
- Job Detail
- Source Add / Import
- Source Health
- Application Tracking

### Priority Order of Content
1. New matched jobs
2. New review jobs
3. Saved / follow-up reminders
4. Manual overrides needing attention
5. Source health warnings
6. Rejected jobs and lower-priority operational detail

## 5. Layout Structure
### Global Layout
- **Header:** product title, primary nav, optional “last ingestion” summary text.
- **Main content container:** max-width centered layout, generous whitespace, 12-column desktop grid.
- **Right rail:** avoid for MVP unless used on dashboard desktop only; keep mobile stacking simple.
- **Footer:** optional lightweight metadata (local mode, last updated timestamp).

### Layout Rules
- Use a two-level hierarchy: page header + content sections.
- Each page header should include title, short purpose text, and page-level actions.
- Prefer stacked content blocks on mobile and tablet.
- Avoid modal-heavy flows; use inline sections and full-page forms where possible.

### Suggested Page Widths
- Dashboard / Jobs / Tracking: wide content layout.
- Job Detail: wide content layout with main detail column and secondary metadata column on desktop.
- Source Add / Import: medium-width form layout.
- Source Health: wide content layout with table-first presentation.

## 6. Components
### Core Components
- Top navigation bar
- Page header
- Summary stat cards
- Filter chips / segmented controls
- Data table
- Job result card
- Detail panel / section card
- Badge / pill
- Status icon + label
- Callout banner
- Empty state block
- Inline validation message
- Confirmation prompt for destructive or irreversible user actions

### Component Recommendations by Use Case
#### Tables
Use tables for:
- jobs list on desktop
- source health
- application tracking

Reason: these views benefit from comparison, sorting, and compact scanning.

#### Cards
Use cards for:
- dashboard summaries
- dashboard recent jobs preview
- mobile job list rows
- decision transparency sections inside job detail

Reason: cards work better for grouped content and responsive stacking.

#### Lists
Use structured lists for:
- matched rules
- rejected rules
- evidence snippets
- reminder queues

### Key Data Presentation Patterns
#### Job List Row
Each job row/card should show:
- title
- company / source label
- classification bucket badge
- tracking status badge if present
- score
- top 1-2 reason summary
- location / remote label if available
- posted / ingested recency
- quick actions: View, Save/Keep, Update Status

#### Badge System
- Classification badges: matched, review, rejected
- Tracking badges: saved, applied, interview, rejected, offer
- Health badges: healthy, warning, failed, stale

Classification and tracking badges must be visually distinct to prevent confusion.

## 7. Interaction Behavior
### Global Interaction Patterns
- Primary actions appear in the top-right of page headers.
- Filters should update the current page state without requiring complex navigation.
- Important actions should be available from both list and detail views.
- Avoid hiding critical job actions behind overflow menus on desktop.

### Main Workflow Support
#### Add Source -> Ingest -> Review
- Sources page should clearly present two entry paths: **Manual Entry** and **CSV Import**.
- After source creation/import, show success feedback plus next recommended action: “Review source health” or “Run ingestion when available.”
- Dashboard should make it obvious when there are no recent ingestion results yet.

### Decision Transparency Presentation Pattern
Use a fixed section order on job detail:
1. **Decision Summary**
   - bucket badge
   - final score
   - concise one-sentence summary
2. **Matched Rules**
   - list of positive rules with evidence snippets
3. **Rejected Rules / Negative Signals**
   - list of negative rules with evidence snippets
4. **Special Handling Notes**
   - sponsorship ambiguity callout when relevant
5. **Source Evidence**
   - link to source job URL and extracted source metadata

Rules should be shown as labeled rows:
- rule name
- effect (positive / negative / review-driving)
- supporting snippet

Evidence snippets should visually read like quoted excerpts, with sufficient spacing and muted background.

### Manual Override Interaction Pattern
- Primary label: **Save / Keep Job**
- Secondary explanatory text: “Preserves this job for tracking without changing the automated decision.”
- Available from jobs list and job detail.
- On activation:
  - create/update tracking status to **saved** if none exists
  - preserve original classification bucket and transparency data
  - show confirmation toast/banner: “Job saved. Automated classification remains unchanged.”
- If job is already saved or tracked, button becomes **Update Tracking** or disabled with current state shown.

### Tracking Status Update Pattern
- Prefer inline dropdown/select in list views.
- On job detail, use a segmented control or select with explicit save action if needed by implementation.
- Status changes should not move the user away from the current page.

### Search / Filter Behavior
- Jobs list should support filters for bucket, tracking status, source, and text search.
- Filters must be combinable.
- Provide a clear “Reset filters” action.

## 8. Component States
### Standard States to Support
All actionable controls should define:
- default
- hover
- focus
- active
- disabled

### Page and Data States
#### Loading
- Use skeleton rows/cards for dashboard summaries and tables when possible.
- If server-rendered without skeletons, use clear loading copy: “Loading jobs…” / “Loading source health…”.

#### Empty
##### Dashboard Empty
- Message: no jobs yet or no recent ingestion.
- CTA: Add Source.

##### Jobs Empty
- Differentiate between:
  - no jobs exist yet
  - current filters return no results

##### Tracking Empty
- Message should explain there are no tracked jobs in the selected status.

##### Source Health Empty
- Message should explain no sources are configured yet.

#### Success
- Inline success banner after source add/import.
- Lightweight confirmation after save/keep or tracking update.

#### Error / Failure
- CSV upload errors should show row-level failures when possible.
- Manual source form errors should appear inline by field and in a summary at top.
- Source health failure state should use prominent warning styling and action guidance.
- Jobs fetch failure should not appear as a blank screen; show last known successful data if available plus warning.

### Source Health Warning States
- **Warning:** zero jobs returned unexpectedly or repeatedly
- **Failed:** latest run failed
- **Stale:** no successful run within expected recent period
- **Partial data:** source returned incomplete fields or weak evidence support

Each warning row should include:
- status label
- short human-readable explanation
- last run timestamp
- jobs fetched count
- suggested next action

## 9. Responsive Design Rules
### Desktop
- Use summary cards and tables freely.
- Jobs list and tracking should default to tables.
- Job detail can use 2-column layout: main content left, metadata/actions right.

### Tablet
- Collapse dashboard cards into 2-column grid.
- Convert wide tables to horizontally scrollable tables only if necessary; otherwise reduce visible columns.
- Job detail should stack lower-priority metadata below main content.

### Mobile
- Top nav may collapse into simple stacked or compact nav pattern.
- Replace dense tables with card/list rows for jobs and tracking.
- Keep primary actions near top of page and repeated at bottom for long detail views.
- Filters should collapse into an expandable filter panel.

### Responsive Priorities
Columns to drop first on smaller screens:
1. source details beyond primary source name
2. lower-priority timestamps
3. secondary reason text

Columns to preserve longest:
- title
- bucket
- tracking status
- score
- primary action

## 10. Visual Design Tokens
Suggested lightweight visual system for Jinja-rendered templates:

### Tone
- Clean, calm, practical
- More product dashboard than enterprise admin console
- Neutral surfaces with restrained accent usage

### Color Roles
- **Background:** warm or neutral off-white / very light gray
- **Surface:** white or near-white cards/panels
- **Text primary:** near-black / dark slate
- **Text secondary:** medium gray
- **Border:** subtle gray
- **Primary accent:** muted blue
- **Success / matched:** green
- **Warning / review:** amber
- **Danger / rejected / failed:** red
- **Info / source metadata:** blue-gray

### Typography
- One sans-serif family only.
- Clear scale with 4-5 sizes max.
- Slightly larger page titles and section titles; body text optimized for long evidence snippets.

### Spacing
- Base spacing unit: 4px or 8px.
- Prefer consistent section padding rather than dense compact layouts.

### Borders and Elevation
- Use light borders and minimal shadows.
- Reserve stronger emphasis for warnings, active filters, and focus states.

### Icon Usage
- Use icons sparingly for status, source type, and warnings.
- Never rely on icon-only communication for critical state.

## 11. Accessibility Requirements
- Semantic headings and landmarks per page.
- Keyboard access for all filters, tables, job actions, and form controls.
- Visible focus ring with sufficient contrast.
- Do not rely on color alone to distinguish classification, tracking, or health state; include text labels.
- Tables must have proper headers and row associations.
- Form fields require persistent labels, not placeholder-only labeling.
- Validation errors must be announced clearly and tied to fields.
- Evidence snippets and quoted content must maintain readable contrast.
- Touch targets should be comfortably usable on mobile.
- Support logical tab order and avoid hidden focus traps.

## 12. Edge Cases
### Jobs and Classification
- Sponsorship unclear: show review bucket plus explicit note that ambiguity prevented auto-rejection.
- Very low-text jobs: show “Limited source text available” and reduce implied confidence.
- Duplicate or near-duplicate jobs: if surfaced in MVP, indicate duplicate source references without forcing merge complexity into primary UX.
- Removed external posting: retain tracked job with warning that source posting is no longer available.

### Sources
- Duplicate CSV source rows: warn before import completion or report duplicates in import results summary.
- Unsupported direct page: explain that source was not added because the page pattern is not supported.
- Partial adapter match: allow source to exist only if minimally valid; otherwise block with clear reason.

### Tracking and Reminders
- Saved job with no action: show as reminder candidate but avoid alarmist styling.
- Applied job needing follow-up: show reminder with last status update date.
- User intentionally keeps a poor-fit job: preserve it cleanly without forcing reclassification.

## 13. Developer Handoff Notes
### A. Navigation Model
- Keep routing simple and page-based for Jinja templates.
- Recommended routes/pages:
  - `/` or `/dashboard`
  - `/jobs`
  - `/jobs/{id}`
  - `/sources`
  - `/source-health`
  - `/tracking`

### B. Page-by-Page UX Specs
#### 1. Dashboard
**Purpose:** daily command center for new jobs, reminders, and source issues.

**Page header:**
- title: Dashboard
- subtitle: short summary of recent ingestion and pending work
- actions: Add Source, View Jobs

**Sections in order:**
1. summary cards
   - new matched
   - new review
   - saved needing action
   - applied needing follow-up
2. recent matched jobs preview
3. recent review jobs preview
4. reminder queue
5. source health warnings

**Recommended patterns:**
- stat cards for high-level counts
- compact cards or short table for recent jobs
- callout banner if recent ingestion failed or no sources exist

**Empty state:**
- if no sources: explain first step and link to Sources
- if sources exist but no jobs yet: explain ingestion may not have run yet

#### 2. Jobs List
**Purpose:** triage and browse all ingested jobs.

**Page header:**
- title: Jobs
- actions: none required beyond filters

**Controls:**
- search input
- bucket filter chips: matched / review / rejected
- tracking status filter
- source filter
- sort: newest, highest score, company/title alphabetical

**Desktop layout:**
table with columns:
- title
- company/source
- bucket
- tracking
- score
- top reason summary
- updated/ingested
- actions

**Mobile layout:**
stacked result cards with same information in priority order.

**Quick actions:**
- View
- Save/Keep
- Update Tracking

**Key usability note:**
- rejected jobs should remain accessible but visually de-emphasized compared with matched/review.

#### 3. Job Detail
**Purpose:** inspect a specific role deeply and take action.

**Page header:**
- job title
- company/source context
- primary actions: Save/Keep Job, Update Tracking, Open Source Posting

**Main sections:**
1. job summary
   - bucket badge
   - tracking status
   - score
   - location / remote
   - source
2. decision summary
3. matched rules
4. rejected rules / negative signals
5. evidence snippets
6. job description excerpt or normalized content summary
7. source metadata

**Secondary column on desktop:**
- tracking controls
- timestamps
- source health context (if relevant)
- reminder-related metadata if available

**Critical behavior:**
- automated decision must always remain visible even after manual keep/save.

#### 4. Source Add / Import
**Purpose:** onboard sources quickly and safely.

**Page header:**
- title: Sources
- subtitle: add sources manually or import from CSV

**Structure:**
- segmented control or tabs:
  - Manual Entry
  - CSV Import

**Manual Entry Form**
Recommended fields:
- source name
- source type
- company name (if distinct)
- source URL
- external identifier / board token / company slug when required by source family
- adapter/pattern selection if applicable
- notes (optional)

**Manual form UX rules:**
- required fields clearly marked
- show helper text for supported source types
- when source type is direct/custom, show support note so user understands coverage limits
- validation should happen server-side and be displayed inline

**CSV Import UX**
Include:
- short instructions
- downloadable or viewable schema/example reference
- file input
- import result summary area

**CSV schema guidance should explicitly show:**
- required columns common to all rows
- which columns are conditionally required by source type
- that import is create-only in MVP and duplicates are skipped with warnings

**CSV import result summary should show:**
- rows imported successfully
- rows skipped
- duplicate rows detected
- rows with validation errors

**Failure handling:**
- do not fail silently
- preserve clear mapping between error and CSV row where possible

#### 5. Source Health
**Purpose:** help the user detect broken, stale, or empty-result sources.

**Page header:**
- title: Source Health
- subtitle: latest ingestion status by configured source

**Primary view:**
table with columns:
- source name
- source type
- latest status
- last run
- jobs fetched
- warning state
- latest note / explanation

**Row behavior:**
- warning and failed rows visually highlighted
- include direct link to source details or source record when available

**Warning copy examples:**
- “Returned zero jobs on latest run.”
- “Multiple empty runs detected.”
- “Last run failed.”
- “No recent successful runs.”

**Empty state:**
- no sources configured yet

#### 6. Application Tracking
**Purpose:** manage active pipeline independent of classification.

**Page header:**
- title: Tracking
- subtitle: jobs you have chosen to keep or progress

**Primary controls:**
- status tabs or chips: saved, applied, interview, rejected, offer
- search
- optional sort by recent update or follow-up urgency

**Desktop layout:**
table with columns:
- title
- company/source
- tracking status
- classification bucket
- score
- last updated
- next reminder / follow-up cue if available
- actions

**Behavior notes:**
- saved jobs are the default landing tab/filter because they represent pending action
- classification bucket remains visible for context but secondary to tracking status on this page

### C. Copy and Labeling Guidance
- Use “review” instead of “maybe.”
- Use “Save / Keep Job” for manual override action.
- Use “Tracking status” for user-managed state.
- Use “Automated classification” for system-generated bucket.
- Use “Source health” instead of “operations logs.”
- Avoid copy that implies manual keep/save rewrites the automated bucket.

### D. Suggested Lightweight Implementation Approach
- Build with reusable Jinja partials for:
  - badges
  - stat cards
  - table wrappers
  - empty states
  - inline alert banners
  - decision rule rows
- Keep client-side behavior optional and progressive.
- Prefer GET-based filter forms for lists so filtered states are URL-addressable.

### E. Most Important UX Safeguards
- Never hide the original classification after save/keep.
- Never treat empty source results as silent success.
- Always show why a job was matched, reviewed, or rejected.
- Keep source onboarding forgiving but explicit about unsupported inputs.
- Preserve a calm, personal dashboard feel rather than an ops/admin product feel.
