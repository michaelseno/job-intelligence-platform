# Implementation Plan

## 1. Feature Overview
Implement backend support for configurable Job Filter Preferences supplied per classification/reclassification request.

## 2. Technical Scope
Add in-memory preference validation/default helpers, refactor classification and source ingestion to require validated preferences, and expose validation/reclassification API endpoints.

## 3. Source Inputs
- `docs/architecture/configurable_job_preferences_architecture.md`
- `docs/product/configurable_job_preferences_product_spec.md`
- `docs/qa/configurable_job_preferences_test_plan.md`
- `docs/release/configurable_job_preferences_issue.md`

## 4. API Contracts Affected
- `GET /job-preferences`: returns setup metadata/defaults for JSON clients and simple HTML shell for browser setup.
- `POST /job-preferences/validate-and-reclassify`: accepts `JobFilterPreferences`, validates/normalizes, reclassifies active jobs, returns normalized preferences and count; `422` invalid, `500` reclassification failure.
- `POST /jobs/reclassify`: accepts `{ "job_preferences": ... }`, returns `{ "jobs_reclassified": n }`; `409` missing, `422` invalid.
- `POST /sources/{source_id}/run`: now requires preferences via JSON `job_preferences` or form `job_preferences_json`; `409` missing, `422` invalid.

## 5. Data Models / Storage Affected
No backend preference persistence or schema changes. Existing job decision rows and `JobPosting.latest_*` fields are updated during classification/reclassification.

## 6. Files Expected to Change
- `app/domain/job_preferences.py`
- `app/domain/classification.py`
- `app/domain/ingestion.py`
- `app/web/routes.py`
- Backend tests under `tests/unit/` and `tests/api/`

## 7. Security / Authorization Considerations
No auth added. Backend revalidates client-controlled preference payloads, limits keyword counts/lengths, rejects missing preferences for classification-triggering routes, and does not persist raw preferences.

## 8. Dependencies / Constraints
No new dependencies. Preserve current scoring weights, bucket rules, low-text confidence, and role-family grouping.

## 9. Assumptions
The backend HTML setup page may be a minimal shell; full localStorage UI behavior is handled by frontend scope.

## 10. Validation Plan
- `pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py`
- `pytest tests/api/test_configurable_job_preferences_api.py`
