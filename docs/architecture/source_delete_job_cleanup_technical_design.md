# Source Delete Job Cleanup Technical Design

## Feature Overview

When a job source is deleted, the application must asynchronously clean up jobs associated with that source. Jobs associated with the deleted source are permanently deleted unless they are both:

- `latest_bucket == "matched"`
- `current_state == "active"`

The source deletion request must remain responsive. During the async cleanup window, dashboard and job list surfaces must immediately suppress non-retained jobs from the deleted source by using the source `deleted_at` marker as the visibility boundary.

Implementation requires **backend changes** and a small **frontend/template copy update**. No major frontend state-management changes are required in the current server-rendered FastAPI/Jinja application.

## Product Requirements Summary

- Source deletion soft-deletes the source from active configuration immediately.
- Source deletion queues or starts asynchronous job cleanup.
- Associated jobs are identified by either `job_postings.primary_source_id` or any `job_source_links.source_id` pointing to the deleted source.
- Retention rule is strict: retain only matched active jobs.
- Non-retained jobs must not appear in Jobs, Dashboard, counts, source-filter views, reminders, or digests while cleanup is pending or after cleanup completes.
- Cleanup must permanently delete non-retained jobs and dependent job-owned records.
- Cleanup must be idempotent, retry-safe, and observable via logs and/or task/run state.

## Scope

### In Scope

- Extend existing source delete flow in `SourceService.delete_source` and source delete endpoints.
- Add a backend cleanup service that deletes eligible jobs and dependent rows.
- Start cleanup asynchronously after source `deleted_at` is committed.
- Add reusable query/helper behavior to exclude pending-cleanup jobs from user-facing job surfaces.
- Update API response/message to communicate that cleanup has been queued/started.
- Add tests for retention/deletion, idempotency, immediate visibility suppression, and dependent cleanup.

### Out of Scope

- Restore/undo for deleted sources or jobs.
- User-configurable retention policies.
- Archival soft-delete for jobs.
- Bulk source deletion.
- New admin UI for cleanup jobs. Logs plus existing source run/ops surfaces are sufficient for MVP.

## Architecture Overview

Current repository findings:

- Backend stack: FastAPI, SQLAlchemy 2.x, Alembic, SQLite/PostgreSQL-compatible schema.
- Source deletion currently soft-deletes `sources` by setting `deleted_at` and `is_active = False` in `app/domain/sources.py`.
- Source delete endpoints:
  - `DELETE /sources/{source_id}` in `app/web/routes.py`
  - `POST /sources/{source_id}/delete` HTML form route in `app/web/routes.py`
- Job model fields:
  - `JobPosting.primary_source_id`
  - `JobPosting.latest_bucket`
  - `JobPosting.current_state`
  - `JobSourceLink.job_posting_id`, `source_id`, `is_primary`
- Existing user-facing surfaces currently select `JobPosting` directly and therefore need visibility filtering:
  - Dashboard: `GET /dashboard`
  - Jobs list/API: `GET /jobs`
  - Job detail/API: `GET /jobs/{job_id}`
  - Tracking page: `GET /tracking`
  - Reminders page/API: `GET /reminders`
  - Digest latest page/API: `GET /digest/latest`
  - Digest/reminder generation in `NotificationService`
- Background infrastructure: APScheduler is initialized in `app/main.py` but no jobs are registered. FastAPI `BackgroundTasks` is the simplest request-triggered async mechanism for this feature.

Recommended design:

1. Delete request soft-deletes the source and commits immediately.
2. Endpoint schedules a cleanup background task after successful commit.
3. Cleanup task opens its own DB session and runs `SourceDeleteCleanupService.cleanup_source(source_id)`.
4. Dashboard/list/query helpers immediately hide non-retained jobs associated with any deleted source by joining source attribution to `sources.deleted_at`.
5. Cleanup permanently deletes dependent job-owned data before deleting `job_postings`.
6. Cleanup records operational status using `source_runs` rows with `trigger_type = "source_delete_cleanup"` and logs structured summary data.

## System Components

### Existing Components Affected

- `app/domain/sources.py`
  - Keep source soft-delete behavior.
  - Optionally return a result object that indicates whether deletion occurred and which source id was deleted.
  - Do not perform physical job deletion inline.
- `app/web/routes.py`
  - Inject `BackgroundTasks` into source delete routes.
  - Schedule cleanup only after `delete_source` returns a deleted source.
  - Apply visibility helper to dashboard/jobs/detail/tracking/reminder/digest surfaces.
- `app/domain/notifications.py`
  - Ensure digest/reminder generation excludes non-retained jobs from deleted sources while cleanup is pending.
- `app/persistence/models.py`
  - No required model changes for MVP if `source_runs` is reused for cleanup status.

