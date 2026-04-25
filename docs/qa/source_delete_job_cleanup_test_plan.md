# Test Plan

## 1. Feature Overview

Feature: source deletion asynchronously cleans up associated jobs while preserving only jobs that are both `latest_bucket = matched` and `current_state = active`.

When a source is deleted, the source must be removed from active configuration immediately, cleanup must be queued/started asynchronously, and normal user-facing surfaces must immediately hide non-retained jobs from the deleted source even before physical deletion completes.

Primary upstream artifacts:
- Product Spec: `docs/product/source_delete_job_cleanup_product_spec.md`
- Technical Design: `docs/architecture/source_delete_job_cleanup_technical_design.md`
- UI/UX Spec: `docs/uiux/source_delete_job_cleanup_uiux_spec.md`

Existing test/tooling alignment observed:
- Python/FastAPI/SQLAlchemy test stack using `pytest` and `fastapi.testclient.TestClient`.
- Existing fixture pattern in `tests/conftest.py` creates an in-memory SQLite DB and overrides the app DB dependency.
- Existing test locations: `tests/unit/`, `tests/api/`, `tests/integration/`, and `tests/ui/`.
- Relevant prior source delete coverage exists in `tests/unit/test_source_edit_delete.py`, `tests/api/test_source_edit_delete_qa.py`, `tests/integration/test_source_edit_delete_html.py`, and `tests/ui/test_source_edit_delete_ui_qa.py`.

## 2. Acceptance Criteria Mapping

| AC | Requirement | Planned Coverage |
|---|---|---|
| AC-01 | Deleted source disappears from active source lists, filters, and ingestion actions immediately. | API, HTML/UI, and integration tests for source list, jobs source filter, source detail/run/delete endpoints after deletion. |
| AC-02 | Cleanup is queued/started without synchronously deleting every associated job before response. | API tests asserting delete response includes cleanup queued/status fields and background task scheduling hook is called; integration test verifies response completes while cleanup can be controlled/mocked separately. |
| AC-03 | Associated matched active job is retained. | Unit cleanup service test and integration surface test. |
| AC-04 | Associated matched inactive/non-active job is permanently deleted. | Unit cleanup service data matrix and API/integration cleanup verification. |
| AC-05 | Associated non-matched active job is permanently deleted. | Unit cleanup service data matrix for `review`, `rejected`, and other non-matched buckets. |
| AC-06 | Associated job with no current classification bucket is permanently deleted. | Unit cleanup service data matrix with `latest_bucket = None`. |
| AC-07 | Review/rejected jobs are deleted regardless of tracking/manual keep/reminders/digest. | Unit/integration tests with tracking events, reminders, digest items, and manual keep/tracking status. |
| AC-08 | After cleanup, only matched active jobs remain associated with deleted source. | Unit cleanup verification querying `job_postings` and `job_source_links` after cleanup. |
| AC-09 | Pending-cleanup non-retained jobs do not appear in dashboard, job list, or summary counts. | Integration/UI tests soft-delete source without running cleanup, then assert dashboard/jobs/counts hide non-retained jobs immediately. |
| AC-10 | Deleted job detail URL returns normal not-found. | API and HTML detail tests after cleanup and during pending-cleanup logical-hide window. |
| AC-11 | Retained matched active jobs remain visible when filters match. | Integration/UI tests for dashboard/jobs/detail with retained job. |
| AC-12 | Retained jobs may show deleted source provenance as historical/non-actionable. | UI tests for retained job detail/source evidence: deleted label if shown; no run/edit/source-management action for deleted source. |
| AC-13 | Cleanup is idempotent and retry-safe. | Unit test invoking cleanup twice and after partial pre-deletion; assert retained job remains and no duplicate/uncaught failures. |
| AC-14 | Cleanup failure does not roll back source deletion; stale jobs remain hidden. | Unit/API failure injection test; integration visibility test after simulated cleanup failure. |
| AC-15 | Source with zero associated jobs deletes successfully without visible cleanup error. | API and UI tests for empty-source delete flow and cleanup no-op success. |

## 3. Test Scenarios

### 3.1 Backend Unit Tests

Recommended files:
- `tests/unit/test_source_delete_cleanup.py`
- `tests/unit/test_job_visibility.py`

Coverage:
1. Cleanup association discovery selects distinct jobs where either:
   - `job_postings.primary_source_id = deleted_source_id`, or
   - `job_source_links.source_id = deleted_source_id`.
2. Cleanup retention rule is strict: retain only `matched` + `active`.
3. Cleanup permanently deletes non-retained jobs from `job_postings`.
4. Cleanup deletes dependent job-owned rows for deleted jobs:
   - `job_decision_rules`
   - `job_decisions`
   - `job_tracking_events`
   - `reminders`
   - `digest_items`
   - `job_source_links`
