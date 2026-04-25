# SaaS Dashboard UI Revamp Technical Design

## Feature Overview

This document defines the frontend implementation approach for the SaaS dashboard UI revamp described in `docs/uiux/saas_dashboard_ui_revamp.md`.

The goal is to modernize the product into a cohesive light-theme SaaS dashboard without changing existing workflows, backend business logic, or product terminology. The revamp should first elevate Dashboard, Jobs, and Sources, then extend the same shell and component system to Source Health, Runs, and remaining operational pages.

## Product Requirements Summary

- Introduce a unified SaaS-style application shell with persistent navigation.
- Establish a reusable visual system for colors, spacing, typography, surfaces, and states.
- Standardize component behavior for forms, buttons, tables, dropdowns, modals/drawers, alerts, and empty/loading/error states.
- Preserve existing user flows such as source create/edit/delete, CSV import, job review, and source health/run inspection.
- Support desktop-first responsive behavior while remaining functional on tablet/mobile.
- Maintain accessibility baseline at WCAG 2.1 AA.

## Scope

### In Scope

- Frontend architecture for server-rendered dashboard pages.
- Layout shell strategy: sidebar, topbar, page header, content containers.
- Design token strategy and CSS organization.
- Reusable template/component composition approach for the current stack.
- Component standards for core dashboard UI elements.
- Migration plan for Dashboard, Jobs, Sources first, then remaining pages.
- Accessibility, responsiveness, rollout, and implementation guidance.

### Out of Scope

- Backend domain logic changes.
- New product capabilities or major workflow redesign.
- New SPA frontend stack adoption.
- Data model changes outside of optional UI view-model shaping.

## Current-State Technical Summary

Based on the repository snapshot and planning artifacts:

- The codebase is a Python FastAPI application with `jinja2` included as a dependency.
- Repository structure currently contains backend-oriented directories under `app/` (`adapters`, `config`, `domain`, `persistence`, `web`) plus tests and Alembic assets.
- The checked-in snapshot does **not** currently expose source template, CSS, or JS files in the repository root, and `app/web/` currently only shows compiled artifacts. This indicates one of:
  - frontend template/static source files are not committed in this branch snapshot, or
  - current UI implementation is incomplete/minimal and needs formal structure added.
- The UI/UX spec explicitly references a “FastAPI/Jinja-style application,” so the safest implementation target is server-rendered Jinja templates with progressive enhancement rather than a client-side SPA rewrite.
- Existing product concepts confirmed by package metadata and the UI/UX spec include:
  - Dashboard
  - Jobs
  - Sources
  - source create/edit/delete/import flows
  - Source Health / run history / run details
  - Greenhouse and Lever ingestion
  - normalized jobs and status tracking

### Architectural Implication

The revamp should be implemented as a **server-rendered design system and layout refactor** that can fit into FastAPI route handlers with minimal backend contract changes. The frontend should rely on:

- shared Jinja base templates/macros
- one global tokenized stylesheet
- small page-specific styles only where necessary
- minimal JavaScript for navigation drawer, dropdowns, modal/drawer behavior, and filter state ergonomics

## Architecture Overview

### Target Frontend Architecture

Adopt a layered frontend architecture suitable for FastAPI + Jinja:

1. **Layout layer**
   - global app shell
   - responsive navigation
   - topbar
   - page header container

2. **Design system layer**
   - CSS custom properties for tokens
   - base element styles
   - utility/layout classes
   - semantic component classes

3. **Template composition layer**
   - base template
   - page archetype templates
   - reusable partials/macros for components

4. **Progressive enhancement layer**
   - lightweight JS for disclosure patterns and interaction polish
   - no dependency on client-side rendering for primary task completion

5. **View-model layer**
   - route handlers provide normalized page context shaped for templates
   - no business logic in templates beyond simple conditionals/loops

### Recommended Rendering Model

