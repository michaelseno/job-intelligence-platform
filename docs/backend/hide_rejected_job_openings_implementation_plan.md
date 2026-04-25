# Implementation Plan

## 1. Feature Overview

Hide jobs whose current display classification is explicitly `rejected` from the main Jobs and Dashboard actionable surfaces while preserving storage records and direct detail access.

## 2. Technical Scope

- Add reusable main-display visibility helpers in `app/domain/job_visibility.py` that compose existing source-delete visibility with non-rejected status filtering.
- Apply the main-display helper to `/jobs` query construction and dashboard actionable jobs data flow.
- Preserve `/jobs/{job_id}` and job mutation route behavior on the existing source-delete visibility helper.
- Add backend tests for predicate behavior, route filtering, dashboard counts/previews, direct detail access, and reclassification transitions.

## 3. Files Expected to Change

- `app/domain/job_visibility.py`
- `app/web/routes.py`
- `tests/unit/test_job_visibility.py`
- `tests/integration/test_hide_rejected_job_openings_surfaces.py`
- Existing regression tests requiring actionable fixture data updates.
- Backend implementation report under `docs/backend/`.

## 4. Dependencies / Constraints

- Use `JobPosting.latest_bucket` as the current display classification source of truth.
- Preserve existing source-delete visibility semantics.
- Do not change schema, ingestion, classification, direct detail authorization, or rejected-record persistence.
- Do not push or create a PR.

## 5. Assumptions

- `NULL` and unknown non-`rejected` bucket values remain visible on the main display.
- `/jobs?bucket=rejected` should return an empty result set through predicate composition, not validation failure.
- Dashboard `rejected_count` remains in the JSON contract with value `0` after filtering.

## 6. Validation Plan

- Run focused backend tests for visibility helpers and new Jobs/Dashboard integration coverage.
- Run backend unit/API/integration regression suites.
- Run the full test suite to identify any remaining non-backend/UI test issues.
