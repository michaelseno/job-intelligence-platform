# Test Plan

## 1. Feature Overview

### Scope and objectives
- Validate the Frontend Revamp / UI Enhancement defined in `docs/uiux/saas_dashboard_ui_revamp.md` across the full application shell and page inventory.
- Prioritize verification of Dashboard, Jobs, and Sources as the highest-visibility surfaces, while ensuring Source Health, Runs/Run History, and remaining operational pages follow the same design system and interaction patterns.
- Confirm the revamp delivers bold visual and layout improvements without changing existing workflows, terminology, backend behavior, or core task completion paths.
- Verify the product presents as one cohesive SaaS dashboard through consistent navigation, hierarchy, surfaces, states, and responsive behavior.

### In-scope
- Global app shell: sidebar, top bar, page header, breadcrumbs, action placement, active navigation behavior.
- Dashboard, Jobs, Sources, Source Health, Runs/Run History, and other existing pages included in the current UI.
- Shared components: buttons, forms, selects/dropdowns, tables, badges, alerts, toasts, modals, drawers, empty/loading/error states.
- Responsive behavior across desktop, laptop, tablet, and mobile breakpoints called out in the spec.
- Accessibility baseline: keyboard access, visible focus, labeling, contrast, status communication, modal/drawer behavior, zoom to 200%.
- Regression coverage to confirm no unintended workflow or terminology changes.

### Out-of-scope
- New product capabilities not already supported by the application.
- Backend/business logic changes, data model changes, and API contract redesign.
- Content strategy or terminology overhaul beyond minor label cleanup already permitted by the spec.
- Deep non-functional certification beyond baseline UI performance and baseline accessibility/security checks.
- Browser/device matrix expansion beyond the agreed QA environment unless separately requested.

## 2. Acceptance Criteria Mapping

| Spec outcome / requirement | QA validation approach |
|---|---|
| All pages share one shell, spacing rhythm, and component language | Compare page layouts across primary and secondary pages; verify common sidebar/top bar/header/tokens/patterns are reused consistently. |
| Dashboard, Jobs, and Sources are visibly the most polished surfaces | Execute priority visual, navigation, state, and workflow checks on those pages first; compare against surrounding pages for consistency. |
| Source Health / Runs feel first-class, not leftover admin pages | Verify shell parity, typography, spacing, status summaries, readable event detail blocks, and aligned action hierarchy. |
| Primary, secondary, tertiary, and danger actions are distinct and consistently placed | Review headers, toolbars, forms, dialogs, and row actions for hierarchy, placement, and destructive-action separation. |
| Forms, dropdowns, modals, and drawers use one unified standard | Validate layout, heights, labels, helper/error text, keyboard support, focus trapping, and submit/cancel patterns across surfaces. |
| Tables are readable, scannable, and balanced in density | Verify headers, row height, sticky header behavior, hover state, column priority, status chips, actions, and responsive collapse behavior. |
| Empty/loading/success/error states are present and professionally written | Trigger each state where feasible and confirm explanatory copy, recovery CTA, and layout stability. |
| Light theme is modern SaaS and enterprise-credible | Perform visual review against token guidance: neutral canvas/surfaces, restrained brand usage, consistent borders/radius/elevation. |
| Responsive behavior is defined and works at desktop/laptop/tablet/mobile | Validate layout changes around 1280px+, 1024-1279px, 768-1023px, and <768px. |
| Accessibility baseline is met | Run keyboard-only, focus visibility, semantic labeling, contrast, live-region/state communication, modal escape/focus, and zoom checks. |
| No workflow logic or terminology is unintentionally changed | Run regression scenarios using existing tasks/labels for navigation, filtering, create/edit/delete/import, inspection, and health/run review. |

## 3. Test Strategy by Area

### Visual consistency
- Compare global shell, typography hierarchy, spacing rhythm, surfaces, borders, shadows, icon usage, and status colors across all pages.
- Validate sentence case for headings/actions and consistent treatment of cards, toolbars, tables, and notices.
- Confirm bold visual refresh does not introduce page-specific visual paradigms outside approved templates.

