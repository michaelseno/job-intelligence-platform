# Design Specification

## 1. Feature Overview

### Problem Statement
The product currently needs a cohesive UI revamp so every page presents as a professional SaaS dashboard rather than a collection of functional but uneven operator screens. The highest-visibility surfaces are Dashboard, Jobs, and Sources, but the same quality bar must extend to operational surfaces such as source health and run history so the product feels consistent in client demos and daily use.

Repository inspection indicates a FastAPI/Jinja-style application with product concepts including manual source creation, CSV import, Greenhouse/Lever ingestion, normalized jobs, status tracking, daily digest/reminders, source run history, and health summaries. Compiled route/test artifacts also indicate source edit/delete flows and source-related QA coverage. This spec therefore preserves the existing workflows and terminology while upgrading the visual system, information hierarchy, navigation pattern, and component behavior.

### Goals
- Make all pages feel like one polished, market-standard B2B SaaS dashboard.
- Improve clarity and consistency across Dashboard, Jobs, Sources, and ops/admin-like pages.
- Establish a reusable light-theme design system for typography, color, spacing, surfaces, and states.
- Improve forms, action hierarchy, dropdowns, tables, modals/drawers, and empty/loading/error states.
- Support desktop-first responsive usage while remaining functional on tablet/mobile.
- Preserve current flows, page inventory, and product terminology.

### Non-Goals
- No workflow redesign that changes business logic or backend behavior.
- No terminology overhaul beyond minor label cleanup for clarity.
- No chart-heavy analytics expansion unless a chart is already required by the page objective.
- No new product capabilities beyond UI structure and interaction improvements.

### Assumptions
- Current pages include at least Dashboard, Jobs, Sources, Source Health, and source run history/detail surfaces.
- Existing actions include create/edit/delete sources, import sources, inspect jobs, and review source health/run outcomes.
- Frontend implementation may be server-rendered or progressively enhanced; all guidance is therefore framework-agnostic and implementation-oriented.

## 2. User Goal
- Operators want to quickly understand system status, review jobs, manage sources, and resolve ingestion issues without UI friction.
- Demo audiences should immediately perceive the product as credible, modern, and organized.
- Frequent users need balanced density: enough information for operational efficiency, without noisy enterprise clutter.

## 3. UX Rationale
- A hybrid SaaS dashboard navigation model is the best fit: persistent left sidebar for global wayfinding, top app bar for context/actions, and optional page-level subnavigation/tabs where needed.
- Balanced density supports both monitoring and task execution. Tables, filters, and side panels should be compact but breathable.
- Operational/admin pages should not look like secondary tools. They must share the same shell, tokens, component standards, and state patterns as customer-facing pages.
- Because charts are not a priority, page layouts should emphasize KPI cards, status summaries, tables, timelines, and structured detail panels instead of decorative data viz.

## 4. Information Hierarchy

### Global Hierarchy
1. App-level navigation and current context
2. Page title and page purpose
3. Primary actions
4. Status summary / key metrics / filters
5. Main working content (table, cards, forms, detail panels)
6. Secondary metadata and diagnostics

### Content Priority by Domain
- **Dashboard:** today’s status, job pipeline summary, source health summary, recent activity requiring attention.
- **Jobs:** filters first, then sortable/scannable job list, then per-job status/actions.
- **Sources:** source inventory first, then per-source health, freshness, adapter type, and management actions.
- **Source Health / Runs:** recent failures, warnings, run results, timestamps, and next troubleshooting action.

## 5. Layout Structure

## 5.1 Navigation and Layout System

### Recommended Shell
- **Left sidebar (persistent on desktop):** global navigation.
- **Top app bar:** workspace title, page breadcrumb or section label, global search placeholder if available later, user/account menu.
- **Main content area:** max-width fluid layout with page container.
- **Page header block:** title, supporting description, primary action, secondary actions.

### Sidebar Structure
- Product/logo area at top.
- Primary nav group:
  - Dashboard
  - Jobs
  - Sources
- Operations nav group:
  - Source Health
  - Runs / Run History
  - Any other admin-like support pages already present
- Utility group at bottom:
  - Settings if present
  - Help / docs link if present

### Sidebar Behavior
- Desktop ≥1280px: expanded default, 240px width.
- Laptop 1024–1279px: collapsible icon rail + flyout labels or 88px compact sidebar.
- Tablet/mobile <1024px: drawer navigation from top bar.
- Active item uses filled subtle background + left accent border + stronger label color.

