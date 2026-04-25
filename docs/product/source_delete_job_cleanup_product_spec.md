# Product Specification

## 1. Feature Overview
Add asynchronous job cleanup behavior when a job source is deleted.

When a source is deleted from active configuration, the system must permanently remove jobs associated with that deleted source unless a job is both:
- classified as `matched`
- currently `active`

Retained jobs are the only jobs from the deleted source that may continue to exist after cleanup. All other jobs from that source must be permanently deleted from the database and must no longer appear in the job list, dashboard, or related job discovery surfaces.

## 2. Problem Statement
Deleted sources are currently removed from normal source management, but jobs previously ingested from those sources can remain visible in the Jobs UI and dashboard. This creates stale, misleading data because the user has intentionally removed the source that produced those jobs.

This matters because source deletion should represent a data lifecycle decision, not only a configuration change. Without cleanup, dashboards and job lists continue to show opportunities from sources the user no longer wants, reducing trust in counts, filters, and prioritized job review workflows.

## 3. User Persona / Target User
- Primary user: the single-user job seeker operating the app locally/self-hosted.
- Usage context: the user manages job sources, reviews matched jobs, and uses the dashboard/job list as the main surfaces for deciding which opportunities deserve attention.

## 4. User Stories
- As a job seeker, I want jobs from a deleted source to be cleaned up automatically, so that my job list does not stay cluttered with stale source data.
- As a job seeker, I want matched active jobs to be retained after deleting a source, so that high-value current opportunities are not accidentally lost.
- As a job seeker, I want non-matched or inactive jobs from a deleted source to be permanently removed, so that deleted sources do not continue influencing my dashboard.
- As a job seeker, I want source deletion to complete quickly from the UI while cleanup happens asynchronously, so that I am not blocked by a potentially large data cleanup task.
- As a job seeker, I want clear feedback that cleanup is queued or in progress, so that I understand any short eventual-consistency window.

## 5. Goals / Success Criteria
- Deleting a source triggers asynchronous cleanup for jobs associated with that source.
- Retention rule Option B is enforced exactly: permanently delete source-associated jobs except jobs that are both `matched` and `active`.
- Deleted jobs do not appear in the dashboard, job list, job detail access, job counts, source-filtered job views, reminders, or digests after cleanup is complete.
- Normal user-facing job discovery surfaces do not show stale deleted-source jobs during the asynchronous cleanup window, except for retained matched active jobs.
- Source deletion remains responsive and does not wait synchronously for all related job rows to be deleted.
- Cleanup behavior is safe to retry and does not delete retained jobs if the cleanup worker runs more than once.

## 6. Feature Scope
### In Scope
- Trigger asynchronous cleanup after a source is deleted.
- Identify all jobs associated with the deleted source through primary source attribution and/or source link attribution.
- Permanently delete jobs from that source that are not both `matched` and `active`.
- Retain jobs from that source only when both retention conditions are true.
- Remove deleted jobs and pending-deletion jobs from dashboard and job list visibility.
- Ensure related job-owned data does not remain as broken or user-visible orphaned data after permanent deletion.
- Provide user-visible confirmation that source deletion has occurred and job cleanup has been queued or started.
- Define eventual-consistency expectations for asynchronous cleanup.

### Out of Scope
- Undo/restore for deleted sources or deleted jobs.
- Bulk source deletion.
- User-configurable retention policies.
- Archiving deleted jobs instead of permanently deleting them.
- Reclassifying retained jobs as part of source deletion.
- Changing ingestion behavior except as needed to prevent deleted sources from being run or reintroducing deleted jobs.
- Reworking dashboard or job list UI beyond states/copy needed for cleanup visibility and stale-job suppression.

## 7. Functional Requirements
1. When source deletion is confirmed, the source must be removed from active source configuration immediately according to existing source delete behavior.
2. When source deletion is confirmed, the system must enqueue or start an asynchronous cleanup task for jobs associated with the deleted source.
3. A job is considered associated with the deleted source if the source is the job's primary source or if any source-link/provenance record connects the job to that source.
4. The cleanup task must evaluate each associated job using the retention rule.
5. A job must be retained only if its latest classification bucket is `matched` and its current job state is `active`.
6. A job that does not satisfy both retention conditions must be permanently deleted from the database.
7. Permanent deletion must include or safely remove dependent job data that would otherwise become invalid, including classification records, rule evidence, tracking events, reminders, digest references, and source-link records as applicable.
8. Retained jobs must remain accessible in normal job surfaces if they otherwise match those surfaces' filters.
9. Retained jobs must not allow the deleted source to be used for future ingestion, source management, or source filter selection.
10. Dashboard and job list queries must not show non-retained jobs from deleted sources while cleanup is pending or after cleanup completes.
11. Job counts and dashboard summaries must exclude non-retained jobs from deleted sources while cleanup is pending or after cleanup completes.
12. If a user attempts to open a job detail page for a job deleted by cleanup, the system must return the normal not-found behavior.
13. The asynchronous cleanup task must be idempotent and safe to retry.
14. Cleanup failures must not roll back the source deletion, but they must be detectable through logs, task state, or an operational error surface available to maintainers/developers.