### Navigation
- Verify persistent left sidebar behavior on desktop, compact/collapsible behavior on laptop, and drawer behavior on tablet/mobile.
- Confirm active nav state, breadcrumb/section labeling, page titles, and header actions clearly indicate current context.
- Validate navigation between Dashboard, Jobs, Sources, Source Health, Runs, and remaining pages preserves expected user context where applicable.

### Forms
- Validate create/edit/import forms for consistent field layout, labels, helper text, required markers, inline validation, submission states, and footer actions.
- Confirm destructive actions remain separated from standard form actions.
- Verify terminology in labels/help text remains aligned with existing workflows.

### Actions
- Validate primary CTA prominence in headers and sections.
- Confirm secondary/tertiary actions remain available but not visually dominant.
- Verify dangerous actions require explicit confirmation and name the affected entity.

### Tables
- Validate toolbar + filter placement, sticky headers, scannable rows, chip semantics, row hover/focus states, row actions, and stable sorting/filtering/pagination behavior.
- Confirm smaller viewports collapse lower-priority columns before forcing unusable horizontal scrolling.

### Modals / drawers
- Validate open/close behavior, titles/descriptions, action ordering, focus trap, escape dismissal, overlay click behavior if intended, and context return after close.
- Confirm inspect/edit flows preserve list context where the existing workflow expects it.

### Empty states
- Validate true no-data empty states vs filtered no-results states.
- Confirm pages explain purpose, why content is empty, and the next recommended action.

### Responsiveness
- Validate at 1440/1280, 1024, 768, and 375/390 widths.
- Confirm action wrapping, card stacking, table adaptation, drawer/nav behavior, and minimum touch target sizing.

### Accessibility baseline
- Keyboard-only navigation on primary flows.
- Visible focus indicators on all interactive controls.
- Associated labels/errors for form fields.
- Status not conveyed by color alone.
- Table headers/semantics preserved.
- Modal/drawer focus trap and escape support.
- 200% zoom without blocking task completion.

### Regression
- Re-run current high-value workflows to ensure the visual revamp has not altered logic or terminology: source creation, source edit/delete, CSV import, job review/filtering, source health inspection, run history inspection, and dashboard drill-in paths.

## 4. Priority Test Scenarios

### Dashboard (P0)
1. Dashboard loads within the new app shell with correct active navigation, page title, supporting description, and action placement.
2. KPI/status cards render consistently, use correct semantic emphasis, and remain readable at all supported widths.
3. Attention-needed sections and recent activity blocks use consistent card/table styling and clear hierarchy.
4. Empty, loading, and error variants are distinct and actionable.
5. Dashboard terminology and destination links preserve existing concepts and navigation paths.

### Jobs (P0)
1. Jobs index uses management-table template with header, filter/action toolbar, summary chips if present, and primary data table.
2. Existing filters/search/sort controls remain usable and visually consistent.
3. Job rows preserve current terminology and status meaning while improving scanability.
4. Row action behavior, detail view, or drawer/inspect flow preserves context and filter state.
5. Dense datasets remain readable, with sticky header and stable column behavior at narrower widths.
6. No-results, empty, loading, and request-failure states are differentiated.

### Sources (P0)
1. Sources index uses management-table template with clear primary actions such as Add source / Import CSV when applicable.
2. Source rows clearly expose source name, adapter type, health/status, last run/last success, and management actions.
3. Add, edit, delete, and import flows keep current workflow terminology and provide consistent validation and confirmation UX.
4. Source detail/expansion/drawer surfaces recent run outcomes and metadata without losing originating list context.
5. Long names/URLs/metadata truncate safely and remain inspectable.
6. Healthy, warning/stale, failed, manual/system, and in-progress states use accessible status chips.

### Source Health / Runs (P1)
1. These pages match the main shell and no longer feel like separate internal utilities.
2. Failure/warning summaries, latest run outcome, timestamps, and retry/view-detail actions are prominently organized.
3. Event/timeline/log groupings remain readable and structured under the new visual system.
4. Error, partial success, and never-run states are clearly differentiated.

