# Bug Report

## 1. Summary

QA rejected configurable job filter preferences due to three issues: a confirmed frontend draft-vs-active comparison defect that falsely reports `Unsaved changes`, deterministic full-suite regressions after source-run requests began requiring preferences, and missing JS-capable browser automation for critical `localStorage` lifecycle behavior.

## 2. Investigation Context

- Source of report: QA rejection in `docs/qa/configurable_job_preferences_qa_report.md`.
- Branch context: `feature/configurable_job_filter_preferences`.
- Related feature/workflow: configurable Job Preferences at `/job-preferences`; browser `localStorage` persistence; source ingestion with submitted job preferences.
- Planning issue: <https://github.com/michaelseno/job-intelligence-platform/issues/10>.
- Relevant QA command that failed: `PYTHONPATH=. uv run --extra dev pytest` (`12 failed, 63 passed`).
- Representative repro command run during investigation:

```bash
PYTHONPATH=. uv run --extra dev pytest tests/api/test_source_edit_delete_qa.py::test_deleted_and_nonexistent_source_endpoints_return_not_found tests/integration/test_html_views.py::test_dashboard_and_jobs_html_render tests/integration/test_source_edit_delete_html.py::test_source_created_with_true_checkbox_can_run_without_inactive_conflict tests/ui/test_source_edit_delete_ui_qa.py::test_source_delete_confirmation_explains_async_cleanup_and_retention tests/ui/test_source_edit_delete_ui_qa.py::test_deleted_source_non_retained_job_uses_normal_not_found
```

Investigation result for the representative command: `5 failed in 0.17s`, matching QA's failure pattern.

## 3. Observed Symptoms

### F-1: Frontend status becomes `Unsaved changes` without user edits

- Failing workflow: `/job-preferences` page load, saved preference load, and post-Save lifecycle.
- Exact QA evidence:
  - `baseline = activePreferences || defaults` includes backend/default metadata such as `configured_at`.
  - `collectDraft()` creates a draft object without `configured_at`.
  - `updateDraftState()` compares `JSON.stringify(draft)` to `JSON.stringify(baseline)`.
- Expected behavior:
  - First-time setup displays `Setup required` with defaults inactive until Save.
  - Saved preferences display `Active`.
  - Successful Save remains `Active` after the save handler completes.
- Actual behavior risk:
  - The status can incorrectly become `Unsaved changes` immediately after first load, loading saved preferences, Reset, or successful Save.

### F-2: Full regression suite fails after source-run preference enforcement

- Failing command from QA: `PYTHONPATH=. uv run --extra dev pytest`.
- QA output excerpt: `12 failed, 63 passed`.
- Reproduced representative failures:
  - `tests/api/test_source_edit_delete_qa.py::test_deleted_and_nonexistent_source_endpoints_return_not_found`: `assert 409 == 404`.
  - `tests/integration/test_html_views.py::test_dashboard_and_jobs_html_render`: `IndexError: list index out of range` after `client.post(f"/sources/{source['id']}/run")` creates no jobs.
  - `tests/integration/test_source_edit_delete_html.py::test_source_created_with_true_checkbox_can_run_without_inactive_conflict`: `assert 409 == 200`.
  - `tests/ui/test_source_edit_delete_ui_qa.py::test_source_delete_confirmation_explains_async_cleanup_and_retention`: `assert 409 == 200`.
  - `tests/ui/test_source_edit_delete_ui_qa.py::test_deleted_source_non_retained_job_uses_normal_not_found`: `assert 409 == 200`.
- Expected behavior:
  - Existing deleted/nonexistent source endpoints retain `404` semantics.
  - Legacy tests that intentionally exercise successful source ingestion should pass valid default preferences under the new contract.
- Actual behavior:
  - Missing preferences return `409` before deleted/nonexistent source identity is checked.
  - Multiple older tests still call `/sources/{source_id}/run` without `job_preferences`, so ingestion is blocked and downstream assertions fail.

### F-3: JS browser lifecycle remains unautomated

- Failing validation gap: no JS-capable harness executes `localStorage`, DOM lifecycle, focus behavior, client guards, or source-run submit-time injection.
- Expected behavior: QA must have manual browser evidence or automated JS/browser coverage for Save/load/refresh/focus/source-run injection behavior.
- Actual behavior: current automated UI checks are static FastAPI/BeautifulSoup tests and `node --check` syntax checks only.

