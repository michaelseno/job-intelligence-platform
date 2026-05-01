# Pull Request

## 1. Feature Name

Job Preference Location Groups

## 2. Summary

Enhances the Job Preference page Location section from a flat country list into a searchable accordion grouped country selector. The implementation adds global ISO 3166-1 country coverage, region-level select/deselect all behavior, mixed region states, and preserves existing country-based preference payloads without backend/API/data model changes.

Closes #18

## 3. Related Documents

- Product Spec: Not applicable; requirements were clear for this focused frontend UI enhancement and captured in the UI/UX and QA artifacts.
- Technical Design: Not applicable; no backend/API/data model changes are expected.
- UI/UX Spec: `docs/uiux/job_preference_location_groups_design_spec.md`
- QA Test Plan: `docs/qa/job_preference_location_groups_test_plan.md`
- Planning Issue: `docs/release/job_preference_location_groups_issue.md`
- Frontend Implementation Doc: `docs/frontend/job_preference_location_groups_implementation.md`
- QA Report: `docs/qa/job_preference_location_groups_test_report.md`
- QA Environment Blocker Report: `docs/bugs/job_preference_location_groups_qa_environment_blocker_bug_report.md`

## 4. Changes Included

- Replaced the flat Job Preferences Location country list with a searchable grouped accordion selector.
- Added ISO 3166-1 static country and region data for global location selection.
- Added region-level select/deselect all behavior with checked, unchecked, and mixed/indeterminate states.
- Preserved individual country selection and existing saved preference behavior unless changed and saved.
- Preserved country-based preference payloads; no region IDs are persisted.
- Added/updated frontend static and UI test coverage for location grouping behavior.
- Added planning, implementation, QA, and release traceability documentation.

## 5. QA Status

- Approved: YES
- QA gate: `[QA SIGN-OFF APPROVED]`
- HITL gate: `HITL validation successful`

## 6. Test Coverage

Validated evidence:

- `uv sync --extra dev` passed.
- `uv run python -m compileall app tests` passed.
- `node --check app/static/js/app.js` passed.
- `uv run python -m pytest tests/ui/test_configurable_job_preferences_ui.py tests/ui/test_job_preference_location_groups_static.py` passed, 8 passed.
- `uv run python -m pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py` passed, 13 passed.
- `uv run python -m pytest` passed, 120 passed.
- `node --test tests/js/job_preferences_helpers.test.mjs` passed, 14 passed.
- Direct FastAPI/TestClient `/job-preferences` smoke passed.
- Static country data integrity checks passed.
- Static UI/a11y/responsive marker checks passed.

## 7. Risks / Notes

- Frontend-only change; no backend/API/data model migration is included or expected.
- ISO country and region mapping is static frontend data and should remain deterministic.
- Region selections are UI behavior only; saved preferences remain country-based.
- Browser-level manual validation may still be useful for final visual review across supported browsers, especially mixed checkbox announcements and responsive layout.
- QA environment blocker was documented separately and did not prevent approved validation evidence.

## 8. Linked Issue

- Closes #18
