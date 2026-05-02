# GitHub Issue

## 1. Feature Name

Transient untracked ingestion jobs

## 2. Problem Summary

The current ingestion flow persists all returned jobs, including jobs the user has not chosen to track. This causes durable local database growth from untracked jobs and related artifacts that should only represent temporary review results. Ingestion should persist only tracked jobs where `tracking_status IS NOT NULL`; newly ingested untracked jobs should remain runtime-only until the user assigns a non-null tracking status.

## 3. Linked Planning Documents
- Product Spec: `docs/product/transient_untracked_ingestion_jobs_product_spec.md`
- Technical Design: `docs/architecture/transient_untracked_ingestion_jobs_technical_design.md`
- UI/UX Spec: `docs/uiux/transient_untracked_ingestion_jobs_design_spec.md`
- QA Test Plan: `docs/qa/transient_untracked_ingestion_jobs_test_plan.md`

## 4. Scope Summary
- In scope
  - Prevent new ingestion results with `tracking_status IS NULL` from being persisted to job, source-link, classification, or ingestion metadata tables.
  - Keep untracked ingestion results visible only in current runtime/app state until refresh or restart.
  - Preserve existing update behavior for ingestion results matching tracked persisted jobs.
  - Persist a transient job and required related artifacts when the user assigns a non-null tracking status.
  - Remove existing persisted jobs where `tracking_status IS NULL` and safely clean up dependent records.
- Out of scope
  - Changing source adapter fetch behavior, classification rules, scoring, bucket logic, or tracking status values.
  - Using `manual_keep` as a persistence or cleanup rule.
  - Preserving transient untracked jobs across app restart.
  - Adding archive/restore, multi-user synchronization, or broader job review UI redesign.

## 5. Implementation Notes
- Frontend expectations
  - Show transient untracked ingestion results alongside persisted tracked jobs where needed for review.
  - Clearly label transient rows/cards with a `Temporary` badge and helper copy explaining restart/refresh behavior.
  - Provide tracking actions that persist transient jobs and then transition UI controls/links to normal persisted job behavior.
- Backend expectations
  - Gate durable persistence on `tracking_status IS NOT NULL`, not `manual_keep`.
  - Add runtime-only transient ingestion storage that refreshes per ingestion run and is not hydrated on startup.
  - Add a transient tracking path that atomically persists the job, source link, classification snapshot/rules, ingestion attribution, and tracking metadata.
  - Add idempotent cleanup/migration for existing untracked persisted jobs and dependent records.
- Dependencies or blockers
  - Existing ingestion orchestration, matching/deduplication, classification, tracking, route/schema, and database migration mechanisms.
  - Runtime state must retain enough source/classification data to persist a transient job later in the same app session.

## 6. QA Section
- Planned test coverage
  - Unit coverage for ingestion persistence gating, transient registry replacement/thread safety, classification preview neutrality, transient tracking, and cleanup idempotency.
  - API/integration coverage for ingestion runs, transient list/detail, tracking transient jobs, mixed tracked/untracked ingestion, restart behavior, and source-run counter semantics.
  - UI coverage for temporary result visibility, badges/callouts, tracking actions, detail link behavior, and accessibility states.
  - Migration/database coverage for deleting untracked persisted jobs and preventing orphaned dependent records.
- Acceptance criteria mapping
  - AC-01 through AC-02: verify new untracked ingestion results create no durable job-specific records.
  - AC-03 through AC-05: verify transient runtime visibility, refresh, and restart loss.
  - AC-06: verify existing tracked matches continue to update normally.
  - AC-07 through AC-09: verify `manual_keep` does not affect persistence or cleanup and tracked rows survive cleanup.
  - AC-10 through AC-12: verify tracking a transient job persists all required records and survives restart.
  - AC-13 through AC-15: verify untracked cleanup removes target rows/dependents and is repeatable.
- Key edge cases
  - Zero-job ingestion, only untracked jobs, mixed untracked and tracked matches, duplicate sources/matches, stale transient IDs, concurrent tracking, cleanup interruption, and restart before tracking.
- Test types expected
  - Unit, API/integration, end-to-end/UI, accessibility, migration/data-integrity, concurrency, and regression tests.

## 7. Risks / Open Questions

- Runtime-only transient storage can lose reviewable jobs on restart by design; UI copy must make this clear.
- Concurrent ingestion or tracking could create stale transient IDs or duplicate persistence attempts if not guarded.
- Cleanup must avoid orphaned dependent records and must never delete tracked jobs.
- Source-run counter semantics for transient-only discoveries should be documented and validated.
- No open product questions are identified in the current planning documents.

## 8. Definition of Done

- Newly ingested untracked jobs are not persisted and remain visible only as current runtime/app-state results.
- Existing tracked jobs continue to update through ingestion without regression.
- Tracking a transient job persists the job and required related artifacts atomically as a normal tracked job.
- Existing persisted untracked jobs and owned dependent records are safely cleaned up without deleting tracked jobs.
- UI clearly distinguishes temporary results and supports tracking them into persisted jobs.
- Planned QA coverage passes for persistence gating, transient runtime behavior, tracking conversion, cleanup, restart behavior, and regressions.