## 8. Acceptance Criteria
- AC-01: Given a source with associated jobs, when the user confirms source deletion, the source no longer appears in active source lists, source filters, or future ingestion actions immediately after the delete response.
- AC-02: Given a deleted source, cleanup is queued or started without requiring the delete request to synchronously delete every associated job before responding.
- AC-03: Given an associated job with `latest_bucket = matched` and `current_state = active`, when cleanup runs, the job is not deleted.
- AC-04: Given an associated job with `latest_bucket = matched` and `current_state != active`, when cleanup runs, the job is permanently deleted.
- AC-05: Given an associated job with `latest_bucket != matched` and `current_state = active`, when cleanup runs, the job is permanently deleted.
- AC-06: Given an associated job with no current classification bucket, when cleanup runs, the job is permanently deleted.
- AC-07: Given an associated job with `latest_bucket = review` or `latest_bucket = rejected`, when cleanup runs, the job is permanently deleted regardless of tracking status or manual keep state.
- AC-08: After cleanup completes, the only remaining jobs associated with the deleted source are jobs that are both matched and active.
- AC-09: After source deletion is confirmed, non-retained jobs from that source do not appear in the dashboard, job list, or dashboard summary counts, even if physical deletion is still pending.
- AC-10: After cleanup deletes a job, direct navigation to that job detail URL returns not found and does not render stale job content.
- AC-11: Retained matched active jobs remain visible in the dashboard/job list when they match the current view filters.
- AC-12: Retained jobs may display historical source provenance as deleted/retired if provenance is shown, but the deleted source must not expose edit, run, or source-selection actions.
- AC-13: Running cleanup more than once for the same deleted source does not delete retained matched active jobs and does not produce duplicate failures for already-deleted jobs.
- AC-14: If cleanup fails after source deletion, the user-facing source deletion remains complete and stale non-retained jobs remain hidden from normal dashboard/job list surfaces until cleanup succeeds or is retried.
- AC-15: Deleting a source with zero associated jobs completes successfully and does not create a visible cleanup error.

## 9. Edge Cases
- Source has no associated jobs.
- Source has only matched active jobs.
- Source has a mix of matched active, matched inactive, review, rejected, and unclassified jobs.
- A job is linked to multiple sources, one of which is deleted.
- A job's primary source is the deleted source but it also has links to other non-deleted sources.
- A job's primary source is not the deleted source but it has a source link to the deleted source.
- Source deletion is submitted twice from stale browser state.
- Cleanup task is retried after partial completion.
- Cleanup task fails after deleting some but not all eligible jobs.
- User opens the dashboard or job list immediately after source deletion but before physical cleanup completes.
- User opens a previously bookmarked job detail URL after that job has been deleted.
- A digest, reminder, or tracking event references a job selected for deletion.
- New ingestion attempt is triggered from stale UI after source deletion.

## 10. Constraints
- Technical constraints:
  - Existing source deletion is modeled separately from source deactivation; this feature must preserve that distinction.
  - Existing domain terms include job classification buckets (`matched`, `review`, `rejected`), job `current_state`, source `deleted_at`, and source/job attribution.
  - Cleanup must be asynchronous and must not make the source delete request depend on deleting all associated jobs inline.
  - Permanent deletion must avoid orphaned dependent records and broken user-facing pages.
- UX constraints:
  - Source delete confirmation and success messaging must make clear that associated jobs will be cleaned up asynchronously.
  - After confirmation, users should see the source as deleted immediately and should not need to refresh repeatedly to remove stale non-retained jobs from dashboard/job list views.
  - If a cleanup-in-progress state is exposed, it must be informational and not require user action.
- Business rules:
  - Retention rule Option B is mandatory: retain only jobs that are both matched and active.
  - Tracking status, reminders, manual keep, and digest inclusion do not override the Option B retention rule unless separately changed by future product decision.
  - Deleted sources must not be eligible for future ingestion.

## 11. Dependencies
- Existing source edit/delete behavior and deleted-source state.
- Job persistence model and source attribution records.
- Classification bucket data for determining `matched` status.
- Job current state data for determining `active` status.
- Dashboard queries, job list queries, job detail route, source filters, reminders, and digest references.
- Background task/job execution mechanism or equivalent asynchronous processing capability.
- QA data fixtures covering mixed job classifications and states.

## 12. Assumptions
- A1: `matched` means the job's current/latest classification bucket is `matched`.
- A2: `active` means the job's current job state is `active`.
- A3: If a job is missing either required retention signal, it is treated as not retained and is deleted.
- A4: Permanent deletion means the job record is removed from normal persistence rather than only hidden with a soft-delete flag.
- A5: Asynchronous cleanup is expected to complete shortly after source deletion under normal local/self-hosted usage; product surfaces must still hide non-retained jobs immediately to avoid stale UI during the cleanup window.
- A6: Retained jobs may continue to exist even though their source is deleted because they represent high-value current opportunities.
- A7: This is a new data lifecycle feature, not a regression bugfix.

## 13. Open Questions
- OQ-01: For jobs linked to multiple sources, should a non-retained job be deleted if any deleted source is associated with it, or should deletion occur only when all associated sources are deleted? Current spec assumes any association to the deleted source makes the job subject to Option B cleanup.
- OQ-02: Should the user-facing delete confirmation show counts by retention outcome, such as “X jobs will be deleted; Y matched active jobs will be retained,” before deletion is confirmed?
- OQ-03: Should cleanup task status be exposed in an admin/developer page, or are logs sufficient for this single-user MVP?