- Keep pages server-rendered.
- Prefer GET-driven filtering and sorting so page state remains shareable and resilient.
- Use optional progressive enhancement for drawers, menus, and inline actions.
- If partial-refresh interactions already exist or are added later, keep them additive and compatible with full-page rendering.

## System Components

### 1. Layout Shell

- `app shell`
- `sidebar navigation`
- `top app bar`
- `page header block`
- `content section containers`

### 2. Shared UI Components

- buttons
- form controls
- filter toolbar
- table wrapper
- badges/status chips
- alerts/notices
- dropdown/menu
- modal
- drawer
- empty/loading/error states
- KPI/stat cards

### 3. Page Templates

- overview template for Dashboard
- management table template for Jobs and Sources
- detail + activity template for Source Health and Runs
- form template for create/edit/import flows

### 4. Frontend Assets

- global tokens stylesheet
- base/layout/component stylesheets
- small JS bundle for accessible interactions

## Data Models and Storage Design

No persistent schema changes are required for the UI revamp.

### Frontend View-Model Shape

Routes should provide template-friendly view models rather than raw ORM objects where feasible.

Recommended view-model patterns:

#### Navigation Item

```text
label
route_name or href
icon_key
is_active
section
badge_count?
```

#### Page Header Model

```text
title
description
breadcrumb[]
primary_action?
secondary_actions[]
```

#### Stat Card Model

```text
label
value
supporting_text?
status_tone?
delta?
href?
```

#### Table Column Definition

```text
key
label
priority
align
responsive_behavior
```

#### Row Action Model

```text
label
href or action
tone
icon_key?
requires_confirmation
```

#### UI State Model

```text
is_loading
is_empty
is_error
error_title?
error_message?
recovery_action?
```

### URL-State Strategy

Persist filter/search/sort/page state in query params.

Recommended shared query param contract:

- `q`: free-text search
- `status`: status filter
- `source`: source filter
- `adapter`: adapter filter where relevant
- `sort`: sort field
- `order`: `asc|desc`
- `page`: page number
- `page_size`: optional if already supported

This preserves state across refresh, navigation, and back/forward flows.

## API Contracts

This revamp should not require new backend APIs if pages remain server-rendered.

### Server-Rendered Contract

Each HTML route should provide:

- `layout_context`
- `page_header`
- page-specific content collections
- `ui_state`
- `flash/notice` payloads if applicable

### Optional Progressive Enhancement Endpoints

If the frontend developer introduces drawers/modals backed by partial responses later, keep contracts minimal and HTML-first:

- `GET /jobs/{id}` → full page or partial detail fragment
- `GET /sources/{id}` → full page or detail fragment
- `GET /runs/{id}` → full page or detail fragment

These are optional future refinements, not required for initial rollout.

## Frontend / Client Impact

## Layout Shell Strategy

### Shell Composition

- **Desktop (`>=1280px`)**: fixed left sidebar, sticky topbar, scrollable content region.
- **Laptop (`1024px-1279px`)**: compact/collapsible sidebar, same topbar/content structure.
- **Tablet/mobile (`<1024px`)**: sidebar becomes modal drawer opened from topbar.

### Shell Regions

1. **Sidebar**
   - logo/product area
   - primary nav: Dashboard, Jobs, Sources
   - operations nav: Source Health, Runs, other existing ops pages
   - utility nav near bottom if present

2. **Topbar**
   - current section/breadcrumb
   - optional contextual page utility slot
   - user/account menu placeholder if implemented
   - mobile nav toggle

3. **Main content**
   - page container with responsive horizontal padding
   - page header block
   - section stack following 24px / 16px spacing rhythm

### Page Header Strategy

Use one shared page-header partial for all pages.

Header contract:

- title
- optional breadcrumb
- supporting description
- primary action
- secondary actions

Header behavior:

- desktop: title/description left, actions right
- small screens: action group wraps below title

### Content Container Strategy

- Use a fluid content column with max-width behavior controlled per template archetype.
- Standard surfaces are bordered white cards on `--bg-canvas`.
- Avoid page-specific ad hoc spacing; all pages should compose from shared section/container classes.