### Remaining pages (P1/P2)
1. Each remaining page adopts one of the approved templates rather than introducing a one-off layout.
2. Shared controls match the same design system and interaction rules.
3. Page-specific explanatory copy is sufficient for operational/config pages without changing terminology.

## 5. Negative / Edge Cases

- No jobs exist yet after a new source is added.
- Source exists but has never run.
- Source run partially succeeds with warnings.
- All sources are failing and the UI must communicate risk without becoming unreadable.
- Large job result sets with many filters, long scrolling, and sticky headers.
- Long source names, URLs, company names, or adapter metadata.
- Validation failures on create/edit/import forms, including required fields and malformed inputs.
- Empty search/filter results distinct from global no-data state.
- Destructive action cancellation, stale page refresh, duplicate-submit prevention, and retry after recoverable failure.
- Responsive edge cases where actions wrap, columns collapse, or drawers/modals compete for limited viewport space.
- Keyboard-only interaction through filters, menus, dialogs, drawers, and table actions.

## 6. Manual and Automated Test Recommendations

### Manual testing
- Cross-page visual review against the UI/UX spec using side-by-side screenshots at defined breakpoints.
- Exploratory walkthroughs of Dashboard, Jobs, and Sources with emphasis on operator efficiency and demo readiness.
- Accessibility spot checks using keyboard-only navigation, browser zoom, and screen-reader smoke checks on representative pages.
- Regression walkthroughs for source management, job review, and run/health investigation workflows.

### Automated testing
- UI regression tests in `tests/ui/` for shell/navigation, page headers, core actions, empty/error states, and representative responsive layouts.
- API/integration tests in `tests/api/` and `tests/integration/` to confirm UI-supported workflows still return expected data/state transitions.
- Visual snapshot coverage for Dashboard, Jobs, Sources, and at least one secondary operational page if tooling is available.
- Accessibility automation (for example, Playwright + axe or equivalent) on primary pages and dialogs.
- Smoke tests for create/edit/delete/import flows to ensure visual refactoring did not break existing behavior.

## 7. Risks and Test Data / Environment Assumptions

### Risks
- Broad UI changes may create inconsistent component adoption across pages.
- Responsive regressions are likely where dense tables and action-heavy headers coexist.
- Visual polish work can accidentally shift workflow wording, control placement, or destructive-action behavior.
- Server-rendered/progressively enhanced implementations may introduce state-preservation differences across pages.
- Existing QA coverage appears workflow-oriented; additional visual/accessibility automation may need to be introduced.

### Test data assumptions
- Test environment includes representative data for jobs, sources, source health states, and run history.
- Seed data should include healthy, warning, failed, never-run, empty, and large-volume scenarios.
- At least one source each for manual creation, CSV import, and integrated adapters should be available where supported.

### Environment assumptions
- QA can validate in at least one Chromium-based browser at desktop and mobile widths, plus one secondary browser for smoke checks if required.
- Build/deployment under test exposes all existing pages referenced in the spec.
- Feature flags, if any, are configured to show the revamp consistently across targeted surfaces.

## 8. Sign-off Criteria

QA approval for this revamp is granted only when all of the following are satisfied:
- All P0 scenarios for Dashboard, Jobs, and Sources pass.
- No blocking defects exist in navigation, primary workflows, destructive confirmations, or form submission/validation behavior.
- Source Health / Runs and remaining pages meet the same shell/component standards with no major visual inconsistency.
- Responsive checks pass for the required breakpoints with no task-blocking layout issues.
- Accessibility baseline issues are resolved or reduced to non-blocking follow-ups explicitly accepted by stakeholders.
- Regression testing confirms no unintended workflow or terminology changes.
- Test execution evidence is captured in the corresponding QA report.

When those conditions are fully met, final QA approval must be expressed exactly as:

`[QA SIGN-OFF APPROVED]`

Until then, approval must not be issued.

## 9. Test Types Covered

- Functional UI validation
- Regression testing
- Responsive testing
- Accessibility baseline testing
- Basic visual consistency review
- Integration/API-backed workflow validation
