# Implementation Plan

## 1. Feature Overview
Implement a frontend-only fix for the Jobs filter form so optional empty filters are omitted from the submitted GET query string instead of being serialized as empty parameters.

## 2. Technical Scope
- Update the Jobs filter form to opt into query cleanup behavior.
- Add lightweight client-side GET form serialization that drops empty string values before navigation.
- Keep existing filter control values, submission flow, and reset behavior unchanged.

## 3. UI/UX Inputs
- Primary input: `docs/bugs/source-filter-empty-query-param-bug_report.md`
- Supporting UI/UX input: `docs/uiux/job_intelligence_platform_mvp_uiux_spec.md`
- `technical_design.md` was not present in the repository at implementation time.

## 4. Files Expected to Change
- `app/web/templates/jobs/list.html`
- `app/web/static/app.js`
- `docs/frontend/source_filter_empty_query_param_implementation_plan.md`
- `docs/frontend/source_filter_empty_query_param_implementation_report.md`

## 5. Dependencies / Constraints
- Server-rendered Jinja templates with lightweight progressive enhancement only.
- Must not change backend contracts in this task.
- Must avoid disturbing unrelated untracked files.

## 6. Assumptions
- Omitting all empty query values for the Jobs filter form is acceptable and preserves expected filter semantics.
- JavaScript is already an accepted progressive enhancement layer for small interaction fixes in this app.

## 7. Validation Plan
- Run targeted Python test coverage for HTML views.
- Run a lightweight compile check for app and test modules.
- Manually review the rendered form and client script changes for query-cleanup behavior.