### New Backend Components

- `app/domain/source_cleanup.py`
  - Owns association discovery, retention evaluation, dependent deletion order, idempotency, and operational logging.
- `app/domain/job_visibility.py` or equivalent helper module
  - Provides reusable SQLAlchemy predicates/functions for “visible jobs” in normal user-facing surfaces.
- Optional route helper in `app/web/routes.py`
  - `enqueue_source_delete_cleanup(background_tasks, source_id)` creates a background task that opens a fresh session via `SessionLocal`.

## Data Models and Storage Design

### Existing Tables Used

- `sources`
  - `deleted_at` is the source deletion boundary and immediate visibility marker.
- `job_postings`
  - Retention fields: `latest_bucket`, `current_state`.
  - Primary source attribution: `primary_source_id`.
- `job_source_links`
  - Source/provenance association.
- Dependent job-owned tables to delete for non-retained jobs:
  - `job_decision_rules`
  - `job_decisions`
  - `job_tracking_events`
  - `reminders`
  - `digest_items`
  - `job_source_links`
  - `job_postings`

### Migration Needs

No schema migration is required for MVP if cleanup status is represented with existing `source_runs`:

- `source_runs.trigger_type = "source_delete_cleanup"`
- `source_runs.status`: `running`, `success`, `failed`, optionally `partial_success`
- `source_runs.jobs_fetched_count`: number of associated jobs evaluated
- `source_runs.jobs_created_count`: use as `retained_count` is not semantically ideal; avoid overloading if possible
- `source_runs.jobs_updated_count`: use as `deleted_count` is not semantically ideal; avoid overloading if possible
- `source_runs.log_summary` and `error_details_json`: store human-readable and structured cleanup summary

Preferred minimal usage: set `jobs_fetched_count` to associated/evaluated count, `error_count`, `log_summary`, and `error_details_json`. Put `deleted_count` and `retained_count` in `error_details_json` or a summary JSON payload even for success.

Future consideration: add a dedicated `source_cleanup_jobs` table if product later needs admin retry controls, progress UI, or multiple cleanup job types.

## API Contracts

### DELETE `/sources/{source_id}`

Current response:

```json
{
  "deleted": true,
  "source_id": 123,
  "deleted_at": "2026-04-25T12:00:00Z"
}
```

Recommended response extension:

```json
{
  "deleted": true,
  "source_id": 123,
  "deleted_at": "2026-04-25T12:00:00Z",
  "cleanup_queued": true,
  "cleanup_status": "queued"
}
```

Backward compatibility: existing clients that only read `deleted`, `source_id`, and `deleted_at` continue to work.

Error behavior remains:

- `404` if source does not exist or is already deleted under current `get_source` behavior.

### POST `/sources/{source_id}/delete`

HTML redirect remains to `/sources`, but success copy should change to:

> Source deleted. It has been removed from active configuration and associated jobs are being cleaned up in the background.

### Existing Job/Dashboard APIs

No new request parameters are required. Responses should simply exclude pending-cleanup non-retained jobs.

For direct `GET /jobs/{job_id}`, recommended behavior is:

- Return `404` if the job has already been physically deleted.
- Also return `404` during the cleanup window if the job is associated with a deleted source and does not satisfy matched+active retention. This prevents stale bookmarked detail views from exposing a job that is logically pending deletion.
- Retained matched active jobs remain accessible.

## Frontend / Client Impact

Implementation requires **both backend and frontend/template work**, but frontend scope is small.

- Source delete confirmation page may keep existing impact counts for runs/linked/tracked jobs.
- Delete success toast/banner copy must mention background cleanup.
- Jobs/dashboard/reminders/digest pages require no new UI widgets if backend filtering is centralized.
- Source filters must continue to list only `Source.deleted_at IS NULL` sources. Current jobs page already does this.
- If retained jobs display deleted source provenance in job detail, source actions should not be offered for deleted sources. Current source actions are primarily on source pages; ensure templates do not render run/edit links for deleted sources if such links are added around provenance.

## Backend Logic / Service Behavior

### Association Discovery

A job is associated with a deleted source if either condition is true:

- `JobPosting.primary_source_id == source_id`
- Exists `JobSourceLink` with `job_source_links.job_posting_id == job_postings.id` and `job_source_links.source_id == source_id`

Use `DISTINCT JobPosting.id` to avoid duplicates when both attribution paths match.

### Retention Rule

Retain only:

```text
job.latest_bucket == "matched" AND job.current_state == "active"
```

Delete all other associated jobs, including:

- `matched` but inactive/non-active current state
- `review`/`rejected` active jobs
- unclassified jobs where `latest_bucket IS NULL`
- manually kept or tracked jobs that do not satisfy matched+active

