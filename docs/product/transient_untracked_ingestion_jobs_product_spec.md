# Product Specification

## 1. Feature Overview

Change ingestion persistence behavior so jobs returned by ingestion are persisted to the local database only when they are tracked.

Untracked ingestion results must remain available only as transient runtime/app-state data for the current session or current ingestion result set. They must not be written to the local database and must not survive an app restart. Existing untracked database jobs must be removed from persistent storage.

When a transient untracked job is later tracked by the user, the system must persist the job and its related ingestion artifacts at that moment.

## 2. Problem Statement

The current ingestion flow persists all returned jobs, including jobs the user has not chosen to track. This causes the local database to accumulate untracked jobs, related source links, classification data, and ingestion metadata that may never become part of the user's active job-search workflow.

This creates unnecessary persistent data growth, makes database state less representative of intentional user tracking decisions, and allows untracked ingestion results to survive app restarts even though they should only represent the latest discovered opportunities.

## 3. User Persona / Target User

- Primary user: the single-user job seeker operating the app locally/self-hosted.
- Usage context: the user runs ingestion, reviews returned jobs, and chooses which jobs to track for ongoing application workflow management.

## 4. User Stories

- As a job seeker, I want newly ingested untracked jobs to be visible for review without being permanently stored, so that my database contains only intentional tracked jobs.
- As a job seeker, I want an ingested job that I decide to track to be saved with its context, so that I can manage it after the current ingestion cycle.
- As a job seeker, I want already tracked jobs to continue updating during ingestion, so that tracked opportunities stay current.
- As a job seeker, I want old untracked persisted jobs removed, so that the app state is consistent with the new persistence rule.

## 5. Goals / Success Criteria

- Ingestion no longer persists jobs whose `tracking_status` is `NULL`.
- `manual_keep` is not used to determine whether a job is persisted.
- Jobs with any non-null `tracking_status` continue to be persisted and updated.
- Existing database jobs with `tracking_status IS NULL` are removed, including related source links and classification data as applicable.
- Transient untracked ingestion results remain visible only in current runtime/app state until ingestion runs again or the app restarts.
- When a transient job is tracked, the system persists the job, source link, classification result, and ingestion metadata to the database at that moment.

## 6. Feature Scope

### In Scope

- Change ingestion behavior so untracked returned jobs are not inserted into the local database.
- Preserve current update behavior for returned jobs that match already tracked database jobs.
- Maintain transient visibility of untracked ingestion results in current runtime/app state.
- Replace or refresh transient untracked ingestion results when ingestion triggers again.
- Persist a transient job and its required related records when the user assigns a non-null tracking status.
- Clean up existing persisted jobs where `tracking_status IS NULL`.
- Clean up dependent records for removed untracked jobs where those records are owned by or only valid with the removed job.

### Out of Scope

- Changing available tracking status values.
- Changing classification rules, scoring, or bucket assignment logic.
- Changing source adapters or external ingestion fetch behavior.
- Using `manual_keep` as a persistence rule.
- Adding multi-user behavior or cloud synchronization.
- Adding an archive/restore flow for removed untracked jobs.
- Preserving transient untracked jobs across app restart.
- Redesigning the job review UI beyond changes required to support transient results.

### Future Considerations

- User-configurable retention policies for untracked jobs.
- Optional local cache with explicit expiration for untracked ingestion results.
- Analytics comparing transient reviewed jobs versus tracked jobs.

## 7. Functional Requirements

1. The system must define a tracked job as any job with `tracking_status IS NOT NULL`.
2. The system must define an untracked job as any job with `tracking_status IS NULL`.
3. During ingestion, the system must not create a persisted job record for a newly returned job when that job has no non-null `tracking_status`.
4. During ingestion, the system must not create persisted source-link, classification-result, or ingestion-metadata records for newly returned untracked jobs.
5. During ingestion, newly returned untracked jobs must remain available in current runtime/app state for user review until ingestion triggers again or the app restarts.
6. When ingestion triggers again, the system must refresh the transient untracked result set according to the latest ingestion output rather than relying on previously persisted untracked jobs.
7. If ingestion returns a job that matches an already tracked database job, the system must update the existing tracked job and source link according to current update behavior.
8. The system must not use `manual_keep` to decide whether a job is persisted, retained, or cleaned up.
9. A job with `manual_keep = true` and `tracking_status IS NULL` must be treated as untracked for persistence and cleanup.
10. When the user assigns a non-null `tracking_status` to a transient job, the system must persist the job record at that moment.
11. When the user tracks a transient job, the system must also persist the job's source link, latest classification result, and ingestion metadata required to represent the job as a normal tracked database job.
12. Once persisted through tracking, the job must behave like any other tracked job in job lists, detail views, source attribution, classifications, and future ingestion updates.
13. The system must remove existing database jobs where `tracking_status IS NULL` as part of this feature's data cleanup.
14. Cleanup must remove or safely delete related source links and classification data for removed untracked jobs as applicable to prevent orphaned or invalid records.
15. Cleanup must not delete jobs where `tracking_status IS NOT NULL`, regardless of `manual_keep` value.
16. Cleanup must be safe to run more than once without deleting tracked jobs or failing because previously targeted untracked records were already removed.

