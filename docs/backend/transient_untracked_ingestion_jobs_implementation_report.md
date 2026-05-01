# Implementation Report

## 1. Summary of Changes
Implemented backend/data-layer support for transient untracked ingestion jobs. Ingestion now persists only existing tracked matches, stores newly discovered untracked jobs in runtime memory, exposes transient API endpoints, and persists transient jobs plus related artifacts when tracked.

## 2. Files Modified
- `app/domain/ingestion.py` — split tracked-match persistence from transient capture and added ingestion logging.
- `app/domain/classification.py` — extracted persistence-neutral classification snapshots and reused them for persisted decisions.
- `app/domain/transient_ingestion.py` — added thread-safe runtime transient registry and dataclasses.
- `app/domain/tracking.py` — added transient tracking persistence flow for job/source link/decision/rules/event.
- `app/schemas.py` — added transient list response schemas.
- `app/web/routes.py` — added transient list/detail/tracking routes.
- `alembic/versions/20260501_0005_cleanup_untracked_jobs.py` — added idempotent cleanup migration for untracked jobs and dependents.
- `tests/conftest.py` — clears transient registry between tests.
- `tests/unit/test_transient_ingestion_jobs.py` — added transient ingestion and tracking coverage.
- `tests/integration/test_api_flow.py` — updated ingestion flow expectations to track transient jobs before persisted-job operations.
- `docs/backend/transient_untracked_ingestion_jobs_implementation_plan.md` — implementation plan.

## 3. API Contract Implementation
Added:
- `GET /ingestion/transient-jobs` with optional integer `source_id` filter.
- `GET /ingestion/transient-jobs/{transient_job_id}` returning runtime detail or `404`.
- `POST /ingestion/transient-jobs/{transient_job_id}/tracking-status` returning `201` for new persistence, `200` for duplicate tracked match, `400` invalid status, `404` missing transient ID, and `409` legacy untracked conflict.

Existing persisted job endpoints remain unchanged.

## 4. Data / Persistence Implementation
No schema changes. Added cleanup migration for `tracking_status IS NULL` jobs and dependent rows. New ingestion of unmatched jobs creates only `SourceRun`; no `JobPosting`, `JobSourceLink`, `JobDecision`, or `JobDecisionRule` rows are created for transient candidates.

## 5. Key Logic Implemented
- Tracked = `tracking_status IS NOT NULL`; `manual_keep` is not used for persistence gating.
- Existing tracked matches are updated and classified through the persisted path.
- Newly discovered untracked candidates are classified with a persistence-neutral preview and stored in the transient registry.
- Registry replaces per-source results on successful ingestion, deduping by source/external ID, normalized URL, or canonical key.
- Tracking a transient job re-runs DB matching, persists or updates the tracked job, writes source link and classification records, emits tracking event, commits, then consumes the transient entry.

## 6. Security / Authorization Implemented
Follows existing local single-user routing. Transient IDs are opaque runtime IDs. Tracking validates status server-side and ignores any client-provided job data beyond status/note.

## 7. Error Handling Implemented
- Invalid transient tracking status raises `400`.
- Missing/expired transient IDs raise `404`.
- Legacy persisted untracked DB matches during transient tracking raise `409`.
- Tracking transaction rolls back on exceptions and consumes the transient entry only after commit.

## 8. Observability / Logging
Ingestion logs fetched, persisted created/updated/unchanged, and transient capture counts.

## 9. Assumptions Made
- Failed ingestion leaves the previous successful transient set unchanged because registry replacement happens only after successful candidate processing.
- `SourceRun.jobs_created_count` remains ingestion-time persisted effects only; later transient tracking does not mutate run counters.

## 10. Validation Performed
- `python -m pytest tests/unit/test_transient_ingestion_jobs.py tests/integration/test_api_flow.py` — failed: `python` command unavailable.
- `python3 -m pytest tests/unit/test_transient_ingestion_jobs.py tests/integration/test_api_flow.py` — failed: `pytest` is not installed in the environment.
- `python3 -m compileall app tests` — passed; application and test Python files compiled successfully.
- `python3 -m compileall alembic/versions/20260501_0005_cleanup_untracked_jobs.py` — passed.
- Backend import validation attempted with `python3`; blocked because runtime dependency `sqlalchemy` is not installed in the environment.

## 11. Known Limitations / Follow-Ups
- Full pytest execution could not be completed due to missing local test dependencies.
- UI templates were not changed in this backend-focused pass; transient API support is present for UI integration.

## 12. Commit Status
Pending commit.