## 4. Evidence Collected

Files inspected:

- `docs/qa/configurable_job_preferences_qa_report.md`
- `docs/product/configurable_job_preferences_product_spec.md`
- `docs/architecture/configurable_job_preferences_architecture.md`
- `docs/uiux/configurable_job_preferences_uiux.md`
- `docs/qa/configurable_job_preferences_test_plan.md`
- `docs/backend/configurable_job_preferences_implementation_report.md`
- `docs/frontend/configurable_job_preferences_implementation_report.md`
- `app/static/js/app.js`
- `app/web/static/app.js`
- `app/web/routes.py`
- `tests/api/test_source_edit_delete_qa.py`
- `tests/integration/test_html_views.py`
- `tests/integration/test_source_edit_delete_html.py`
- `tests/ui/test_source_edit_delete_ui_qa.py`

Key frontend evidence:

- `app/static/js/app.js:159-160` and `app/web/static/app.js:119-120`: `preferencesEqual()` uses raw `JSON.stringify` equality.
- `app/static/js/app.js:197-198` and `app/web/static/app.js:157-158`: `baseline = activePreferences || defaults`.
- `app/static/js/app.js:258-268` and `app/web/static/app.js:238-248`: `collectDraft()` returns only criteria fields and `schema_version`; it does not include `configured_at`.
- `app/static/js/app.js:273-277` and `app/web/static/app.js:254-263`: `updateDraftState()` derives `Unsaved changes` from `!preferencesEqual(draft, baseline)`.
- `app/static/js/app.js:315-335` and `app/web/static/app.js:325-358`: after successful Save, `baseline = normalized`, then `finally` calls `updateDraftState()`, reintroducing the metadata mismatch.

Key backend/test evidence:

- Architecture contract, `docs/architecture/configurable_job_preferences_architecture.md:280-312`: `/sources/{source_id}/run` requires preferences with `409` for missing, `422` for invalid, while existing `404`/`409` source errors remain unchanged.
- Backend route, `app/web/routes.py:770-775`: missing/invalid preferences are checked before source lookup.
- Backend route, `app/web/routes.py:776-783`: source lookup and `404` occur only after preference validation.
- Test expectation, `tests/api/test_source_edit_delete_qa.py:56-71`: deleted and nonexistent `POST /sources/{id}/run` endpoints are expected to return `404`.
- Legacy tests still call source run without preferences:
  - `tests/integration/test_html_views.py:39`, `:67`
  - `tests/integration/test_source_edit_delete_html.py:143`
  - `tests/ui/test_source_edit_delete_ui_qa.py:64`, `:185`
- Reproduced test output confirms representative failures are deterministic, not flaky.

Coverage-gap evidence:

- QA Test Plan notes existing UI tests use FastAPI `TestClient`/BeautifulSoup and no Playwright configuration is present (`docs/qa/configurable_job_preferences_test_plan.md:16-20`, `:127-158`, `:254`).
- Frontend implementation report explicitly lists the limitation: no JS-capable browser test harness for `localStorage`, focus movement, or submit-time hidden field injection (`docs/frontend/configurable_job_preferences_implementation_report.md:47-50`).

## 5. Execution Path / Failure Trace

### F-1

1. `/job-preferences` initializes defaults from server data and reads any active preferences from `localStorage`.
2. `baseline` is assigned to the active/default preference object, which may contain `configured_at`.
3. The page populates DOM fields from `baseline`.
4. `collectDraft()` reconstructs a criteria-only object from form fields and omits `configured_at`.
5. `updateDraftState()` compares the criteria-only draft to the metadata-bearing baseline via `JSON.stringify`.
6. The objects differ solely due to metadata, so the UI reports `Unsaved changes` despite no user edit.

### F-2

1. Legacy tests create a source and call `POST /sources/{source_id}/run` without preferences.
2. `run_source()` parses the request and finds no `job_preferences` / `job_preferences_json`.
3. `run_source()` returns `409` at `app/web/routes.py:770-771` before adapter execution or source lookup.
4. Tests expecting successful ingestion receive `409`, so no jobs are created and downstream list/detail assertions fail.
5. Deleted/nonexistent source run requests also receive `409` before source lookup, masking the existing `404` not-found contract.

### F-3

