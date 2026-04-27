# Implementation Report

## 1. Summary of Changes
- Implemented the `/job-preferences` frontend page with editable role-family, role negative, work arrangement, location, and sponsorship preference criteria.
- Added browser localStorage preference handling, draft-vs-active state, client validation/normalization, Save API integration, client-side guards, and source-run preference injection.
- Added UI/template tests for navigation placement, page structure, scope boundaries, source-run integration hooks, and guarded pages.
- QA fix: draft dirty-state comparison now uses editable preference fields only, excluding metadata such as `configured_at`, so saved/default preferences do not falsely display `Unsaved changes`.
- Added lightweight Node-based JS tests with mocked `localStorage`/DOM for editable comparison, positive-signal usability, and source-run submit-time preference injection.
- HITL correction: replaced first-time all-fields setup with a four-step wizard for job categories, countries, work arrangement, and visa sponsorship. Advanced keyword fields are hidden during setup and available as a collapsed secondary section after setup.

## 2. Files Modified
- `app/web/routes.py`
- `app/templates/base.html`
- `app/templates/preferences/job_preferences.html`
- `app/templates/sources/index.html`
- `app/templates/sources/detail.html`
- `app/static/js/app.js`
- `app/static/css/app.css`
- `app/web/templates/base.html`
- `app/web/templates/preferences/job_preferences.html`
- `app/web/templates/sources/index.html`
- `app/web/templates/sources/detail.html`
- `app/web/static/app.js`
- `app/web/static/styles.css`
- `tests/ui/test_configurable_job_preferences_ui.py`
- `tests/js/job_preferences_helpers.test.mjs`
- `docs/frontend/configurable_job_preferences_implementation_plan.md`

## 3. UI Behavior Implemented
- First-time setup renders default editable criteria but does not store active preferences until Save succeeds.
- Existing saved preferences are read from `localStorage["job_intelligence.job_filter_preferences.v1"]` and displayed as Active.
- Draft edits show an Unsaved changes state and do not update active storage.
- Save preflights localStorage, trims/removes blanks, deduplicates case-insensitively, validates at least one positive signal, calls `/job-preferences/validate-and-reclassify`, and writes backend-normalized preferences only after success.
- Save loading, success, validation error, reclassification error, and localStorage unavailable states are represented with accessible alerts/status text.
- Preference-dependent pages are marked for client guard redirect to `/job-preferences?next=<original-path>` when no usable saved preferences exist.
- Source run forms read preferences at submit time and inject `job_preferences_json`.
- Dirty-state detection compares a canonical editable snapshot only; Save and Reset refresh the baseline to that same snapshot shape while preserving `configured_at` for storage/display.
- Client storage usability checks now reject preference objects with no positive signal before guards/source-run injection treat them as active.
- Wizard selections are mapped to the existing backend `JobFilterPreferences` DTO before Save/reclassification and source-run injection. The browser stores a localStorage envelope containing `wizard` metadata plus normalized `preferences`; backend requests submit only the mapped `preferences` object.
- Flexible / Any is exclusive and maps to unrestricted work arrangement criteria. Visa sponsorship No maps sponsorship lists to empty/neutral.

## 4. Assumptions Made
- Client-side guards are acceptable for HTML pages because localStorage cannot be read server-side without out-of-scope persistence.
- The combined validation/reclassification endpoint is the Save flow’s canonical normalization source.
- Existing app and app/web template/static trees were both updated to keep duplicated frontend shells consistent.

## 5. Validation Performed
- `pytest` and `python -m pytest` were unavailable directly in the shell.
- `python3 -m pytest tests/ui/test_configurable_job_preferences_ui.py` failed because pytest was not installed globally.
- `PYTHONPATH=. uv run --extra dev pytest tests/ui/test_configurable_job_preferences_ui.py` passed: `5 passed`.
- `node --check app/static/js/app.js` passed with no syntax errors.
- `PYTHONPATH=. uv run --extra dev pytest tests/api/test_configurable_job_preferences_api.py tests/integration/test_job_preferences_routes.py tests/integration/test_source_run_requires_preferences.py` could not run because the listed integration files are not present.
- `PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py` passed: `16 passed`.
- QA fix validation:
  - `node --check app/static/js/app.js && node --check app/web/static/app.js` passed.
  - `node --test tests/js/job_preferences_helpers.test.mjs` passed: `8 passed`.
  - `PYTHONPATH=. uv run --extra dev pytest tests/ui/test_configurable_job_preferences_ui.py` passed: `5 passed`.
  - `PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py` passed: `17 passed`.
  - `PYTHONPATH=. uv run --extra dev pytest` passed: `75 passed`.
  - HITL wizard validation:
    - `node --check app/static/js/app.js && node --check app/web/static/app.js` passed.
    - `node --test tests/js/job_preferences_helpers.test.mjs` passed: `14 passed`.
    - `PYTHONPATH=. uv run --extra dev pytest tests/ui/test_configurable_job_preferences_ui.py` passed: `6 passed`.
    - `PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py` passed: `18 passed`.
    - `PYTHONPATH=. uv run --extra dev pytest` passed: `76 passed`.

## 6. Known Limitations / Follow-Ups
- No full browser test harness exists, but lightweight Node JS tests now exercise the canonical comparison helpers, localStorage usability check, and source-run submit injection with mocked browser objects. Manual browser QA is still required for rendered focus movement, actual refresh behavior, and visual status transitions.
- Guards are client-side and may allow a brief server-rendered page flash before redirect.
- The role-family UI supports the current five editable families; arbitrary add/remove family controls were not added.

## 7. Commit Status
- Not committed. The user explicitly requested no git commits, no push, and no PR.