## Reusable UI Composition Strategy

Because the target stack is FastAPI + Jinja, the recommended composition model is:

### Templates

- `base.html` — global shell, asset loading, flash region
- `layouts/app_shell.html` — sidebar/topbar/content frame
- `pages/...` — page templates extending the shell

### Partials / Macros

- `partials/sidebar.html`
- `partials/topbar.html`
- `partials/page_header.html`
- `partials/alerts.html`
- `partials/empty_state.html`
- `partials/loading_state.html`
- `partials/error_state.html`
- `partials/pagination.html`
- `macros/buttons.html`
- `macros/forms.html`
- `macros/table.html`
- `macros/badges.html`
- `macros/dropdowns.html`
- `macros/modals.html`
- `macros/drawers.html`
- `macros/cards.html`

### CSS Organization

Recommended file/module split:

- `static/css/tokens.css`
- `static/css/base.css`
- `static/css/layout.css`
- `static/css/components.css`
- `static/css/utilities.css`
- `static/css/pages/dashboard.css`
- `static/css/pages/jobs.css`
- `static/css/pages/sources.css`

Rules:

- tokens only in `tokens.css`
- reset/base element rules in `base.css`
- shell/grid/container patterns in `layout.css`
- reusable semantic components in `components.css`
- utility classes should remain limited and intentional
- page CSS should only handle page-specific layout differences, not redefine components

### JavaScript Organization

Keep JS small and focused:

- `static/js/ui-shell.js` — sidebar drawer, topbar interactions
- `static/js/dropdown.js`
- `static/js/modal.js`
- `static/js/drawer.js`
- `static/js/table.js` — optional sticky/focus enhancements only

Avoid putting business rules in JS. Core page tasks must still work without complex client logic.

## Design Token Strategy

Implement the spec’s visual system as CSS custom properties on `:root`.

### Token Groups

#### Color Tokens

- canvas/background
- surfaces
- text tiers
- border tiers
- brand
- semantic statuses: success, warning, danger, info

#### Spacing Tokens

- base 4px scale
- component paddings
- layout gaps

#### Radius Tokens

- `sm`, `md`, `lg`

#### Typography Tokens

- font family
- type sizes
- line heights
- semantic text roles: page title, section title, body, dense body, caption

#### Elevation Tokens

- `shadow-sm`
- `shadow-lg`

#### Interaction Tokens

- focus ring color and width
- hover fills
- disabled opacity
- selected background

### Token Usage Rules

- Use semantic tokens in components, not raw hex values.
- Do not create page-level custom colors unless a new semantic token is added centrally.
- Status visuals must always pair color with text/icon.
- Keep light theme neutral-heavy; brand blue reserved for action emphasis and selected states.

## Backend Logic / Service Behavior

Backend behavior should remain largely unchanged, but route handlers should provide cleaner presentation-oriented context.

### Required Backend Support

- expose active navigation context per page
- shape page header/action metadata consistently
- normalize empty/loading/error message payloads
- support query-param based filter persistence
- provide semantic status values that map cleanly to badge tones

### Preferred Template Data Discipline

- avoid direct ORM branching in templates
- map backend statuses to UI-safe enums before render
- centralize common page context generation in `app/web/` helpers when source files are restored/added

## Component Implementation Plan

### Buttons

- Create one macro/API for button rendering with `primary`, `secondary`, `tertiary`, `danger` variants.
- Support icon-left, loading, disabled, and full-width options.
- Use anchor/button rendering from the same macro to avoid drift.

### Forms

- Standardize label, helper, error, and field wrapper structure.
- One field macro per control family: input, select, textarea, checkbox/radio group.
- Ensure server-side validation messages render inline and in a page-level summary when needed.

### Tables

- Build one reusable table wrapper with slots for toolbar, summary chips, table body, pagination, and state panels.
- Support priority-based responsive columns.
- Keep row actions in a consistent trailing column or overflow menu.

