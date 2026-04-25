# GitHub Issue

## 1. Feature Name
Source Delete Job Cleanup

## 2. Problem Summary
Deleted sources are removed from active source management, but jobs previously ingested from those sources can remain visible in job lists, dashboard counts, reminders, digests, and direct job detail views. This creates stale and misleading data after the user has intentionally removed a source.

The planned feature adds asynchronous cleanup after source deletion: permanently delete jobs associated with the deleted source except jobs that are both `matched` and `active`. Non-retained jobs must be hidden from normal user-facing surfaces immediately after source deletion, even while physical cleanup is still pending.

## 3. Linked Planning Documents
- Product Spec: `docs/product/source_delete_job_cleanup_product_spec.md`
- Technical Design: `docs/architecture/source_delete_job_cleanup_technical_design.md`
- UI/UX Spec: `docs/uiux/source_delete_job_cleanup_uiux_spec.md`
- QA Test Plan: `docs/qa/source_delete_job_cleanup_test_plan.md`

## 4. Scope Summary
- in scope
  - Trigger asynchronous job cleanup after a source is deleted.
  - Permanently delete source-associated jobs unless they are both `matched` and `active`.
  - Identify source-associated jobs by primary source attribution and source-link/provenance records.
  - Hide non-retained deleted-source jobs from dashboard, job list, job detail, tracking, reminders, digest, source filters, and counts immediately after source deletion.
  - Retain matched active jobs and treat the deleted source as historical/non-actionable provenance.
  - Ensure cleanup is idempotent, retry-safe, and observable through logs and/or operational status.
- out of scope
  - Undo or restore for deleted sources or deleted jobs.
  - Bulk source deletion.
  - User-configurable retention policies.
  - Archiving jobs instead of permanent deletion.
  - Reclassifying retained jobs as part of source deletion.
  - Major dashboard or job list redesign beyond required copy and visibility behavior.
  - New admin cleanup UI for the MVP unless later required.

## 5. Implementation Notes
- frontend expectations
  - Update source delete confirmation copy to explain permanent cleanup and matched-active retention.
  - Update post-delete success messaging to state cleanup has queued/started and non-retained jobs are hidden from Dashboard and Jobs immediately.
  - Keep existing server-rendered UI patterns; do not add client-side polling or filtering unless a later decision adds explicit cleanup status.
  - Ensure deleted sources are absent from source filters and actionable source controls.
  - If retained job provenance displays a deleted source, label it as historical/deleted and non-actionable.
- backend expectations
  - Preserve existing source soft-delete behavior using `deleted_at`/inactive source state.
  - Queue or start cleanup asynchronously after successful source deletion commit.
  - Add cleanup service logic to discover associated jobs, apply the strict `latest_bucket == matched` and `current_state == active` retention rule, delete non-retained jobs and dependent job-owned rows, and record operational status.
  - Centralize visibility rules so user-facing job surfaces exclude pending-cleanup non-retained jobs before physical deletion completes.
  - Ensure direct access to non-retained deleted-source jobs returns normal not-found behavior during the pending-cleanup window and after deletion.
- dependencies or blockers
  - Existing source delete flow and `sources.deleted_at` semantics.
  - Job attribution through `job_postings.primary_source_id` and `job_source_links.source_id`.
  - Classification and state fields: `latest_bucket` and `current_state`.
  - Background task mechanism, recommended as FastAPI `BackgroundTasks` for MVP.
  - Dependent job-owned tables such as decisions, decision rules, tracking events, reminders, digest items, and source links.
  - Open product question for multi-source jobs: current planning assumes any association to the deleted source makes a non-retained job cleanup-eligible.

## 6. QA Section
- planned test coverage
  - Unit tests for cleanup association discovery, retention/deletion matrix, dependent row cleanup, idempotency, retry safety, and visibility helper behavior.
  - API tests for source deletion response, cleanup scheduling, hidden pending-cleanup jobs, retained matched active jobs, deleted job not-found behavior, and deleted source filtering.
  - Integration tests for mixed job data across dashboard, jobs list/detail, tracking, reminders, digests, source list, and cleanup success/failure paths.
  - UI tests for delete confirmation copy, post-delete alert copy, source filter behavior, retained job deleted-source provenance, and normal not-found content for deleted jobs.
- acceptance criteria mapping
  - AC-01 through AC-02: verify immediate source removal and asynchronous cleanup scheduling.
  - AC-03 through AC-08: verify strict retention/deletion outcomes and final database state.
  - AC-09 through AC-12: verify immediate UI/API visibility suppression, retained job visibility, and non-actionable deleted-source provenance.
  - AC-13 through AC-15: verify idempotent retry behavior, cleanup failure handling, and zero-associated-job behavior.
- key edge cases
  - Source has no associated jobs.
  - Source has only matched active jobs.
  - Source has mixed matched active, matched inactive, review, rejected, and unclassified jobs.
  - Job is associated by primary source, source link only, or duplicate primary/link attribution.
  - Job is linked to both deleted and active sources.
  - Cleanup is retried after partial completion or failure.
  - User opens dashboard, jobs list, stale source filter, or bookmarked job detail immediately after source deletion.
  - Job selected for deletion has reminders, digest items, tracking events, decisions, or rule evidence.
- test types expected
  - Unit, API, integration, UI, regression, negative/failure, async behavior, idempotency, and data cleanup tests.

## 7. Risks / Open Questions
- Multi-source cleanup policy needs confirmation: should any association to a deleted source make a non-retained job cleanup-eligible, or only when all associated sources are deleted?
- Pre-delete impact counts may require extra query work; if not implemented, UI copy must explain the rule without fabricating counts.
- Cleanup status visibility is planned through logs and/or existing operational records; a dedicated admin retry/status UI is out of scope for MVP.
- Physical deletion must remove dependent rows safely to avoid orphaned data and broken reminders/digests.
- Immediate visibility filtering must be applied consistently across all job surfaces to avoid stale data leaks during the async cleanup window.

## 8. Definition of Done
- Planning documents are complete and linked from this issue.
- Source delete flow queues or starts asynchronous cleanup after source deletion is committed.
- Cleanup permanently deletes all associated non-retained jobs and dependent job-owned records.
- Only jobs that are both `matched` and `active` remain from the deleted source.
- Dashboard, job list, job detail, tracking, reminders, digest, source filters, and counts hide non-retained deleted-source jobs immediately after deletion.
- Retained matched active jobs remain visible when filters match and deleted source provenance is historical/non-actionable.
- Cleanup is idempotent, retry-safe, and observable through logs and/or operational status.
- QA test coverage for the planned acceptance criteria and edge cases is implemented and passing before implementation release.
