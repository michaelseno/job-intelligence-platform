# Implementation Report

## 1. Summary of Changes

Implemented backend query-layer filtering for the Hide Rejected Job Openings feature. The main Jobs endpoint and Dashboard actionable data now exclude jobs with `latest_bucket == "rejected"` while keeping matched, review, `NULL`, and unknown non-rejected buckets visible.

## 2. Files Modified

- `app/domain/job_visibility.py`
- `app/web/routes.py`
- `tests/unit/test_job_visibility.py`
- `tests/integration/test_hide_rejected_job_openings_surfaces.py`
- `tests/integration/test_html_views.py`
- `tests/ui/test_source_edit_delete_ui_qa.py`
- `docs/backend/hide_rejected_job_openings_implementation_plan.md`
- `docs/backend/hide_rejected_job_openings_implementation_report.md`

## 3. Key Logic Implemented

- Added `actionable_job_status_predicate()` to exclude only explicit rejected buckets and include SQL `NULL` buckets correctly.
- Added `main_display_job_predicate()` and `apply_main_display_jobs()` to compose source-delete visibility with rejected filtering.
- Updated `/jobs` base query to use `apply_main_display_jobs()`, so bucket, tracking, search, source filtering, and sorting operate within the non-rejected result set.
- Updated Dashboard actionable jobs loading to use `apply_main_display_jobs()`, causing matched/review counts and previews to exclude rejected jobs and `rejected_count` to remain `0`.
- Left direct job detail and mutation routes on `apply_visible_jobs()` so rejected records remain directly accessible when source-visible.
- Added tests for predicate behavior, `/jobs?bucket=rejected`, rejected-only search, source-filter compatibility, dashboard counts/previews, direct rejected detail access, and persisted reclassification transitions.

## 4. Assumptions Made

- `JobPosting.latest_bucket` is the canonical current display bucket for Jobs and Dashboard surfaces.
- Unknown non-rejected bucket values and `NULL` bucket values remain visible to preserve existing behavior.
- Template removal of the `Rejected` bucket option remains a frontend handoff item; backend filtering prevents exposure of rejected jobs even if stale UI/query parameters request them.

## 5. Validation Performed

- `./.venv/bin/python -m pytest tests/unit/test_job_visibility.py tests/integration/test_hide_rejected_job_openings_surfaces.py` — **passed**, 8 tests.
- `./.venv/bin/python -m pytest tests/unit/test_job_visibility.py tests/integration/test_hide_rejected_job_openings_surfaces.py tests/integration/test_api_flow.py tests/integration/test_html_views.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/api/test_source_delete_job_cleanup_api.py` — **passed**, 20 tests.
- `./.venv/bin/python -m pytest tests/unit tests/api tests/integration` — **passed**, 34 tests.
- `./.venv/bin/python -m pytest` — **failed**, 44 passed / 5 failed. Remaining failures are in `tests/ui/test_saas_dashboard_ui_revamp.py` and appear tied to UI test harness expectations for HTML responses without an HTML `Accept` header and fixed seed data/detail assumptions, not to rejected-job backend filtering.

## 6. Known Limitations / Follow-Ups

- Frontend should remove the `Rejected` option from the Jobs bucket selector and update copy to `All actionable` per UI/UX spec.
- Frontend/QA should review `tests/ui/test_saas_dashboard_ui_revamp.py` because it requests JSON-default routes without HTML `Accept` headers while asserting HTML shells.
- Reminder/tracking-specific surfaces intentionally continue to use existing source-delete visibility and may still surface rejected jobs outside the main display.

## 7. Commit Status

Included in the backend feature commit for hide rejected job openings.
