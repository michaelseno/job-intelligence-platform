# Implementation Plan

## 1. Feature Overview
Implement the browser-facing Job Preferences setup/edit page at `/job-preferences`, using localStorage as the active preference store and backend validation/reclassification for Save.

## 2. Technical Scope
- Replace the minimal backend HTML shell with a Jinja page using the shared layout.
- Add client-side preference form population, draft state, validation/normalization, Save API integration, localStorage persistence, route guards, and source-run preference injection.
- Keep saved preferences browser-local under `job_intelligence.job_filter_preferences.v1`.
- Preserve role-family grouping and all required criteria categories.

## 3. UI/UX Inputs
- Dedicated primary-nav page labelled `Job Preferences`.
- First-time setup shows editable defaults but remains `Setup required` until Save succeeds.
- Existing saved preferences load as `Active`; edits show `Unsaved changes`.
- Save shows loading, validation errors, storage errors, and success with reclassified count.

## 4. Files Expected to Change
- `app/web/routes.py`
- `app/web/templates/preferences/job_preferences.html`
- `app/web/templates/base.html`
- `app/web/templates/sources/index.html`
- `app/web/templates/sources/detail.html`
- `app/web/static/app.js`
- `app/web/static/styles.css`
- `tests/ui/test_configurable_job_preferences_ui.py`
- `docs/frontend/configurable_job_preferences_implementation_report.md`

## 5. Dependencies / Constraints
- Backend contracts already exist for `/job-preferences`, `/job-preferences/validate-and-reclassify`, `/jobs/reclassify`, and `/sources/{source_id}/run`.
- No auth, DynamoDB, backend preference persistence, custom weights, or unrelated UI changes.
- Existing server-rendered UI and BeautifulSoup-style tests are the available automated frontend conventions.

## 6. Assumptions
- Browser guards are implemented client-side because localStorage is not server-readable.
- Source-run HTML forms can be marked with data attributes and populated at submit time.
- The Save endpoint’s combined validation/reclassification response is the canonical source for normalized saved values.

## 7. Validation Plan
- Add UI/template tests for nav order, page structure, field inventory, accessibility attributes, and source-run form integration hooks.
- Run the targeted UI tests and relevant route/API tests if feasible.
- Manually reason through JS localStorage behavior; no JS-capable test harness exists in this repo.