### Page Container
- Standard content width: fluid, with 24px horizontal padding on desktop and 16px on tablet/mobile.
- Vertical spacing rhythm: 24px between major sections, 16px between related blocks, 8px within component groups.

### Page Header Template
- Row 1: breadcrumb (optional for nested pages).
- Row 2: page title + supporting sentence.
- Row 3 right-aligned: actions.
- On narrower widths, actions wrap below title.

## 5.2 Page Archetypes and Templates

### A. Overview Template
Used for Dashboard.
- Header
- KPI/status summary cards
- Two-column content region for recent items and attention-needed blocks
- Lower full-width table/list for recent activity

### B. Management Table Template
Used for Jobs and Sources index pages.
- Header
- Filter/action toolbar
- Optional summary chips
- Primary data table
- Optional bulk or row detail drawer

### C. Detail + Activity Template
Used for source detail, source health detail, run detail.
- Header
- Summary strip
- Main detail card(s)
- Activity timeline / event list / related runs table
- Sticky side metadata panel when space allows

### D. Form Template
Used for create/edit/import flows.
- Header with explicit task title
- Single-column form up to 720px readable width, or 2-column only for short independent fields
- Persistent footer actions for long forms
- Inline validation and helper text

## 6. Components

## 6.1 Visual System

### Typography
- Font stack: Inter, ui-sans-serif, system-ui, sans-serif.
- Page title: 24/32 semibold.
- Section title: 18/28 semibold.
- Card title: 16/24 medium.
- Body: 14/20 regular.
- Table/body dense text: 13/18 regular.
- Caption/meta: 12/16 medium.
- Use sentence case for headings and actions.

### Color System
- **Canvas background:** #F7F8FA
- **Primary surface:** #FFFFFF
- **Secondary surface:** #F3F5F7
- **Primary text:** #111827
- **Secondary text:** #4B5563
- **Tertiary text:** #6B7280
- **Border default:** #E5E7EB
- **Border strong:** #D1D5DB
- **Brand / primary:** #2563EB
- **Brand hover:** #1D4ED8
- **Brand subtle bg:** #EFF6FF
- **Success:** #16A34A / bg #F0FDF4
- **Warning:** #D97706 / bg #FFFBEB
- **Danger:** #DC2626 / bg #FEF2F2
- **Info:** #0891B2 / bg #ECFEFF

### Spacing Scale
- 4, 8, 12, 16, 20, 24, 32, 40, 48
- Standard control height: 36px
- Large primary action height: 40px
- Card padding: 20px desktop, 16px compact

### Elevation
- Base cards: no heavy shadow; use border + 0 1px 2px rgba(16,24,40,0.04)
- Raised surfaces (dropdown, modal, drawer): 0 8px 24px rgba(16,24,40,0.12)
- Hovered cards: slightly stronger shadow, never dramatic

### Borders and Radius
- Radius sm: 8px
- Radius md: 10px
- Radius lg: 12px
- Default border width: 1px
- Inputs, cards, tables, dropdowns share consistent radius and border color

### Iconography
- Use a clean 1.5px–2px stroke icon set (Lucide/Heroicons style).
- Default icon size 16px in controls, 18px in nav, 20px in headers only when needed.
- Icons should support scanning, not decorate every label.

### Interaction States Token Rules
- Hover: subtle fill or border emphasis
- Focus: 2px visible blue focus ring outside component boundary
- Active: darker fill or pressed border
- Disabled: 40–50% opacity reduction plus no elevation
- Selected: brand-subtle background + stronger text/icon contrast

## 6.2 Component Standards

### Buttons and Action Hierarchy
- **Primary:** solid brand fill. One per section/header when possible.
- **Secondary:** neutral outline on white surface.
- **Tertiary:** text-only / ghost for low-emphasis actions.
- **Danger:** red text or red outline; destructive primary only inside explicit confirmation contexts.
- Include leading icons only when they improve recognition (Add source, Import CSV, Retry run).
- Button order in action groups: primary first, then secondary, then tertiary/danger separated.

### Forms
- Labels above fields, left-aligned.
- Helper text below field, muted.
- Required fields marked with “*”; avoid relying on color alone.
- Validation errors inline below field and summarized at top for multi-field failures.
- Group related fields into titled sections.
- Inputs, selects, date fields, and textareas must share consistent height, padding, radius, and border treatments.

### Dropdowns / Selects / Menus
- Use 36px trigger height.
- Menu width should match trigger minimum and align to trigger edge.
- Group destructive actions in a separated lower section.
- Keyboard navigation required; first item receives focus on open.

