# Test Report

Feature: Hide Rejected Job Openings  
Branch: `feature/hide_rejected_job_openings`  
QA date: 2026-04-25

## 1. Execution Summary

### Automated test execution

| Command | Scope | Result |
|---|---|---|
| `./.venv/bin/python -m pytest tests/unit/test_job_visibility.py tests/integration/test_hide_rejected_job_openings_surfaces.py tests/ui/test_hide_rejected_job_openings_ui.py -q` | Feature unit, integration, and UI validation | **13 passed / 0 failed** |
| `./.venv/bin/python -m pytest tests/integration/test_html_views.py tests/integration/test_api_flow.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/api/test_source_delete_job_cleanup_api.py tests/ui/test_source_edit_delete_ui_qa.py -q` | Relevant Jobs/Dashboard/source-delete regression coverage | **17 passed / 0 failed** |
| `./.venv/bin/python -m pytest -q` | Full repository suite | **49 passed / 5 failed** |

### Summary counts

- Critical feature-targeted tests: **13 total / 13 passed / 0 failed**
- Relevant regression tests: **17 total / 17 passed / 0 failed**
- Full suite: **54 total / 49 passed / 5 failed**

The 5 full-suite failures are isolated to `tests/ui/test_saas_dashboard_ui_revamp.py` and are classified as unrelated test harness/data expectation issues, not defects in Hide Rejected Job Openings.

### Acceptance criteria validation

| AC | QA Result | Evidence |
|---|---|---|
| AC-01: Rejected jobs hidden from main Jobs display. | Pass | `test_jobs_api_excludes_rejected_and_keeps_null_unknown_visible`; `test_jobs_page_omits_rejected_rows_and_cards`. |
| AC-02: Review jobs remain visible. | Pass | API and UI tests show review fixtures remain in `/jobs` and dashboard previews. |
| AC-03: Matched jobs remain visible. | Pass | API and UI tests show matched fixtures remain in `/jobs` and dashboard previews. |
| AC-04: Counts reflect eligible non-rejected jobs only. | Pass | Dashboard JSON asserts `matched_count == 1`, `review_count == 1`, `rejected_count == 0`; UI asserts `2 actionable job(s) found.` |
| AC-05: Rejected exclusion applied before count/pagination. | Pass with current architecture note | Current implementation has no pagination. Code inspection confirms `/jobs` starts from `apply_main_display_jobs(select(JobPosting))` before bucket/search/source/sort handling. |
| AC-06: Search matching only rejected jobs returns empty/no-results. | Pass | `test_jobs_filters_do_not_reintroduce_rejected_jobs` asserts `/jobs?search=Rejected%20Only` returns `[]`. |
| AC-07: Existing filters do not reintroduce rejected jobs. | Pass | Bucket rejected, shared search, and source filter tests pass; regression suites passed. |
| AC-08: Review -> rejected disappears after refresh/reload. | Pass | `test_reclassification_transitions_affect_main_display_without_deleting_records`. |
| AC-09: Rejected -> matched/review appears after refresh/reload when eligible. | Pass | `test_reclassification_transitions_affect_main_display_without_deleting_records` validates rejected -> matched visibility. |
| AC-10: Rejected jobs are not deleted. | Pass | Tests assert rejected record still exists and remains `latest_bucket == "rejected"` after Jobs access. |
| AC-11: All-rejected data shows normal empty state. | Pass | `test_all_rejected_jobs_render_normal_empty_state`; `/jobs?bucket=rejected` UI empty state validated. |
| AC-12: Analytics/telemetry counts based on filtered visible set or distinguished. | Pass / not applicable | No dedicated analytics/telemetry event path found; dashboard count contract uses filtered actionable set. |

### Additional QA validations

- `/jobs` excludes rejected records and includes `matched`, `review`, `NULL`, and unknown non-rejected buckets.
- `/jobs?bucket=rejected` returns an empty result set and does not reveal rejected payloads.
- Jobs page bucket selector exposes only `All actionable`, `Matched`, and `Review`; no `Rejected` option is rendered.
- Dashboard actionable counts/previews exclude rejected jobs and do not render a `/jobs?bucket=rejected` link.
- Direct rejected job detail route remains unchanged for source-visible rejected jobs; JSON detail returns 200 with `latest_bucket == "rejected"`.
- Source-delete visibility composition remains covered by passing regression tests.
- Rejected records are not deleted, archived, or reclassified by list/dashboard access.

## 2. Failed Tests

Full-suite failures from `./.venv/bin/python -m pytest -q`:

1. `tests/ui/test_saas_dashboard_ui_revamp.py::test_dashboard_renders_html_shell`
   - Error: expected `text/html`, received `application/json`.
   - Relevant log: response body was JSON dashboard counts: `{"matched_count":0,"review_count":0,"rejected_count":0,...}`.

2. `tests/ui/test_saas_dashboard_ui_revamp.py::test_jobs_index_renders_management_table_ui`
   - Error: expected `text/html`, received `application/json`.
   - Relevant log: response body was `[]`.

