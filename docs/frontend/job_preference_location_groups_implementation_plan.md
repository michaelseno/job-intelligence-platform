# Implementation Plan

## 1. Feature Overview
Enhance the Job Preferences Location step with a searchable grouped country checklist backed by static ISO 3166-1 frontend data while preserving the existing country-based preference contract.

## 2. Technical Scope
- Replace the flat country render with native `details` region accordions.
- Add region select-all/deselect-all and native mixed checkbox state.
- Keep `input[name="selected_countries"]` values as country IDs only.
- Add local search across country label, stable ID, aliases/keywords, and region label.

## 3. UI/UX Inputs
- `docs/uiux/job_preference_location_groups_design_spec.md`
- `docs/qa/job_preference_location_groups_test_plan.md`
- `docs/release/job_preference_location_groups_issue.md`

## 4. Files Expected to Change
- `app/templates/preferences/job_preferences.html`
- `app/static/js/app.js`
- `app/static/css/app.css`
- `tests/ui/test_job_preference_location_groups_static.py`
- `docs/frontend/job_preference_location_groups_implementation.md`

## 5. Dependencies / Constraints
- Frontend-only implementation; no backend/API/model changes.
- Static country data remains in the existing JS bundle.
- Existing localStorage envelope, wizard, save, and reclassification flow must remain intact.

## 6. Assumptions
- The frontend revamp uses `app/templates` and `app/static`; legacy `app/web` files are not active in this UI path.
- Unknown legacy country IDs are warned about and are not written to generated country keywords.

## 7. Validation Plan
- Run existing pytest suite or targeted UI tests.
- Run Python compile check.
- Run a JS syntax check with Node if available.
