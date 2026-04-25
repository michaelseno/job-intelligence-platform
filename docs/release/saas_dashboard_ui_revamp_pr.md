# Pull Request

## 1. Feature Name

SaaS Dashboard UI Revamp

## 2. Summary
This branch delivers the full frontend revamp planned for the application shell and page inventory, then follows up on QA findings to ensure browser/default requests render HTML correctly across the revamp surfaces.
It also adds responsive and accessibility polish for sidebar navigation so the updated UI is safer to release for desktop, laptop, and mobile usage.

## 3. Related Documents
- Product Spec: Not currently available in this repository snapshot under `docs/product/...`
- Technical Design: `docs/architecture/saas_dashboard_ui_revamp.md`
- UI/UX Spec: `docs/uiux/saas_dashboard_ui_revamp.md`
- QA Report: `docs/qa/saas_dashboard_ui_revamp_report.md`
- QA Test Plan: `docs/qa/saas_dashboard_ui_revamp_test_plan.md`
- Release Issue: `docs/release/saas_dashboard_ui_revamp_issue.md`
- Implementation Notes: `docs/frontend/saas_dashboard_ui_revamp_implementation.md`

## 4. Changes Included
- Ships the SaaS dashboard shell, design-system styling, and shared frontend assets across Dashboard, Jobs, Sources, Source Health, Runs, Tracking, Digest, and Reminders
- Fixes route wrapper behavior so browser/default requests resolve to HTML for revamp pages while explicit JSON requests continue to work for the covered routes
- Adds QA follow-up accessibility and responsive updates including skip link support, mobile drawer backdrop/escape handling, focus return and trapping, sticky table headers, and compact laptop navigation behavior
- Adds targeted UI smoke coverage for the HTML-first sources flow and records planning, QA, and release documentation for the feature
- Key components affected: `app/templates/base.html`, `app/static/css/app.css`, `app/static/js/app.js`, `app/web/routes.py`, `tests/ui/test_saas_dashboard_ui_revamp.py`, and revamp planning/QA/release docs

## 5. QA Status
- Approved: YES
- Approval evidence: `[QA SIGN-OFF APPROVED]`

## 6. Test Coverage
- Targeted pytest coverage via `PYTHONPATH="/Users/mjseno/Documents/Development/Development/job-intelligence-platform" ".venv/bin/pytest" tests/ui/test_saas_dashboard_ui_revamp.py -q`
- FastAPI `TestClient` route matrix for browser/default HTML responses across primary and secondary revamp pages
- Explicit `Accept: application/json` fallback spot checks on covered routes
- Regression-style HTML flow checks for source validation, jobs filters, and source edit/delete screens
- Coverage types executed: functional UI, regression, responsive/accessibility smoke validation, and route-behavior verification

## 7. Risks / Notes
- `docs/product/...` artifact is still not present in this repository snapshot
- The implementation still depends on compiled wrapper behavior in `app/web/routes.py`, which remains a maintainability risk
- The compact laptop nav improves density but uses text-hidden iconless pills, so discoverability is weaker than the ideal icon-rail target
- QA documented a non-blocking inconsistency where explicit `Accept: application/json` on `/dashboard` still returns `500`
