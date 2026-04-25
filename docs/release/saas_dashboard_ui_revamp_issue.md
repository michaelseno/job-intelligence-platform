# GitHub Issue

## 1. Feature Name

SaaS Dashboard UI Revamp

## 2. Problem Summary

The product currently presents as a set of functional but visually uneven operator screens rather than a cohesive, modern SaaS dashboard. Dashboard, Jobs, and Sources are the highest-visibility surfaces, but the same shell, design system, and interaction standards also need to extend to Source Health, Runs, and other operational pages without changing backend business logic, workflows, or terminology.

Because the repository currently has no configured git remote/origin, an actual GitHub issue could not be created from this environment. This local issue document is the required planning artifact for later release operations.

## 3. Linked Planning Documents
- Product Spec: Not currently available in this repository snapshot under `docs/product/...`
- Technical Design: `docs/architecture/saas_dashboard_ui_revamp.md`
- UI/UX Spec: `docs/uiux/saas_dashboard_ui_revamp.md`
- QA Test Plan: `docs/qa/saas_dashboard_ui_revamp_test_plan.md`

## 4. Scope Summary
- in scope
  - Unified SaaS-style application shell with persistent sidebar/top bar/page header patterns
  - Shared light-theme design system for typography, color, spacing, surfaces, borders, elevation, and interaction states
  - Reusable component standards for buttons, forms, dropdowns, tables, badges, alerts, modals, drawers, and empty/loading/error states
  - Frontend revamp of Dashboard, Jobs, and Sources first, then extension to Source Health, Runs/Run History, and remaining existing operational pages
  - Responsive behavior across desktop, laptop, tablet, and mobile widths
  - Accessibility baseline aligned to WCAG 2.1 AA expectations in planning documents
  - Regression-safe implementation that preserves existing workflows, terminology, and backend behavior
- out of scope
  - Backend domain logic changes
  - New product capabilities or major workflow redesign
  - Data model/schema changes beyond optional template/view-model shaping
  - SPA rewrite or adoption of a new frontend stack
  - Terminology overhaul beyond minor clarity improvements already allowed in planning

## 5. Implementation Notes
- frontend expectations
  - Implement as a server-rendered design-system and layout refactor aligned with the FastAPI/Jinja-style architecture described in planning
  - Add shared app shell, tokenized styling, reusable templates/macros/partials, and minimal progressive-enhancement JavaScript for drawer/menu/modal interactions
  - Prioritize Dashboard, Jobs, and Sources as P0 surfaces, then roll the same standards into Source Health, Runs, and remaining pages
  - Preserve GET-driven filter/sort/shareable page state where applicable
- backend expectations
  - No backend business logic changes are expected
  - Existing HTML routes should continue supplying page context, layout context, headers, collections, and UI-state data needed by templates
  - No persistent schema changes are required for this revamp
- dependencies or blockers
  - No `docs/product/...` artifact is currently present in the repository snapshot
  - Repository has no configured git remote/origin, so creating an actual GitHub issue is blocked from this environment
  - Current snapshot notes that source template/static frontend assets may be missing or incomplete, which may affect implementation planning detail
  - QA planning exists, but release progression later will still require explicit QA approval evidence before any push/PR steps

## 6. QA Section
- planned test coverage
  - Functional UI validation across shell, navigation, page headers, tables, forms, dialogs, states, and responsive layouts
  - Regression coverage for source create/edit/delete/import, job review/filtering, source health inspection, run history/detail review, and dashboard drill-in paths
  - Accessibility baseline checks, responsive testing, visual consistency review, and API/integration-backed workflow validation
- acceptance criteria mapping
  - All pages must share one shell, spacing rhythm, and component language
  - Dashboard, Jobs, and Sources must be the most polished/high-priority surfaces
  - Source Health and Runs must meet the same quality bar as core pages
  - Component behavior, state handling, and action hierarchy must be consistent across the application
  - No unintended workflow or terminology changes are permitted
- key edge cases
  - Empty datasets vs filtered no-results states
  - Never-run, warning, partial-success, and failed source/run states
  - Large tables, long names/URLs/metadata, and responsive action wrapping/collapsing
  - Validation failures, destructive action cancellation, stale refresh, duplicate submit prevention, and keyboard-only operation
- test types expected
  - Functional UI testing
  - Regression testing
  - Responsive testing
  - Accessibility baseline testing
  - Visual consistency review
  - Integration/API-backed workflow validation

## 7. Risks / Open Questions

- Broad UI changes may lead to uneven component adoption across pages if rollout is incomplete.
- Responsive regressions are likely on dense table and action-heavy pages.
- Visual polish work may accidentally alter wording, control placement, or destructive-action behavior.
- The repository snapshot suggests template/static asset structure may be incomplete or not committed, which could affect implementation sequencing.
- There is currently no product spec artifact under `docs/product/...`; confirm whether one should be added later for full planning traceability.
- There is currently no configured remote/origin, so GitHub issue creation and later remote release operations are blocked until repository remote configuration exists.
- No explicit QA approval artifact has been provided yet; later release manager steps that involve push/PR remain blocked until approval is documented.

## 8. Definition of Done

- Planning references for UI/UX, technical design, and QA test plan are linked and consistent.
- The frontend revamp is implemented across targeted pages using one cohesive shell, design system, and component standard.
- Dashboard, Jobs, and Sources meet P0 quality expectations, with Source Health, Runs, and remaining pages aligned to the same system.
- Existing workflows, terminology, and backend behavior remain unchanged except for approved UI improvements.
- Responsive and accessibility baseline requirements pass per the QA plan.
- Regression coverage confirms no task-blocking issues in core workflows.
- A formal QA report is produced and explicit approval is documented before any push/PR release actions.
- Remote repository configuration is available before attempting actual GitHub issue/PR operations.