### Tables
- Default row height: 44px.
- Header background slightly tinted secondary surface.
- Sticky table header for long pages.
- Important columns left-aligned; status/action columns right-aligned only when necessary.
- Row hover uses subtle tinted background.
- Support empty, loading, and error states within table container.
- On smaller widths, collapse low-priority columns before introducing horizontal scroll.

### Badges / Status Chips
- Small rounded rectangular chips with 12px medium text.
- Semantic mappings:
  - Healthy/success = green
  - Warning/stale = amber
  - Failed/error = red
  - Neutral/system/manual = gray
  - Running/in-progress = blue
- Avoid more than one dominant color chip per row unless status requires it.

### Alerts / Notices
- Inline page alert for critical failures at top of content.
- Inline field alert for validation.
- Toasts only for transient confirmations (saved, deleted, retried).
- Alert layout: icon, title, supporting text, optional action link.

### Modals
- Use modal for confirmation, small edit tasks, or decisions requiring interruption.
- Max width 560px for standard dialogs.
- Include clear title, supporting description, body, and footer with actions.
- Dangerous confirmations must name the affected entity.

### Drawers
- Use right-side drawer for inspect/edit contexts that benefit from preserving table/list context.
- Preferred for source details, run details, and job quick-view if supported by current flow.
- Width: 480px standard, 640px for detailed operational review.

### Empty States
- Must explain what the page is for, why it is empty, and what action to take next.
- Include one primary CTA where appropriate.
- Use restrained illustrations or icon panels only; avoid playful consumer-style art.

### Loading States
- Use skeletons for cards/tables/forms where structure is known.
- Use inline spinner only inside buttons or small refresh regions.
- Keep layout stable during loading.

### Error States
- Distinguish between page-level load failure, section-level load failure, and form submission failure.
- Provide recovery action: Retry, Refresh, Review inputs, or View run details.

## 7. Interaction Behavior

### General Patterns
- Filters should update content predictably and keep visible active filter tokens when applied.
- Preserve context after actions: for example, after editing a source, return user to the same list position/filter state where possible.
- Destructive actions require confirmation; non-destructive edits should feel lightweight.
- For long-running actions (imports, run retries), show in-progress state plus destination for status follow-up.

### State Preservation
- Maintain selected filters, sort order, and pagination on refresh/navigation when technically feasible.
- Drawers should close back to the originating context rather than sending the user to a disconnected page.

## 8. Component States

Every interactive component family must define and visually support:
- default
- hover
- focus
- active
- disabled
- loading
- empty
- success
- error

### Required State Examples
- Buttons: spinner for loading, disabled cursor removal, clear pressed feedback.
- Inputs: neutral border, hover border emphasis, focus ring, red error border + message, success optional only where meaningful.
- Tables: skeleton rows, no-results state, connection failure state.
- Modals/drawers: submitting state disables duplicate submissions.
- Badges: semantic states remain readable in light theme and high zoom.

## 9. Responsive Design Rules

- **Desktop-first target:** optimize 1280px+ first.
- **1024–1279px:** reduce outer margins, allow 2-column areas to become 1:1 or stacked where needed.
- **768–1023px:** convert persistent sidebar to collapsible drawer; summary card grids reduce from 4-up to 2-up.
- **<768px:** stack header actions, prioritize essential columns, use cards or expandable rows for dense tables if needed.
- Maintain minimum tap target of 40px on touch devices.
- Never hide critical actions behind hover-only affordances on tablet/mobile.

## 10. Visual Design Tokens

### Core Tokens
- `--bg-canvas: #F7F8FA`
- `--bg-surface: #FFFFFF`
- `--bg-surface-subtle: #F3F5F7`
- `--text-primary: #111827`
- `--text-secondary: #4B5563`
- `--text-tertiary: #6B7280`
- `--border-default: #E5E7EB`
- `--border-strong: #D1D5DB`
- `--brand-600: #2563EB`
- `--brand-700: #1D4ED8`
- `--brand-50: #EFF6FF`
- `--success-600: #16A34A`
- `--warning-600: #D97706`
- `--danger-600: #DC2626`
- `--info-600: #0891B2`
- `--radius-sm: 8px`
- `--radius-md: 10px`
- `--radius-lg: 12px`
- `--space-1: 4px` through `--space-12: 48px`
- `--shadow-sm: 0 1px 2px rgba(16,24,40,0.04)`
- `--shadow-lg: 0 8px 24px rgba(16,24,40,0.12)`