5. Cleanup preserves retained matched active job rows and their valid dependent rows.
6. Cleanup creates or updates operational status/audit records as designed, including `source_runs.trigger_type = source_delete_cleanup`, success/failure state, counts, and error details where applicable.
7. Cleanup no-ops safely when source does not exist or source is not deleted.
8. Cleanup is idempotent when run multiple times for the same deleted source.
9. Cleanup re-checks retention at final delete, preserving a job that becomes matched active between selection and final deletion.
10. Visibility helper implements: visible if no associated deleted source OR job is matched active.

### 3.2 Backend API Tests

Recommended file:
- `tests/api/test_source_delete_job_cleanup_api.py`

Coverage:
1. `DELETE /sources/{source_id}` soft-deletes the source and returns existing fields plus cleanup queued/status fields, without breaking backward-compatible fields.
2. `DELETE /sources/{source_id}` schedules cleanup via background task after successful source deletion.
3. Deleted or nonexistent source delete still returns normal not-found behavior and does not queue duplicate cleanup.
4. Deleted source is absent from source list/detail/run/update APIs according to existing deletion semantics.
5. Jobs API `/jobs` excludes pending-cleanup non-retained jobs immediately after source deletion.
6. Jobs API `/jobs/{job_id}` returns 404 for non-retained jobs during pending-cleanup state and after physical deletion.
7. Jobs API `/jobs/{job_id}` returns 200 for retained matched active jobs.
8. Source filter behavior excludes deleted source IDs; stale `source_id=<deleted>` does not expose hidden jobs.
9. Tracking/reminder/digest APIs do not return non-retained deleted-source jobs during pending cleanup or after cleanup.

### 3.3 Integration / Regression Tests

Recommended files:
- `tests/integration/test_source_delete_job_cleanup_surfaces.py`
- Add focused regression coverage to existing source edit/delete integration tests only if needed.

Coverage:
1. End-to-end delete flow with mixed job data:
   - create source
   - create jobs with all retention matrix combinations
   - create source links/dependent rows
   - delete source
   - verify immediate UI/API suppression before cleanup completes
   - run cleanup service
   - verify physical database deletion and retained job visibility
2. Dashboard cards/counts/recent jobs exclude non-retained jobs immediately after source soft-delete.
3. Jobs list bucket/status/search/source filters do not reveal non-retained jobs.
4. Tracking page excludes deleted-source non-retained jobs.
5. Reminder and digest display/generation exclude invisible jobs and tolerate missing/deleted job references.
6. Multi-source behavior follows product assumption: any association to the deleted source makes non-retained jobs cleanup-eligible, even if another active source is also linked.
7. Source deletion failure path leaves jobs unchanged and shows no cleanup success messaging.
8. Cleanup failure path leaves source deleted, logs/status records failure, and keeps pending-cleanup jobs hidden from user surfaces.

### 3.4 Frontend / UI Tests

Recommended file:
- `tests/ui/test_source_delete_job_cleanup_ui.py`

Coverage:
1. Source delete confirmation page copy warns that most associated jobs are permanently removed and only matched active jobs are retained.
2. If impact counts are implemented, confirmation page shows linked, will-be-removed, and retained counts accurately.
3. If exact counts are not implemented, confirmation page uses rule-based copy and does not fabricate counts.
4. Post-delete flash/alert states that cleanup has started/queued and non-retained jobs are hidden from Dashboard and Jobs now.
5. Source list no longer displays deleted source after redirect.
6. Jobs source dropdown excludes deleted source.
7. Stale `/jobs?source_id=<deleted>` resets/ignores deleted source and does not show deleted-source non-retained jobs; if alert is implemented, assert visible reset copy.
8. Dashboard/jobs pages show retained matched active jobs and hide all non-retained jobs immediately.
9. Retained job detail may show deleted-source provenance with neutral “Deleted source” label and must not render edit/run/source-management actions for that deleted source.
10. Deleted job detail page returns normal not-found content/status.
11. Accessibility checks for destructive warning text, explicit “Delete source” button label, keyboard-reachable actions, and status/error alert roles where existing pattern supports them.

## 4. Edge Cases

### 4.1 Data Setup Matrix

Use source `deleted_source` plus at least one `active_source` for multi-source cases. For every row, validate both immediate visibility after source soft-delete and final database state after cleanup.