1. Static HTML tests verify templates and form hooks but do not execute browser JavaScript.
2. `node --check` verifies syntax only.
3. No current automated validation executes the exact paths where F-1 occurs: `localStorage` read/write, post-Save `finally`, refresh load, focus behavior, source form hidden-field injection, and client guards.

## 6. Failure Classification

| Failure | Primary classification | Severity | Reproducibility |
|---|---|---|---|
| F-1 frontend active/draft state defect | Application Bug | Blocker | Always reproducible by code path; browser execution still needs manual/JS-harness evidence |
| F-2a source `404` masked by missing-preference `409` | Application Bug / Contract Mismatch | Medium, blocking for QA sign-off as part of full-suite failure | Always reproducible |
| F-2b legacy tests call source-run without preferences | Test Bug | Blocker for sign-off until maintained | Always reproducible |
| F-3 missing JS browser lifecycle automation/evidence | Environment / Configuration Issue | Medium; currently blocks sign-off because it hides critical untested behavior | Cannot reproduce dynamic behavior with current harness |

Severity justification:

- F-1 is a blocker because it violates AC-1 through AC-5 and undermines the save-gated UX.
- F-2 is blocking for QA sign-off because the full regression suite is red. The source-run not-found masking is Medium product severity but must be fixed/classified before release.
- F-3 is Medium as a tooling gap, but must be addressed with manual evidence or automation before approval because the unexecuted path already contains a real defect.

## 7. Root Cause Analysis

### F-1: Confirmed Root Cause

- Immediate failure point: `updateDraftState()` marks the page changed when `preferencesEqual(draft, baseline)` is false.
- Underlying root cause: frontend equality compares objects with different shapes. `baseline` can include `configured_at`; `collectDraft()` intentionally omits metadata; raw JSON equality treats metadata-only differences as unsaved edits.
- Supporting evidence: `baseline = activePreferences || defaults`, `collectDraft()` criteria-only object, `preferencesEqual()` raw stringify comparison, and post-Save `finally` calls `updateDraftState()` after `baseline = normalized`.

### F-2a: Most Likely Root Cause

- Immediate failure point: deleted/nonexistent `POST /sources/{id}/run` returns missing-preference `409` instead of not-found `404`.
- Underlying root cause: `run_source()` validates preferences before checking whether the source exists or is deleted.
- Supporting evidence: `app/web/routes.py:770-775` precedes `SourceService(...).get_runnable_source(source_id)` at `:776-783`; test `tests/api/test_source_edit_delete_qa.py:56-71` expects `404` for deleted/nonexistent source run endpoints; architecture says existing `404` source errors remain unchanged.
- Confidence is slightly below confirmed because product/backend should confirm desired precedence for missing preferences vs nonexistent resource, but architecture strongly supports preserving `404`.

### F-2b: Confirmed Root Cause

- Immediate failure point: legacy tests receive `409` or no jobs after calling source run without preferences.
- Underlying root cause: tests were not updated to satisfy the new `/sources/{source_id}/run` contract where successful classification-triggering ingestion requires submitted preferences.
- Supporting evidence: architecture and implementation report both state source ingestion requires preferences; failing tests still call `client.post(f"/sources/{id}/run")` without JSON/form preferences.

### F-3: Confirmed Coverage Gap

- Immediate failure point: current automated QA cannot execute JS/browser lifecycle behavior.
- Underlying root cause: repository lacks a JS-capable browser harness; current UI tests inspect static HTML only.
- Supporting evidence: QA report and test plan state no Playwright/Selenium-style harness exists; frontend report lists localStorage/focus/source-submit as manual follow-ups.

## 8. Confidence Level

High.

The frontend state defect is directly supported by source code shape/equality evidence. Representative backend/test regressions were reproduced locally with the same failure signatures as QA. The coverage gap is documented in the QA plan and frontend report. The only medium-certainty item is exact response precedence for nonexistent source plus missing preferences, but architecture explicitly states existing source `404` errors remain unchanged.

## 9. Recommended Fix

### F-1 routing: Frontend

- Likely owner: Frontend.
- Likely files: `app/static/js/app.js` and duplicated `app/web/static/app.js`.
- Recommended correction:
  - Normalize/canonicalize preference objects before draft-vs-baseline comparison, excluding metadata such as `configured_at` and comparing only criteria fields in stable order.
  - Ensure `baseline` after Save and Reset uses the same comparable shape as `collectDraft()`, or update `preferencesEqual()` to compare canonical criteria-only objects.
  - Preserve `configured_at` for display/storage; do not include it in unsaved-change detection.
  - Keep both duplicated static JS trees synchronized.
