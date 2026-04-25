# Implementation Plan

## 1. Feature Overview
Revamp the server-rendered Job Intelligence Platform UI into a cohesive light-theme SaaS dashboard, prioritizing Dashboard, Jobs, and Sources, then extending the same shell and component language to source health, runs, tracking, digest, and reminders.

## 2. Technical Scope
- Rehydrate the missing Python source surface by wiring source modules back to compiled application artifacts.
- Introduce a shared template shell, reusable UI macros, and tokenized CSS/JS assets.
- Replace page-by-page HTML with a unified sidebar/topbar/page-header system.
- Refresh management tables, forms, alerts, badges, empty states, and detail layouts without changing route behavior.

## 3. UI/UX Inputs
- `docs/uiux/saas_dashboard_ui_revamp.md`
- `docs/architecture/saas_dashboard_ui_revamp.md`
- `docs/qa/saas_dashboard_ui_revamp_test_plan.md`
- `docs/release/saas_dashboard_ui_revamp_issue.md`

## 4. Files Expected to Change
- `app/main.py`
- `app/web/routes.py`
- compiled-module wrapper files under `app/`
- shared templates under `app/templates/`
- shared static assets under `app/static/`
- frontend implementation docs under `docs/frontend/`

## 5. Dependencies / Constraints
- Existing backend behavior must remain driven by the compiled application artifacts present in the branch.
- No SPA rewrite, backend contract changes, or push/PR operations.
- Keep light theme only.

## 6. Assumptions
- The checked-in source tree is incomplete, so thin source wrappers around compiled modules are acceptable to restore runnable application behavior.
- Existing HTML routes still provide the context variables observed from the compiled routes module.
- Tests exist only as compiled cache artifacts, so validation will rely on direct runtime smoke checks unless source tests are restored.

## 7. Validation Plan
- Compile the restored source tree.
- Run TestClient-based HTML smoke coverage for core routes.
- Exercise source create/edit/delete HTML flows and key Jobs UI regressions.