| Case | Association | `latest_bucket` | `current_state` | Extra state | Expected visibility after source delete before cleanup | Expected after cleanup |
|---|---|---:|---:|---|---|---|
| M1 | Primary deleted source | matched | active | none | Visible if filters match | Retained |
| M2 | Source link only | matched | active | none | Visible if filters match | Retained |
| M3 | Primary + link duplicate | matched | active | none | Visible once | Retained once/no duplicate processing |
| D1 | Primary deleted source | matched | inactive/closed | none | Hidden | Permanently deleted |
| D2 | Primary deleted source | matched | `None` or non-active | none | Hidden | Permanently deleted |
| D3 | Primary deleted source | review | active | none | Hidden | Permanently deleted |
| D4 | Primary deleted source | rejected | active | none | Hidden | Permanently deleted |
| D5 | Primary deleted source | `None` | active | unclassified | Hidden | Permanently deleted |
| D6 | Source link only | review | active | none | Hidden | Permanently deleted |
| D7 | Deleted source + active source links | review | active | multi-source | Hidden | Permanently deleted per product assumption |
| D8 | Primary deleted source + active source link | rejected | active | multi-source | Hidden | Permanently deleted per product assumption |
| D9 | Primary deleted source | matched | active | changes to inactive before cleanup | Hidden once non-retained | Permanently deleted if cleanup sees inactive |
| R1 | Primary deleted source | review | active | manual keep/tracked/saved | Hidden | Permanently deleted |
| R2 | Primary deleted source | rejected | active | reminder + digest item | Hidden | Job and dependent records deleted |
| Z1 | Deleted source | n/a | n/a | zero jobs | No jobs affected | Cleanup no-op success |

### 4.2 Async Cleanup Verification

1. Assert source delete response/redirect completes before physical job cleanup is required.
2. In tests, control background execution by mocking/stubbing the cleanup task or calling the cleanup service manually after asserting pending-cleanup visibility.
3. Verify the background task receives primitive source ID and uses a fresh DB session, not request-scoped session state.
4. Verify operational evidence exists after cleanup success/failure (`source_runs` and/or logs per implementation).
5. Verify retry safety by running cleanup repeatedly against already-cleaned source and against partially cleaned data.

### 4.3 Immediate Visibility Verification

Before running cleanup, after only `sources.deleted_at` is committed:
- `/dashboard` does not count or render non-retained jobs.
- `/jobs` does not return/render non-retained jobs.
- `/jobs/{non_retained_job_id}` returns not found.
- `/tracking`, `/reminders`, and `/digest/latest` do not return/render non-retained jobs.
- Source filter dropdown and source list do not include deleted source.
- Retained matched active jobs remain visible and accessible.

### 4.4 Negative and Failure Scenarios

1. Duplicate/stale source delete submit returns normal not-found/already-deleted behavior and does not queue duplicate user-visible cleanup.
2. Cleanup exception after source deletion records failure; source remains deleted; non-retained jobs remain hidden.
3. Missing classification or missing current state is treated as non-retained.
4. Jobs with dependent records are deleted without orphaned dependent rows.
5. Digest/reminder/tracking references to deleted jobs do not break page rendering or generation.
6. Deleted source cannot be run from stale UI/API.
7. Cleanup for non-deleted source does not delete jobs.
8. Logging/status output should include IDs/counts/status but not full job descriptions or raw payloads.

## 5. Test Types Covered

- Functional correctness: source deletion, retention/deletion rules, association discovery, physical cleanup.
- Validation and negative scenarios: nonexistent/already-deleted source, stale source filter, direct deleted job URL, cleanup failure.
- Edge cases: zero jobs, all retained jobs, all deleted jobs, mixed jobs, multi-source attribution, duplicate attribution, missing bucket/state.
- API/UI consistency: API responses and server-rendered pages must apply the same visibility rule.
- Integration/regression: dashboard, jobs list/detail, tracking, reminders, digest, source list/filter/run actions.
- Basic reliability: async behavior, idempotent retry, partial cleanup recovery, failure observability.
- Basic security/safety: no actionable deleted-source controls; logs/status do not expose full sensitive job payloads; destructive action remains explicit.

Recommended commands once tests are implemented:

```bash
pytest tests/unit/test_source_delete_cleanup.py tests/unit/test_job_visibility.py
pytest tests/api/test_source_delete_job_cleanup_api.py
pytest tests/integration/test_source_delete_job_cleanup_surfaces.py
pytest tests/ui/test_source_delete_job_cleanup_ui.py
pytest tests/unit tests/api tests/integration tests/ui
```

QA sign-off gate for this feature:
- All critical retention/deletion, immediate visibility, and idempotency tests pass.
- No user-facing surface leaks non-retained pending-cleanup jobs.
- Cleanup failure does not roll back source deletion and remains observable.
- Retained matched active jobs remain available without actionable deleted-source controls.