### Consistency Rules
- Use one border system across cards, inputs, tables, and menus.
- Use color semantically, not decoratively.
- Use brand blue primarily for emphasis and action, not large area fills.
- Prefer neutral surfaces with selective color highlights to achieve enterprise polish.

## 11. Accessibility Requirements

- Meet WCAG 2.1 AA baseline for contrast, keyboard use, focus visibility, and semantic labeling.
- Do not rely on color alone for status; pair with label text/icon.
- All interactive controls require visible focus states.
- Modal and drawer patterns require focus trapping and escape dismissal where appropriate.
- Form fields require associated labels and error messaging tied via ARIA attributes.
- Tables need meaningful headers and row associations.
- Toasts/alerts should use polite/assertive live regions based on severity.
- Support zoom to 200% without loss of task completion.

## 12. Edge Cases

- No jobs yet after a new source is added.
- Source exists but has never run.
- Source run partially succeeds with warnings.
- All sources failing, requiring an obvious at-risk state without overwhelming the page.
- Large job result sets needing sticky filters and table header stability.
- Long source names, URLs, or adapter metadata requiring truncation + tooltip/full detail view.
- Confirmation flows for source deletion where downstream effects should be plainly stated.
- Empty search/filter results distinct from true no-data empty state.

## 13. Developer Handoff Notes

### Page-Specific Guidance

#### Dashboard
- Purpose: quick daily operational overview.
- Top section: 3–5 summary cards only, such as total active sources, jobs added/recently updated, sources needing attention, failed recent runs.
- Middle section: split layout with “Jobs needing review / recent jobs” and “Source health / recent run issues.”
- Lower section: recent activity table or feed.
- Avoid charts by default; use trend copy or delta text inside cards instead.

#### Jobs
- Primary template: management table.
- Header actions should favor filtering/export/refresh only if already supported; avoid adding net-new actions.
- Filters likely include status, source, freshness, search, and saved/applied states if present.
- Table columns should prioritize title, company/source, location if available, status, last updated, and row actions.
- Row click should open detail or preserve existing flow; if feasible, use a drawer for quick inspect without losing scan context.

#### Sources
- Primary template: management table with stronger row summaries.
- Important columns: source name, adapter type, status/health, last run, last success, jobs discovered or relevant volume metric if already available, actions.
- Primary actions likely include Add source and Import CSV if those exist today.
- Source row expansion or drawer should surface metadata, schedule/frequency if present, and recent run outcomes.

#### Source Health / Runs
- Must visually match the main product shell, not a separate admin utility.
- Use status-first summaries and event/timeline blocks instead of dense debugging walls.
- Highlight latest run outcome, failure reason summary, timestamps, and retry/view-detail actions.
- Use badges, notices, and structured log/event grouping for readability.

#### Remaining Pages
- Apply one of the approved templates rather than inventing page-by-page layouts.
- Reuse the same header, toolbar, filter, card, table, modal, and drawer patterns.
- If a page is mostly operational/configurational, increase explanatory text and inline guidance rather than introducing new visual paradigms.

### Design Principles
- Professional before expressive.
- Dense enough for operators, calm enough for demos.
- Strong action hierarchy, minimal ambiguity.
- System status should be visible without visual noise.
- Reuse patterns aggressively across all pages.

### Acceptance-Oriented UI Outcomes / Review Checklist
- All pages share the same shell, spacing rhythm, and component language.
- Dashboard, Jobs, and Sources clearly read as priority polished surfaces.
- Source Health / run pages feel visually first-class, not internal leftovers.
- Primary, secondary, tertiary, and danger actions are visually distinct and consistently placed.
- Forms, dropdowns, modals, and drawers use one unified visual and interaction standard.
- Tables are readable, scannable, and balanced in density.
- Empty, loading, success, and error states are present and professionally written.
- Light theme feels modern SaaS and enterprise-credible.
- Responsive behavior is defined for desktop, laptop, tablet, and mobile.
- Accessibility baseline is met for contrast, focus, keyboard behavior, labels, and status communication.
- No workflow logic or terminology is unintentionally changed.

### Implementation Priority Recommendation
1. App shell + navigation
2. Core tokens + typography + surface system
3. Buttons/forms/dropdowns/modals/drawers
4. Table standard
5. Dashboard
6. Jobs
7. Sources
8. Source Health / Runs
9. Remaining pages and cleanup pass
