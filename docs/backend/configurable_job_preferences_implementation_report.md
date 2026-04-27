# Implementation Report

## 1. Summary of Changes
Implemented backend preference validation/default helpers, refactored classification and source ingestion to require supplied preferences, and added reclassification APIs for configurable job filter preferences.

## 2. Files Modified
- `app/domain/job_preferences.py`: added preference DTO, defaults, validation, and active-job reclassification helper.
- `app/domain/classification.py`: replaced runtime constant reads with supplied `JobFilterPreferences` while preserving scoring mechanics.
- `app/domain/ingestion.py`: requires preferences for source runs and passes them to classification.
- `app/web/routes.py`: added preference endpoints, source-run preference parsing/enforcement, safe `next` handling, and nav metadata entry.
- `tests/unit/test_job_preferences_validation.py`: added validator coverage.
- `tests/unit/test_classification_preferences.py`: added custom/default classification coverage.
- `tests/unit/test_classification.py`: updated existing classification test to pass default preferences explicitly.
- `tests/api/test_configurable_job_preferences_api.py`: added API coverage for save/reclassify and missing source-run preferences.
- `tests/integration/test_api_flow.py`: updated source-run calls to provide preferences.

## 3. API Contract Implementation
Implemented `GET /job-preferences`, `POST /job-preferences/validate-and-reclassify`, `POST /jobs/reclassify`, and preference enforcement for `POST /sources/{source_id}/run` with `409` for missing preferences and `422` for invalid preferences.

## 4. Data / Persistence Implementation
No backend preference persistence, tables, migrations, sessions, cookies, or DynamoDB resources were added. Reclassification writes existing `JobDecision` / `JobDecisionRule` history and updates `JobPosting.latest_bucket`, `latest_score`, and `latest_decision_id`.

## 5. Key Logic Implemented
Validation trims entries, drops blanks, deduplicates case-insensitively within category/family, enforces schema version and bounds, preserves role-family grouping, and requires at least one positive signal.

HITL correction: classification now treats all three empty sponsorship keyword lists as sponsorship disabled/neutral. In neutral mode, sponsorship keyword matching, score deltas, and missing/ambiguous/unsupported sponsorship bucket gates are skipped while default/Visa-required sponsorship behavior remains unchanged.

## 6. Security / Authorization Implemented
No auth added. Client-controlled preferences are revalidated on each classification-triggering backend path. Raw preferences are not persisted server-side.

## 7. Error Handling Implemented
Missing preferences return `409`. Invalid structure/schema/limits return structured `422` errors. Save reclassification failures roll back and return `500` without instructing frontend to promote preferences.

## 8. Observability / Logging
No new logging was added; implementation avoids logging raw preference values.

## 9. Assumptions Made
The backend `/job-preferences` HTML response is a minimal setup shell for frontend integration; full localStorage UI behavior remains frontend scope.

## 10. Validation Performed
- `pytest ...` failed: `pytest` command not found.
- `python -m pytest ...` failed: `python` command not found.
- `python3 -m pytest ...` failed: global Python has no `pytest` installed.
- `./.venv/bin/python -m pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/integration/test_api_flow.py` passed: `17 passed in 0.31s`.

QA failure follow-up validation:
- `PYTHONPATH=. uv run --extra dev pytest tests/api/test_source_edit_delete_qa.py::test_deleted_and_nonexistent_source_endpoints_return_not_found` passed: `1 passed in 0.08s`.
- `PYTHONPATH=. uv run --extra dev pytest tests/integration/test_html_views.py tests/integration/test_source_edit_delete_html.py tests/ui/test_source_edit_delete_ui_qa.py tests/ui/test_saas_dashboard_ui_revamp.py` passed after fixes: `23 passed in 0.59s`.
- `PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py` passed: `17 passed in 0.21s`.
- `PYTHONPATH=. uv run --extra dev pytest` passed: `75 passed in 2.31s`.

Visa-neutral HITL correction validation:
- `PYTHONPATH=. uv run --extra dev pytest tests/unit/test_classification_preferences.py` passed: `9 passed in 0.08s`.
- `node --check app/static/js/app.js && node --check app/web/static/app.js` passed with no output.
- `node --test tests/js/job_preferences_helpers.test.mjs` passed: `14 passed`.
- `PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py` passed: `24 passed in 0.30s`.
- `PYTHONPATH=. uv run --extra dev pytest` passed: `82 passed in 2.38s`.

## 11. Known Limitations / Follow-Ups
Frontend must still address the QA-reported `configured_at` draft-vs-active comparison defect and provide manual or automated browser evidence for localStorage lifecycle behavior.

## 12. Commit Status
Initial backend implementation was committed previously. QA/HITL follow-up fixes were intentionally not committed per instruction.
