# Test Report

Feature/Fix: Source Active Checkbox Run Blocker  
Branch: `feature/hide_rejected_job_openings`  
Fix commit: `3b33e28 Fix source active checkbox parsing`  
QA date: 2026-04-25

## 1. Execution Summary

### Automated test execution

| Command | Scope | Result |
|---|---|---|
| `./.venv/bin/python -m pytest tests/integration/test_source_edit_delete_html.py -q` | Source create/edit checkbox parsing and run-blocker regression | **7 passed / 0 failed** |
| `./.venv/bin/python -m pytest tests/unit/test_job_visibility.py tests/integration/test_hide_rejected_job_openings_surfaces.py tests/ui/test_hide_rejected_job_openings_ui.py -q` | Hide Rejected Job Openings targeted regression | **13 passed / 0 failed** |
| `./.venv/bin/python -m pytest tests/integration/test_html_views.py tests/integration/test_api_flow.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/api/test_source_delete_job_cleanup_api.py tests/ui/test_source_edit_delete_ui_qa.py -q` | Related HTML/API/source-delete regression | **17 passed / 0 failed** |
| `./.venv/bin/python -m pytest tests/unit tests/api tests/integration -q` | Backend/API/integration suites | **39 passed / 0 failed** |
| `./.venv/bin/python -m pytest -q` | Full repository suite | **54 passed / 5 failed** |

### Validation requirements status

| Requirement | QA Result | Evidence |
|---|---|---|
| Source creation with checked checkbox value `true` persists active. | Pass | `test_source_create_form_accepts_true_checkbox_value` passed; DB assertion verifies `source.is_active is True`. |
| Source creation with checked checkbox value `on` persists active. | Pass | `test_source_create_form_accepts_on_checkbox_value` passed; DB assertion verifies `source.is_active is True`. |
| Omitted checkbox persists inactive if intended. | Pass | `test_source_create_form_omitted_checkbox_persists_inactive` passed; aligns with implementation assumption that missing checkbox means unchecked/inactive. |
| Edit flow uses corrected active-state parsing. | Pass | `test_source_edit_form_accepts_true_checkbox_value` passed; inactive source updated to active via HTML edit form with `is_active=true`. |
| Active source does not fail immediately with inactive-source 409 on `Run now`. | Pass | `test_source_created_with_true_checkbox_can_run_without_inactive_conflict` passed using mocked Greenhouse HTTP response; run returned 200 with expected `source_id`, not inactive-source 409. |
| Hide-rejected-jobs feature remains valid. | Pass | Targeted hide-rejected unit/integration/UI suite passed 13/13. |
| Remaining full-suite failures inspected/classified. | Pass | All 5 failures remain isolated to `tests/ui/test_saas_dashboard_ui_revamp.py`; see classification below. |

## 2. Failed Tests

Full-suite failures from `./.venv/bin/python -m pytest -q`:

1. `tests/ui/test_saas_dashboard_ui_revamp.py::test_dashboard_renders_html_shell`
   - Error: expected `text/html`, received `application/json`.
   - Relevant log: response body was JSON dashboard counts: `{"matched_count":0,"review_count":0,"rejected_count":0,...,"source_count":1}`.

2. `tests/ui/test_saas_dashboard_ui_revamp.py::test_jobs_index_renders_management_table_ui`
   - Error: expected `text/html`, received `application/json`.
   - Relevant log: response body was `[]`.

3. `tests/ui/test_saas_dashboard_ui_revamp.py::test_job_detail_renders_html_detail_view`
   - Error: expected status `200`, received `404` for `/jobs/1`.
   - Relevant log: `{"detail":"Job not found."}`.

4. `tests/ui/test_saas_dashboard_ui_revamp.py::test_sources_index_renders_management_table_ui`
   - Error: expected `text/html`, received `application/json`.
   - Relevant log: response body was JSON source data from the non-isolated app database, not an HTML shell.

5. `tests/ui/test_saas_dashboard_ui_revamp.py::test_source_detail_renders_html_detail_view`
   - Error: failed to find an HTML source link in `/sources` response.
   - Relevant log: `/sources` returned JSON source data, so the HTML-link regex could not match.

## 3. Failure Classification

| Failed test | Classification | Related to checkbox fix? | Related to hide-rejected feature? | Rationale |
|---|---|---:|---:|---|
| `test_dashboard_renders_html_shell` | Test Bug / Harness Issue | No | No | Test requests `/dashboard` without `Accept: text/html` while route returns JSON by default. HTML-specific tests using the correct Accept header pass. |
| `test_jobs_index_renders_management_table_ui` | Test Bug / Harness Issue | No | No | Test requests `/jobs` without `Accept: text/html` while route returns JSON by default. Hide-rejected HTML UI tests use the correct Accept header and pass. |
| `test_job_detail_renders_html_detail_view` | Test Data Issue | No | No | Test assumes `/jobs/1` exists without creating a job fixture; 404 is expected when no such job exists. |
| `test_sources_index_renders_management_table_ui` | Test Bug / Environment Data Issue | No | No | Test requests `/sources` without `Accept: text/html` and uses the global app client outside isolated DB fixtures; JSON response is not evidence of source active parsing failure. |
| `test_source_detail_renders_html_detail_view` | Test Bug / Environment Data Issue | No | No | Test parses an HTML link from a JSON response and does not use isolated seeded HTML fixture flow. |

No failed full-suite test demonstrates that a checked `true`/`on` checkbox persists inactive, that active source run flow is blocked with inactive-source 409, or that rejected jobs leak into Jobs/Dashboard surfaces.

## 4. Observations

- Code inspection confirms `parse_form_checkbox()` treats `None` as `False` and accepts `on`, `true`, `1`, and `yes` as truthy.
- `parse_source_form()` now uses `parse_form_checkbox(form.get("is_active"))`; source create and edit flows share this parser.
- Run validation used a mocked Greenhouse adapter HTTP response (`{"jobs": []}`) to avoid live network dependency and isolate the inactive-source blocker behavior.
- Hide-rejected regression remains stable after commit `3b33e28`: `/jobs`, `/jobs?bucket=rejected`, dashboard actionable counts/previews, direct detail behavior, null/unknown visibility, and UI filter behavior remain covered by passing targeted tests.
- Existing full-suite UI revamp failures remain stable and unrelated to both this fix and hide-rejected job visibility.

## 5. QA Decision

APPROVED

The source active checkbox/run blocker fix meets validation requirements, and the Hide Rejected Job Openings feature remains valid after regression testing. Remaining full-suite failures are unrelated test harness/data issues.

[QA SIGN-OFF APPROVED]