## 8. Acceptance Criteria

- AC-01: Given ingestion returns a new job with `tracking_status IS NULL`, when ingestion completes, then no job row for that new untracked job exists in the local database.
- AC-02: Given ingestion returns a new job with `tracking_status IS NULL`, when ingestion completes, then no persisted source-link, classification-result, or ingestion-metadata rows are created solely for that untracked job.
- AC-03: Given ingestion returns new untracked jobs, when the user views current ingestion results before another ingestion run or app restart, then those untracked jobs are visible from current runtime/app state.
- AC-04: Given transient untracked jobs are visible in current runtime/app state, when ingestion triggers again, then the transient untracked result set is refreshed from the latest ingestion output.
- AC-05: Given transient untracked jobs are visible in current runtime/app state, when the app restarts, then those untracked jobs are no longer visible unless returned by a subsequent ingestion run.
- AC-06: Given ingestion returns a job matching an existing database job where `tracking_status IS NOT NULL`, when ingestion completes, then the existing tracked job and source link are updated using the same behavior as before this feature.
- AC-07: Given ingestion returns a new job with `manual_keep = true` and `tracking_status IS NULL`, when ingestion completes, then the job is not persisted to the local database.
- AC-08: Given an existing database job has `manual_keep = true` and `tracking_status IS NULL`, when data cleanup runs, then that job is removed because `manual_keep` does not determine persistence.
- AC-09: Given an existing database job has `tracking_status IS NOT NULL`, when data cleanup runs, then that job is not removed due to this cleanup regardless of its `manual_keep` value.
- AC-10: Given a transient untracked job is visible to the user, when the user assigns any non-null `tracking_status`, then the job is persisted to the local database.
- AC-11: Given a transient job is tracked, when persistence completes, then the related source link, latest classification result, and ingestion metadata are persisted with the job.
- AC-12: Given a transient job has been tracked and persisted, when the user restarts the app, then the job remains available as a tracked job.
- AC-13: Given existing database jobs with `tracking_status IS NULL`, when cleanup completes, then those job records no longer exist in the local database.
- AC-14: Given cleanup removes an untracked database job, when cleanup completes, then related source links and classification records that are only applicable to that removed job are also removed or otherwise cannot remain as orphaned data.
- AC-15: Given cleanup is run more than once, when the later run executes, then it completes without deleting tracked jobs and without requiring already removed untracked jobs to exist.

## 9. Edge Cases

- Ingestion returns zero jobs.
- Ingestion returns only new untracked jobs.
- Ingestion returns a mix of new untracked jobs and jobs matching existing tracked records.
- Ingestion returns the same job from multiple sources before the user tracks it.
- A transient job is tracked after another ingestion run has refreshed the transient result set.
- A transient job is tracked while source-link or classification data is available only in runtime/app state.
- Existing persisted job has `tracking_status IS NULL` and `manual_keep = true`.
- Existing persisted job has `tracking_status IS NOT NULL` and `manual_keep = false` or `NULL`.
- Existing untracked job has related source links, classification results, ingestion metadata, or other dependent records.
- Cleanup is interrupted after deleting some untracked jobs but before all related records are removed.
- Cleanup runs when there are no untracked database jobs.
- App restarts after ingestion but before the user tracks a transient job.

## 10. Constraints

- Technical constraints:
  - Local database persistence eligibility is determined by `tracking_status`, not `manual_keep`.
  - `tracking_status IS NULL` means untracked.
  - `tracking_status IS NOT NULL` means tracked.
  - Transient untracked results must be held outside durable local database storage.
  - Tracking a transient job must have enough runtime/app-state data to create normal persisted job, source-link, classification, and ingestion metadata records.
- UX constraints:
  - Untracked ingestion results must remain reviewable after ingestion completes within the current runtime/app state.
  - Users must not see untracked jobs from previous app runs unless those jobs were tracked or returned again by ingestion.
- Business rules:
  - `manual_keep` must not preserve or persist an otherwise untracked job.
  - Existing tracked-job update behavior must be preserved.

## 11. Dependencies

- Existing ingestion flow and source adapter outputs.
- Existing job matching/deduplication logic used to identify returned jobs that correspond to tracked database jobs.
- Existing job persistence schema for jobs, source links, classifications, and ingestion metadata.
- Existing tracking-status update flow.
- Existing job list/review surfaces that display current ingestion results.
- Database cleanup or migration mechanism capable of deleting existing untracked jobs and related dependent records safely.

## 12. Assumptions

- No assumptions requiring confirmation. The persistence rule is fully determined by `tracking_status` nullability.

## 13. Open Questions

- None.
