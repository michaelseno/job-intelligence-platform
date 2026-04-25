# Implementation Plan

## 1. Feature Overview

Hide rejected job openings from the main Jobs UI and dashboard actionable presentation while preserving direct detail access and backend filtering implemented upstream.

## 2. Technical Scope

- Remove the visible `Rejected` bucket option from server-rendered Jobs list templates.
- Update the default bucket copy to `All actionable`.
- Keep stale/manual `/jobs?bucket=rejected` rendering as a normal empty actionable-jobs state.
- Remove the user-facing rejected stat card/link from dashboard templates where present.
- Add frontend/UI regression coverage for Jobs filter options, empty states, hidden rejected rows/cards, and dashboard rejected-card removal.

## 3. UI/UX Inputs

- Product Spec: `docs/product/hide_rejected_job_openings_product_spec.md`
- Technical Design: `docs/architecture/hide_rejected_job_openings_technical_design.md`
- UI/UX Spec: `docs/uiux/hide_rejected_job_openings_uiux_spec.md`
- QA Test Plan: `docs/qa/hide_rejected_job_openings_test_plan.md`

## 4. Files Expected to Change

- `app/templates/jobs/list.html`
- `app/web/templates/jobs/list.html`
- `app/templates/dashboard/index.html`
- `app/web/templates/dashboard/index.html`
- `tests/ui/test_hide_rejected_job_openings_ui.py`
- `docs/frontend/hide_rejected_job_openings_implementation_plan.md`
- `docs/frontend/hide_rejected_job_openings_implementation_report.md`

## 5. Dependencies / Constraints

- Backend query-layer filtering from commit `1971d70` is authoritative and must not be undone.
- No rejected-jobs management page or show-rejected toggle is in scope.
- Duplicate template paths must remain consistent because the active Jinja search path uses `app/templates` first while older tests/specs still reference `app/web/templates`.

## 6. Assumptions

- `app/templates/*` is the active rendered template set for current HTML routes due to Jinja template search order.
- `app/web/templates/*` is still maintained as a duplicate/fallback template set.
- Existing backend behavior ensures rejected jobs are absent from Jobs/Dashboard data; frontend changes should avoid exposing stale rejected navigation affordances.

## 7. Validation Plan

- Run targeted UI tests for this feature.
- Run related HTML/dashboard regression tests.
- Run backend hide-rejected integration tests to confirm frontend changes do not conflict with upstream behavior.