### Filters

- Use a shared filter toolbar pattern with search first, then selects/chips, then reset action.
- Active filters should render as visible chips/tokens near the toolbar.
- Filters should submit as GET where possible.

### Dropdowns

- One accessible disclosure/menu pattern for row actions, topbar menu, and select-like menus where native select is unsuitable.
- Keyboard support required: open, close, arrow navigation, escape, focus return.

### Badges

- Centralize status-to-tone mapping.
- Provide variants: neutral, success, warning, danger, info.

### Alerts

- Provide page-level, inline, and toast variants.
- Page-level alerts live below page header; inline alerts live within cards/forms.

### Modals / Drawers

- Start with modals for confirmations and small edit tasks.
- Use drawers only where preserving list context clearly improves workflows, especially Sources and Runs.
- If drawer support is deferred, keep navigation contracts compatible with future adoption.

### Empty / Loading / Error States

- Make these reusable partials with consistent title, body copy, optional icon, and CTA.
- Table and card containers should each support embedded state rendering.

## File / Module Structure

The repository snapshot does not currently expose template/static source files. To implement the revamp cleanly, introduce or restore a conventional FastAPI web asset structure under `app/web/`.

Recommended target structure:

```text
app/
  web/
    routes/
      dashboard.py
      jobs.py
      sources.py
      operations.py
    templates/
      base.html
      layouts/
        app_shell.html
      partials/
        sidebar.html
        topbar.html
        page_header.html
        alerts.html
        empty_state.html
        error_state.html
      macros/
        buttons.html
        forms.html
        table.html
        badges.html
        cards.html
        overlays.html
      pages/
        dashboard.html
        jobs/
          index.html
          detail.html
        sources/
          index.html
          form.html
          detail.html
        operations/
          source_health.html
          runs.html
    static/
      css/
        tokens.css
        base.css
        layout.css
        components.css
        utilities.css
        pages/
      js/
        ui-shell.js
        dropdown.js
        modal.js
        drawer.js
```

If the project already uses another internal web structure once source files are restored, apply the same logical layering there rather than duplicating directories.

## Page Migration Plan

### Phase 1: Foundation

1. Create token set and base CSS.
2. Implement app shell.
3. Implement shared page header.
4. Implement buttons, form controls, badges, alerts, tables, dropdowns.
5. Add reusable empty/loading/error state partials.

### Phase 2: Priority Pages

#### Dashboard

- Apply overview template.
- Add KPI card row.
- Add two-column summary region.
- Add recent activity container.
- Keep charts out unless already present and required.

#### Jobs

- Apply management table template.
- Build filter toolbar and state chip pattern.
- Normalize table density, row hover, sticky header, and action placement.

#### Sources

- Apply management table template.
- Surface source health/freshness more clearly via badges and supporting metadata.
- Standardize create/import actions in header.

### Phase 3: Operational Pages

- Migrate Source Health.
- Migrate Runs / run details.
- Use detail + activity template.
- Prefer summary strip + readable timeline/event blocks over raw dense layouts.

### Phase 4: Remaining Pages

- Apply approved templates only.
- Eliminate page-specific one-off controls where a shared component exists.
- Cleanup pass for spacing, responsiveness, and accessibility.

## Security and Access Control

This UI revamp does not introduce new authorization rules, but implementation must preserve access boundaries already enforced by FastAPI routes.

Frontend-specific requirements:

- do not render destructive controls to unauthorized users if authorization distinctions exist
- ensure CSRF strategy remains consistent with current form submission approach if applicable in the existing app architecture
- destructive actions must use explicit confirmation UI and entity naming
- avoid exposing sensitive adapter/source details in summary surfaces unless already intentionally visible

## Reliability / Operational Considerations

- All critical flows must work with full-page server rendering.
- JS enhancements must fail gracefully.
- Maintain stable layout during loading using skeleton placeholders and reserved container height.
- Standardize error surfaces so operational failures are visible but not visually chaotic.
- Use query-string state to reduce accidental context loss after refresh/back navigation.