3. `tests/ui/test_saas_dashboard_ui_revamp.py::test_job_detail_renders_html_detail_view`
   - Error: expected status `200`, received `404` for `/jobs/1`.
   - Relevant log: `{"detail":"Job not found."}`.

4. `tests/ui/test_saas_dashboard_ui_revamp.py::test_sources_index_renders_management_table_ui`
   - Error: expected `text/html`, received `application/json`.
   - Relevant log: response body was `[]`.

5. `tests/ui/test_saas_dashboard_ui_revamp.py::test_source_detail_renders_html_detail_view`
   - Error: failed to find source detail link in `/sources` response.
   - Relevant log: `/sources` response body was `[]`.

## 3. Failure Classification

| Failed test | Classification | Feature-related? | Rationale |
|---|---|---:|---|
| `test_dashboard_renders_html_shell` | Test Bug / Harness Issue | No | Test requests `/dashboard` without `Accept: text/html` but asserts HTML shell. Existing route returns JSON unless HTML is requested. Feature-specific dashboard HTML tests request `Accept: text/html` and pass. |
| `test_jobs_index_renders_management_table_ui` | Test Bug / Harness Issue | No | Test requests `/jobs` without `Accept: text/html` but asserts HTML. JSON `[]` is expected for an empty test DB/API request. Feature-specific Jobs UI tests request HTML and pass. |
| `test_job_detail_renders_html_detail_view` | Test Data Issue | No | Test assumes `/jobs/1` exists without seeding a job. Failure is 404 due to missing fixture, not rejected-job filtering. |
| `test_sources_index_renders_management_table_ui` | Test Bug / Harness Issue | No | Test requests `/sources` without `Accept: text/html` but asserts HTML. JSON `[]` is expected for an empty source list/API request. |
| `test_source_detail_renders_html_detail_view` | Test Data / Harness Issue | No | Test expects an HTML source link in a JSON empty response and does not seed source data. |

No failed test shows a rejected job leaking into `/jobs`, `/jobs?bucket=rejected`, dashboard counts/previews, or an unintended mutation/deletion of rejected records.

## 4. Observations

- The implementation uses `apply_main_display_jobs(select(JobPosting))` for `/jobs` and dashboard actionable loading, which supports query-layer filtering rather than UI-only hiding.
- `actionable_job_status_predicate()` explicitly includes `NULL` buckets and excludes only `latest_bucket == "rejected"`, matching the technical design.
- Direct job detail uses `apply_visible_jobs()` rather than `apply_main_display_jobs()`, preserving detail access behavior for source-visible rejected jobs.
- The full-suite failures are stable and reproducible; they are not flaky and are unrelated to the new feature.
- Current `/jobs` implementation has no pagination, so pagination acceptance was validated by query-layer placement and current architectural constraints rather than page-boundary execution.

## 5. QA Decision

APPROVED

All critical Hide Rejected Job Openings validations passed. Remaining full-suite failures are unrelated/pre-existing UI test harness and fixture assumptions.

[QA SIGN-OFF APPROVED]

---

## 6. Regression Re-check After Source Active Checkbox Fix

Fix commit re-checked: `3b33e28 Fix source active checkbox parsing`  
Regression QA date: 2026-04-25

### Automated regression execution

| Command | Scope | Result |
|---|---|---|
| `./.venv/bin/python -m pytest tests/unit/test_job_visibility.py tests/integration/test_hide_rejected_job_openings_surfaces.py tests/ui/test_hide_rejected_job_openings_ui.py -q` | Hide-rejected targeted unit/integration/UI regression | **13 passed / 0 failed** |
| `./.venv/bin/python -m pytest tests/integration/test_html_views.py tests/integration/test_api_flow.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/api/test_source_delete_job_cleanup_api.py tests/ui/test_source_edit_delete_ui_qa.py -q` | Related Jobs/Dashboard/source-delete regression | **17 passed / 0 failed** |
| `./.venv/bin/python -m pytest tests/unit tests/api tests/integration -q` | Backend/API/integration suites | **39 passed / 0 failed** |
| `./.venv/bin/python -m pytest -q` | Full repository suite | **54 passed / 5 failed** |

### Regression result

Hide Rejected Job Openings remains approved after the source active checkbox/run blocker fix. Targeted tests continue to validate:

- `/jobs` excludes rejected jobs and retains matched/review/null/unknown non-rejected jobs.
- `/jobs?bucket=rejected` returns no rejected records.
- Dashboard actionable counts/previews exclude rejected jobs.
- Jobs UI bucket selector exposes actionable options only.
- Direct rejected job detail behavior remains unchanged.

The remaining 5 full-suite failures are still isolated to `tests/ui/test_saas_dashboard_ui_revamp.py` and remain classified as unrelated HTML Accept-header/test fixture assumptions.

[QA SIGN-OFF APPROVED]