- Caution: do not solve by adding `configured_at` to drafts, because drafts are not active persisted preferences and timestamps should not define user-edit state.

### F-2a routing: Backend

- Likely owner: Backend.
- Likely file/function: `app/web/routes.py::run_source`.
- Recommended correction:
  - Check source existence/deleted-state before returning missing-preference `409` for `/sources/{source_id}/run`, while still avoiding adapter fetch/classification when preferences are missing.
  - Preserve inactive-runnable conflict behavior (`409`) for existing non-runnable sources as appropriate.
  - Keep missing-preference `409` for existing runnable sources that omit preferences.
- Caution: ensure the reordered flow does not fetch from adapters before preference validation.

### F-2b routing: QA/test maintenance, with backend support if fixtures need helpers

- Likely owner: QA/test.
- Likely files:
  - `tests/integration/test_html_views.py`
  - `tests/integration/test_source_edit_delete_html.py`
  - `tests/ui/test_source_edit_delete_ui_qa.py`
  - Other full-suite failures listed in QA report with source-run setup paths.
- Recommended correction:
  - Add a shared default valid preference fixture/payload, likely based on `get_default_job_filter_preferences().model_dump()`, for tests that expect successful source ingestion/classification.
  - Preserve explicit negative tests that intentionally omit preferences and expect `409`.
  - For HTML/form source-run tests, submit `job_preferences_json` when exercising server behavior without JS.

### F-3 routing: QA automation / Frontend QA

- Likely owner: QA/test automation with Frontend support.
- Recommended correction:
  - Add a JS-capable browser harness (for example Playwright) or capture manual browser evidence before sign-off.
  - Minimum required checks: initial setup state, Save success storage write, refresh active display, unsaved draft behavior, failed validation/reclassification preserving prior storage, focus to success/error alerts, client guard redirect, and source-run submit-time preference injection.

## 10. Suggested Validation Steps

After fixes, rerun:

```bash
node --check app/static/js/app.js && node --check app/web/static/app.js
PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py
PYTHONPATH=. uv run --extra dev pytest tests/api/test_source_edit_delete_qa.py::test_deleted_and_nonexistent_source_endpoints_return_not_found
PYTHONPATH=. uv run --extra dev pytest tests/integration/test_html_views.py tests/integration/test_source_edit_delete_html.py tests/ui/test_source_edit_delete_ui_qa.py tests/ui/test_saas_dashboard_ui_revamp.py
PYTHONPATH=. uv run --extra dev pytest
```

Manual or browser-automation validation required for F-1/F-3:

1. Empty `localStorage`, open `/job-preferences`: status is `Setup required`, not `Unsaved changes`; no active preference is written before Save.
2. Save valid preferences: backend succeeds, `localStorage["job_intelligence.job_filter_preferences.v1"]` is written, status remains `Active` after the handler completes.
3. Refresh `/job-preferences`: saved values display and status is `Active`, not `Unsaved changes`.
4. Edit one field without saving: status becomes `Unsaved changes`; refresh/navigate does not promote draft changes.
5. Trigger validation/reclassification failure: prior active preferences remain in `localStorage`, focus moves to error alert.
6. Submit a source run form after saved preferences exist: `job_preferences_json` is injected from current `localStorage` at submit time.
7. Direct `/jobs` or `/dashboard` without usable preferences redirects/guards to `/job-preferences?next=<path>`.

Expected passing behavior: targeted configurable preference tests pass, selected regression suites pass, full pytest suite passes, and browser lifecycle evidence shows correct setup/active/unsaved states.

## 11. Open Questions / Missing Evidence

- Product/backend should explicitly confirm error precedence for `POST /sources/{missing_or_deleted_id}/run` when preferences are also missing. Architecture currently indicates existing source `404` errors remain unchanged.
- No JS-capable browser harness exists in the repository, so F-1 was confirmed by code-path inspection rather than an automated browser execution trace.
- The full list of all 12 failing full-suite tests should be rechecked after the representative source-run fixes/test updates, because some failures may collapse once shared fixtures are updated.

## 12. Final Investigator Decision

Ready for developer fix.

Route F-1 to Frontend, F-2a to Backend, F-2b to QA/test maintenance, and F-3 to QA automation/Frontend QA for manual evidence or a browser harness.