## Dependencies and Constraints

### Confirmed Dependencies

- FastAPI
- Jinja2
- Python multipart/form handling

### Constraints

- Documentation-only task; no implementation changes in this step.
- Current repository snapshot lacks visible checked-in template/static source, so frontend file recommendations are necessarily target-state guidance grounded in FastAPI/Jinja conventions and the repo’s package metadata.
- Preserve backend workflows and terminology.
- Prefer minimal JavaScript and avoid SPA complexity.

## Assumptions

- HTML pages are or will be served by FastAPI with Jinja templates.
- Existing routes already cover Dashboard, Jobs, Sources, Source Health, and Runs or close equivalents.
- Existing backend data can support status summaries, lists, and timestamps needed by the redesigned UI.
- The team is willing to add a conventional `templates/` and `static/` source layout under `app/web/` if not already present outside this branch snapshot.

## Risks / Open Questions

### Risks

1. **Missing frontend source in current snapshot**
   - Risk: implementation may reveal different existing file locations or conventions.
   - Mitigation: preserve the logical architecture while adapting paths to actual restored source structure.

2. **Template drift during migration**
   - Risk: pages may partially adopt the new shell while keeping old component markup.
   - Mitigation: ship foundation first, then migrate page-by-page against shared macros.

3. **Responsive table complexity**
   - Risk: dense operational data may not fit smaller widths cleanly.
   - Mitigation: define column priority rules and allow stacked/secondary metadata rows on narrow screens.

4. **Drawer interaction overhead**
   - Risk: drawer behavior can introduce accessibility and focus-management defects.
   - Mitigation: modal/drawer JS should be centralized and introduced after core page rendering is stable.

### Open Questions

- Where are the current HTML templates and static assets in the implementation branch history?
- Are there existing frontend libraries already used for interactivity that should be retained?
- Are row-detail views currently separate pages, and which of them should remain page-based versus become drawers?
- Is there an authenticated user menu/settings surface that needs topbar accommodation now?
- Are flash messages and validation patterns already standardized on the backend?

## Accessibility and Responsiveness Implementation Considerations

### Accessibility

- Use semantic landmarks: `header`, `nav`, `main`, `aside`.
- Ensure one visible `h1` per page.
- Provide keyboard-operable sidebar drawer, dropdowns, modals, and drawers.
- Trap focus in modal/drawer overlays and return focus to invoker on close.
- Pair all status colors with text labels and, where useful, icons.
- Associate labels/help/error text with form fields using semantic HTML and ARIA only where necessary.
- Ensure table headers and row associations remain meaningful for screen readers.

### Responsiveness

- Desktop-first implementation with explicit breakpoints at roughly `1280`, `1024`, `768`.
- Collapse sidebar to drawer below `1024px`.
- Stack header actions and reduce multi-column regions below tablet widths.
- Collapse low-priority table columns before horizontal scroll.
- Keep minimum 40px touch targets for mobile/touch interactions.

## Implementation Notes for Downstream Agents

1. Treat this as a **design-system-first refactor**, not a page-by-page visual patch.
2. Implement foundation in this order:
   - tokens
   - base styles
   - app shell
   - page header
   - button/form/badge/alert primitives
   - table/filter toolbar
3. Use Jinja macros for every component with repeated markup.
4. Keep route handlers responsible for shaping template context; keep templates mostly declarative.
5. Use query params for filters, sorting, and pagination across Jobs and Sources.
6. Do not introduce a JS-heavy framework unless there is an explicit future architecture decision.
7. Migrate Dashboard, Jobs, and Sources first; only then move operational pages.
8. Build and review empty/loading/error states during each page migration rather than leaving them for a final pass.
9. Prefer drawers only where they materially preserve operator context; separate detail pages remain acceptable in v1 of the revamp.
10. Validate every migrated page against a checklist for shell consistency, action hierarchy, focus states, responsive behavior, and semantic status rendering.