### Immediate Visibility Strategy

Define a reusable “normal visible jobs” rule:

```text
Visible if NOT EXISTS an associated deleted source
OR (latest_bucket = 'matched' AND current_state = 'active')
```

Where “associated deleted source” means either primary source is deleted or any source link points to a deleted source.

Apply this helper to:

- `dashboard()` job set before counts/cards/reminders summary are calculated.
- `build_jobs_query()` / `list_jobs()` before bucket/tracking/search/source filters are applied.
- `get_job()` detail route before rendering/serializing.
- `tracking_page()`.
- `NotificationService.generate_digest()` by joining/looking up jobs for candidate decisions and excluding invisible jobs.
- `NotificationService.generate_reminders()`.
- `latest_digest()` and `list_reminders()` display paths should skip invisible or already-deleted jobs.

Important: retained matched active jobs from a deleted source remain visible even though their source is deleted.

### Async Cleanup Strategy

Use FastAPI `BackgroundTasks` for request-triggered cleanup:

1. Endpoint calls `SourceService.delete_source(source_id)`.
2. If a source is returned, endpoint adds a background task with only primitive arguments, e.g. `source_id`.
3. Background task function imports/uses `SessionLocal` to open a fresh session. Do not reuse the request-scoped session after the response.
4. Task calls `SourceDeleteCleanupService(session).cleanup_source(source_id)`.
5. Task commits success/failure status in `source_runs` and logs exceptions.

Rationale: this is the simplest implementable asynchronous behavior in the existing FastAPI app. APScheduler exists but is not currently configured with persistent jobs; introducing a durable queue would be out of scope.

Retry options:

- Automatic retry is not required for MVP, but cleanup must be safe if invoked again.
- Maintainers can retry by calling the service from a shell/test task or by adding a simple operational endpoint later.
- Future: APScheduler periodic sweep for deleted sources with failed/missing cleanup runs.

### Cleanup Algorithm

For `cleanup_source(source_id)`:

1. Load source with `include_deleted=True`.
2. If source does not exist, log no-op and return success/no-op.
3. If `source.deleted_at is None`, do not cleanup; log and return no-op/failure depending caller use. Cleanup should only run for deleted sources.
4. Create a `SourceRun` row:
   - `source_id = source_id`
   - `trigger_type = "source_delete_cleanup"`
   - `status = "running"`
5. Query distinct associated job ids.
6. Partition ids into retained and delete candidates using current DB state at cleanup time.
7. Delete candidates in batches. MVP can use one transaction for local-scale data, but service should be structured so batching can be added easily.
8. For each delete batch, delete dependent rows in safe order:
   1. Select decision ids for batch jobs.
   2. Delete `JobDecisionRule` where `job_decision_id IN decision_ids`.
   3. Delete `JobDecision` where `job_posting_id IN job_ids`.
   4. Delete `JobTrackingEvent` where `job_posting_id IN job_ids`.
   5. Delete `Reminder` where `job_posting_id IN job_ids`.
   6. Delete `DigestItem` where `job_posting_id IN job_ids`.
   7. Delete `JobSourceLink` where `job_posting_id IN job_ids`.
   8. Delete `JobPosting` where `id IN job_ids` and still not retained.
9. Re-check the retention predicate in the final `DELETE FROM job_postings` condition to avoid deleting a job that became matched+active between partition and delete.
10. Mark run `success`, set `finished_at`, summary counts, and commit.
11. On exception, rollback current transaction if needed, mark run `failed` in a separate transaction/session state where possible, and log `source_id`, `run_id`, exception class/message.

### Idempotency and Retry Safety

- Running cleanup multiple times for the same deleted source must be safe because:
  - Already-deleted jobs are absent from associated job query.
  - Retained jobs are re-evaluated each run and skipped while matched+active.
  - Dependent deletes should use `WHERE ... IN (...)` and tolerate zero affected rows.
- The final job delete statement must include the inverse retention condition:

```text
NOT (latest_bucket = 'matched' AND current_state = 'active')
```

- No cleanup operation should undelete or mutate retained jobs.
- Source deletion itself must not be rolled back if cleanup fails.

### Multi-Source Jobs

Per current product assumption, any association to the deleted source makes the job subject to cleanup. Therefore a non-retained job linked to both a deleted source and an active source is deleted. Retained matched active jobs remain even if one or more associated sources are deleted.

## File / Module Structure

Recommended implementation changes:

```text
app/
  domain/
    source_cleanup.py        # new SourceDeleteCleanupService
    job_visibility.py        # new reusable visible-job predicates/helpers
    sources.py               # preserve soft-delete, optionally expose delete result
    notifications.py         # apply visibility in generation queries
  web/
    routes.py                # enqueue background task and use visibility helpers
  schemas.py                 # extend SourceDeleteResponse with cleanup fields
  main.py                    # no required scheduler changes
tests/
  unit/
    test_source_delete_cleanup.py
    test_job_visibility.py
  api/
    test_source_delete_job_cleanup_api.py
  integration/
    test_source_delete_job_cleanup_surfaces.py
```

## Security and Access Control

- The current app is local/single-user and has no explicit auth model. This feature should follow existing route access behavior.
- Do not expose deleted source run/edit actions from retained job provenance.
- Cleanup logs must not include full raw payloads or full job descriptions; include ids/counts/status only.
- Deletion is irreversible, so route behavior must continue to require the existing explicit source delete confirmation for HTML users.

## Reliability / Operational Considerations

- Cleanup failures must not affect source deletion success.
- Use structured logging with at least:
  - `source_id`
  - `cleanup_run_id` / `source_run.id`
  - `associated_count`
  - `retained_count`
  - `deleted_count`
  - `status`
  - exception message on failure
- `source_runs` with `trigger_type = "source_delete_cleanup"` provides a basic operational audit trail visible through existing ops run list/detail routes.
- For SQLite, keep transactions reasonably small. If batch size is implemented, start with 500 job ids per batch.
- If background execution fails due to process shutdown, immediate visibility suppression still protects user-facing lists because it depends on committed `sources.deleted_at`. A later retry can physically delete rows.
- Avoid using request-scoped SQLAlchemy sessions in background tasks.

## Dependencies and Constraints

- Existing source soft-delete schema (`sources.deleted_at`) must remain the lifecycle marker.
- Existing FastAPI/Jinja server-rendered app should not require a new frontend framework.
- Existing `source_runs` table can represent cleanup execution status without migration.
- Existing foreign keys do not define cascading deletes in models/migrations, so application-level dependent deletion order is required.
- Retention is based on denormalized `JobPosting.latest_bucket`, not by recomputing or joining latest `JobDecision`, because product assumptions define latest bucket and the model already maintains it.

## Assumptions

- `latest_bucket == "matched"` is the authoritative matched signal.
- `current_state == "active"` is the authoritative active signal.
- Missing bucket or state mismatch means non-retained.
- Permanent delete means removal from `job_postings`, not a job-level soft delete.
- FastAPI background tasks are acceptable async behavior for the local/self-hosted MVP.
- Logs plus `source_runs` are sufficient operational visibility for MVP.
- Jobs associated with multiple sources are deleted if any deleted source association exists and the job is not matched+active.

## Risks / Open Questions

- **Durability of background tasks:** FastAPI `BackgroundTasks` are in-process and not durable across process crashes. Mitigation: visibility suppression is immediate; cleanup is idempotent and can be retried. Future: scheduled sweeper or persistent queue.
- **SourceRun semantic overload:** Reusing `source_runs` for cleanup avoids migration but is not a perfect domain fit. Future: dedicated cleanup task table.
- **Multi-source deletion semantics:** Current design follows product assumption that any deleted source association subjects the job to cleanup. This may surprise users if an active source also found the same job.
- **Query consistency:** Every user-facing job surface must use the visibility helper. Missing one surface could leak pending-cleanup jobs.
- **Race with classification/tracking changes:** Cleanup evaluates current DB state and should re-check retention at final delete. A job that becomes matched+active before final delete should be retained.

## Implementation Notes for Downstream Agents

- Route implementation should be assigned to a **backend agent** with light template updates; frontend-only implementation is insufficient.
- Add `BackgroundTasks` to both API and HTML source delete handlers.
- Keep `SourceService.delete_source` focused on source soft-delete and commit; schedule cleanup in route layer after success.
- Implement a single source of truth for visibility. Do not duplicate ad hoc filters in each route.
- Tests should create sources, runs, jobs, links, decisions/rules, tracking events, reminders, and digest items directly using SQLAlchemy fixtures.
- Required test scenarios:
  - matched+active associated job is retained.
  - matched+inactive job is deleted.
  - review/rejected/unclassified active jobs are deleted.
  - manual_keep/tracking/reminder/digest do not prevent deletion.
  - source with zero jobs succeeds.
  - repeated cleanup run is safe and leaves retained jobs intact.
  - dashboard/job list counts hide non-retained jobs immediately after source soft-delete before cleanup service runs.
  - job detail returns not found for logically pending-deletion non-retained jobs if adopting recommended detail suppression.
  - dependent rows are removed for deleted jobs; retained jobs keep their rows.
  - deleted source does not appear in source list/filter/run endpoints.
- Prefer explicit delete statements over relying on ORM cascades because relationships/cascades are not fully modeled.
- Ensure `DELETE /sources/{id}` response schema update remains backward compatible by adding optional/default fields.
