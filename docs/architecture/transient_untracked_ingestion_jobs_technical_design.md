# Technical Design

## 1. Feature Overview

Change ingestion so newly discovered untracked jobs are not persisted. A job is tracked only when `tracking_status IS NOT NULL`; `manual_keep` must not influence persistence or cleanup eligibility. Untracked ingestion results remain in runtime memory for review until the next ingestion refresh or process restart. When the user tracks a transient job, the backend persists the job, source link, latest classification result, and ingestion metadata so it becomes a normal tracked database job.

Product spec: `docs/product/transient_untracked_ingestion_jobs_product_spec.md`.

## 2. Product Requirements Summary

- Do not insert DB rows for newly ingested jobs with `tracking_status IS NULL`.
- Do not insert source-link, classification-result, or ingestion-metadata rows solely for newly ingested untracked jobs.
- Preserve updates for ingestion results matching existing tracked jobs.
- Keep untracked ingestion results reviewable only in current runtime/app state.
- Refresh transient results on each ingestion run and lose them on restart.
- Persist a transient job and related artifacts when any non-null tracking status is assigned.
- Remove existing DB jobs where `tracking_status IS NULL`, including dependent records as applicable.
- Cleanup must be idempotent and must not delete tracked jobs regardless of `manual_keep`.

## 3. Requirement-to-Architecture Mapping

| Requirement / AC | Architectural responsibility |
| --- | --- |
| FR1-FR4, AC-01, AC-02, AC-07 | `IngestionOrchestrator` separates matched tracked persistence from new untracked transient capture. |
| FR5-FR6, AC-03-AC-05 | New in-memory transient ingestion registry stores latest untracked result set and replaces it per ingestion run. |
| FR7, AC-06 | Existing DB upsert/classification path remains only for jobs matched to persisted tracked jobs. |
| FR8-FR9, AC-07-AC-09 | Persistence and cleanup predicates use only `tracking_status IS NULL/IS NOT NULL`; never `manual_keep`. |
| FR10-FR12, AC-10-AC-12 | Tracking service/API gains transient-job tracking path that persists all required artifacts atomically. |
| FR13-FR16, AC-13-AC-15 | Alembic data migration/domain cleanup deletes existing untracked jobs and dependents safely and repeatably. |

## 4. Technical Scope

### Current Technical Scope

- Refactor ingestion persistence gating in `app/domain/ingestion.py`.
- Add runtime-only transient result storage and schemas.
- Expose current transient ingestion results to API/HTML surfaces needed for review.
- Add transient tracking endpoint/service path.
- Add idempotent cleanup migration for existing untracked jobs and dependent records.
- Add/adjust tests for ingestion, cleanup, transient state, and tracking from transient state.

### Out of Scope

- Changing adapter fetch behavior, classification rules, scoring, buckets, or tracking status values.
- Persisting transient results in DB, files, browser storage, Redis, or cache with restart survival.
- Multi-user/session isolation beyond current single-user local app model.
- Archive/restore for deleted untracked rows.
- Redesigning job review UI beyond transient result visibility and tracking actions.

### Future Technical Considerations

- Optional expiring local cache for untracked results.
- Retention policies or analytics for reviewed-but-untracked jobs.
- More robust multi-session ownership if the app becomes multi-user.

## 5. Architecture Overview

### Current-state flow and affected files/modules

Current ingestion in `app/domain/ingestion.py`:

1. `IngestionOrchestrator.run_source()` creates and flushes a persisted `SourceRun`.
2. Adapter returns `AdapterFetchResult.jobs` (`app/adapters/base/contracts.py`).
3. For every candidate, `_upsert_job()` inserts or updates `JobPosting`, then inserts/updates `JobSourceLink`.
4. `ClassificationService.classify_job()` writes `JobDecision` and `JobDecisionRule` rows and updates `JobPosting.latest_*`.
5. `SourceRun.jobs_created_count`, `jobs_updated_count`, and `jobs_unchanged_count` count all candidates, including untracked jobs.

Current tracking in `app/domain/tracking.py` assumes a persisted `JobPosting` exists and updates `/jobs/{job_id}/keep` or `/jobs/{job_id}/tracking-status` in `app/web/routes.py`.

Current DB models in `app/persistence/models.py` include:

- `JobPosting.tracking_status` nullable.
- `JobPosting.manual_keep` boolean.
- Dependents: `JobSourceLink`, `JobDecision`, `JobDecisionRule`, `JobTrackingEvent`, `Reminder`, `DigestItem`.
- `SourceRun` stores ingestion run metadata.

### Proposed high-level flow

1. Ingestion fetches candidates as today.
2. For each candidate, compute matching keys (`normalized_url`, `canonical_key`, and source/external ID link match).
3. If candidate matches an existing persisted job where `tracking_status IS NOT NULL`, update that job/source link/classification using current behavior.
4. If candidate does not match a tracked persisted job, do not create DB job/source-link/classification rows. Build a transient result containing the normalized candidate, source/run attribution, matching keys, raw payload, and a non-persisted classification snapshot.
5. Replace the runtime transient result set for the source/run with the latest untracked results.
6. API/UI reads transient results from memory.
7. When user assigns a non-null tracking status to a transient result, persist job, source link, classification decision/rules, tracking event, and update source-run counters in one DB transaction.

## 6. System Components

### `IngestionOrchestrator` (`app/domain/ingestion.py`)

Responsibilities:

- Maintain existing adapter validation, source-run creation, warnings, source health, and commit behavior.
- Replace candidate loop with a tracked-match branch and transient branch.
- Use `tracking_status.is_not(None)` as the only persistence-eligible existing-job predicate for matched updates.
- Return `SourceRun` as today; optionally attach non-persisted summary counts through response/schema if needed.

Implementation guidance:

- Do not pass transient candidates into current `classify_job()` because it writes DB rows.
- Introduce a classification preview method (see Classification component) to produce the same bucket/score/rule outcome without persistence.
- Preserve existing `_upsert_job()` behavior for tracked jobs, but guard lookup results so untracked persisted rows are not updated during the migration window.

### Transient ingestion registry (new module, recommended `app/domain/transient_ingestion.py`)

Responsibilities:

- Runtime-only storage for latest untracked ingestion results.
- Thread-safe access because source batch execution uses `ThreadPoolExecutor`.
- Replace result set for a source on every completed ingestion for that source.
- Remove or mark consumed a transient result when it is persisted through tracking.

Recommended storage shape:

- Process-global registry object using `threading.RLock`.
- Primary key: opaque `transient_job_id` (`uuid4` string) generated per current runtime result.
- Indexes: by `source_id`, `source_run_id`, and `transient_job_id`.
- No DB persistence and no startup hydration.

### `ClassificationService` (`app/domain/classification.py`)

Responsibilities:

- Preserve `classify_job(job, preferences)` for persisted jobs.
- Add a persistence-neutral classification method that accepts job-like candidate data and returns a decision snapshot with rules.
- Reuse the same rule logic to avoid drift between transient preview and persisted classification.

Recommended internal contract:

- Extract rule evaluation into a pure method returning bucket, score, sponsorship state, summary, and rule list.
- `classify_job()` persists the pure result for a `JobPosting`.
- Transient ingestion stores the pure result snapshot.

### Tracking service (`app/domain/tracking.py`)

Responsibilities:

- Preserve existing tracking for persisted jobs.
- Add a `track_transient_job(transient_job_id, tracking_status, note_text)` path.
- Validate `tracking_status in VALID_TRACKING_STATUSES`.
- Persist all related records atomically and emit a tracking event.

### Web/API routes (`app/web/routes.py`) and schemas (`app/schemas.py`)

Responsibilities:

- Keep existing persisted job routes unchanged for persisted jobs.
- Add read route(s) for transient ingestion results.
- Add route to track a transient result.
- For HTML, provide a review surface or augment current source/detail/jobs surfaces so users can see and track transient results.

### Database cleanup/migration

Responsibilities:

- Delete existing `JobPosting` rows where `tracking_status IS NULL`.
- Delete dependent rows for those jobs first, including classification rules through decisions.
- Be safe to run repeatedly.
- Never use `manual_keep` in delete predicates.

## 7. Data Models

### Existing persisted entity: `JobPosting`

#### Purpose

Durable record for tracked jobs only after this feature.

#### Primary Key

`id` integer DB primary key.

#### Fields

Existing fields remain unchanged. Persistence eligibility is determined by `tracking_status`:

- `tracking_status: str | None` — `NULL` means untracked and should not be present for new ingestion-created rows; non-null means tracked.
- `manual_keep: bool` — not a persistence or cleanup rule.

#### Ownership Model

Single-user local database.

#### Lifecycle

- Created during transient tracking, or updated during ingestion when a tracked persisted match exists.
- Existing untracked rows are deleted by migration/cleanup.
- Future ingestion must not create untracked rows.

### Existing persisted entity: `JobSourceLink`

#### Purpose

Durable source attribution for persisted tracked jobs.

#### Primary Key

`id` integer DB primary key.

#### Fields

Existing fields remain unchanged.

#### Ownership Model

Scoped to a persisted `job_posting_id` and `source_id`.

#### Lifecycle

- Created/updated during tracked-job ingestion updates.
- Created when a transient job is tracked.
- Deleted for untracked cleanup targets.

### Existing persisted entity: `JobDecision` / `JobDecisionRule`

#### Purpose

Durable classification result for persisted tracked jobs.

#### Lifecycle

- Created by `ClassificationService.classify_job()` for persisted jobs.
- Created from transient classification snapshot when a transient job is tracked, or recomputed with the same preferences if the snapshot is unavailable in memory.
- Deleted for untracked cleanup targets.

### Existing persisted entity: `SourceRun`

#### Purpose

Durable ingestion run metadata and source health/audit record.

#### Lifecycle

- Still created for every ingestion run, even if all fetched jobs are transient.
- `jobs_fetched_count` remains total adapter candidates.
- `jobs_created_count` should count persisted job creations only. New untracked transient discoveries should not inflate persisted-created count.
- If a transient job is tracked later, update the originating run metadata only if downstream UI relies on `jobs_created_count`; otherwise record linkage via `JobSourceLink.source_run_id` and do not mutate historical ingestion counters. Preferred: leave run counters as ingestion-time persisted effects and document transient count separately if added.

### New runtime entity: `TransientIngestionJob`

#### Purpose

Reviewable, non-durable representation of an untracked ingestion result.

#### Primary Key

`transient_job_id: str` generated UUID. This ID is valid only for the current process and current registry contents.

#### Fields

- `transient_job_id: str`
- `source_id: int`
- `source_run_id: int`
- `external_job_id: str | None`
- `canonical_key: str`
- `normalized_job_url: str | None`
- Candidate fields matching `NormalizedJobCandidate` (`title`, `company_name`, `job_url`, `location_text`, `employment_type`, `remote_type`, `description_text`, `description_html`, `sponsorship_text`, `posted_at`, `raw_payload`)
- `classification: TransientClassificationSnapshot`
- `first_seen_at: datetime` and `last_seen_at: datetime` within runtime state
- `created_at: datetime`

#### Ownership Model

Single process, single-user runtime state. Not user-scoped unless future auth is added.

#### Lifecycle

- Created during ingestion for new/untracked candidates.
- Replaced when ingestion runs again for the same source. For batch ingestion, each source refreshes its own set.
- Deleted/consumed when tracked.
- Lost on app restart.

### New runtime entity: `TransientClassificationSnapshot`

#### Purpose

Non-durable classification preview for a transient job.

#### Fields

- `decision_version: str`
- `bucket: str`
- `final_score: int`
- `sponsorship_state: str`
- `decision_reason_summary: str`
- `rules: list[RuleResult-like objects]`

## 8. API Contracts

Existing persisted-job endpoints remain unchanged:

- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /jobs/{job_id}/keep`
- `POST /jobs/{job_id}/tracking-status`

### Endpoint: GET /ingestion/transient-jobs

#### Purpose

Return current runtime untracked ingestion results for review.

#### Authentication / Authorization

No auth today; follows existing local single-user route behavior. If auth is added later, require the same owner/session as ingestion.

#### Request Parameters

- Query `source_id: int | None` — optional filter.

#### Request Body

None.

#### Response Body

```json
{
  "items": [
    {
      "transient_job_id": "uuid",
      "source_id": 1,
      "source_run_id": 10,
      "title": "Software Engineer",
      "company_name": "Example Co",
      "job_url": "https://example.com/job/1",
      "location_text": "Remote",
      "employment_type": "Full-time",
      "remote_type": "remote",
      "posted_at": null,
      "latest_bucket": "matched",
      "latest_score": 42,
      "tracking_status": null,
      "created_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

#### Success Status Codes

- `200 OK`

#### Error Status Codes

- `422 Unprocessable Entity` for invalid `source_id` query value.

#### Validation Rules

- `source_id`, if provided, must parse as integer.

#### Side Effects

None.

#### Idempotency / Duplicate Handling

Read-only. Returned set reflects latest in-memory registry state.

### Endpoint: GET /ingestion/transient-jobs/{transient_job_id}

#### Purpose

Return full current runtime details for one transient job, including description and classification rules.

#### Authentication / Authorization

Same as existing local job detail routes.

#### Request Parameters

- Path `transient_job_id: str`.

#### Request Body

None.

#### Response Body

Same shape as `JobDetailResponse` where possible, but with `id` replaced by `transient_job_id`, `tracking_status: null`, source-link attribution from runtime state, and classification snapshot without persisted decision IDs.

#### Success Status Codes

- `200 OK`

#### Error Status Codes

- `404 Not Found` if the transient ID is absent, consumed, refreshed away, or lost after restart.

#### Validation Rules

- Treat malformed/unknown IDs as not found; do not query DB by this ID.

#### Side Effects

None.

#### Idempotency / Duplicate Handling

Read-only.

### Endpoint: POST /ingestion/transient-jobs/{transient_job_id}/tracking-status

#### Purpose

Assign a non-null tracking status to a transient job and persist it with related artifacts.

#### Authentication / Authorization

Same as persisted tracking routes. Verify the transient ID exists in runtime state.

#### Request Parameters

- Path `transient_job_id: str`.
- For HTML form submissions: optional `next` URL.

#### Request Body

```json
{
  "tracking_status": "saved",
  "note_text": "optional note"
}
```

#### Response Body

On JSON success, return the persisted `JobResponse` plus `persisted_job_id` if not already obvious.

#### Success Status Codes

- `201 Created` when a new persisted job is created from transient state.
- `200 OK` if duplicate handling finds an already-persisted tracked job and updates tracking/status/link safely.

#### Error Status Codes

- `400 Bad Request` for invalid tracking status.
- `404 Not Found` if transient result is no longer available.
- `409 Conflict` if the transient job matches a persisted untracked row during migration window or another concurrent request consumes it; response should instruct refresh.

#### Validation Rules

- `tracking_status` is required and must be one of `VALID_TRACKING_STATUSES`.
- Null/empty tracking status is invalid for this endpoint.
- Do not accept or use `manual_keep` as a persistence signal.

#### Side Effects

- Inserts/updates `JobPosting` with non-null `tracking_status`.
- Inserts `JobSourceLink` using transient source/run/raw payload metadata.
- Inserts current `JobDecision` and `JobDecisionRule` rows from classification snapshot or recomputation.
- Inserts `JobTrackingEvent`.
- Removes/consumes transient registry entry.
- Commits transaction.

#### Idempotency / Duplicate Handling

- Use DB matching by source/external ID, normalized URL, and canonical key before insert.
- If a tracked persisted job already exists, update it rather than creating a duplicate, then consume transient entry.
- If a repeated request uses an already-consumed transient ID, return `404` or `409`; do not create duplicate rows.

## 9. Frontend Impact

### Components Affected

- Source run trigger flow in `app/web/routes.py` and source templates, because run completion should lead to visible transient review results.
- Jobs review UI templates (`app/web/templates/jobs/list.html`, `app/web/templates/jobs/detail.html`) or a new transient-results template.
- Shared macros for tracking/keep forms if reused for transient IDs.

### API Integration

- Fetch/list transient results from `GET /ingestion/transient-jobs` for API clients.
- Submit tracking from transient cards/details to `POST /ingestion/transient-jobs/{transient_job_id}/tracking-status`.
- Existing `/jobs` APIs should continue to return persisted jobs only unless explicitly enhanced with a separate transient section. Do not mix integer DB IDs and transient UUIDs in the same `id` field without a discriminator.

### UI States

- Loading: current app is mostly server-rendered; display normal page load/submit behavior.
- Empty: “No current transient ingestion results. Run ingestion to discover new jobs.”
- Error: transient job no longer available due to refresh/restart; prompt user to rerun ingestion.
- Consumed: after successful tracking, redirect to `/jobs/{persisted_job_id}` or back to review list with success message.

## 10. Backend Logic

### Responsibilities

- Gate DB writes for job/source-link/classification rows by tracked status or existing tracked match.
- Maintain source-run audit rows for ingestion executions.
- Store untracked candidate artifacts in runtime memory only.
- Persist transient artifacts atomically when tracking occurs.
- Clean existing untracked DB rows.

### Validation Flow

Ingestion candidate:

1. Normalize URL and compute canonical key.
2. Look for source-link match by `(source_id, external_job_id)`.
3. Resolve linked job if present.
4. Look for direct `JobPosting` match by normalized URL or canonical key.
5. Treat as persistable update only if matched job exists and `tracking_status IS NOT NULL`.
6. Otherwise build transient record.

Tracking transient job:

1. Validate status is non-null and in `VALID_TRACKING_STATUSES`.
2. Load transient record by ID under registry lock or consume reservation.
3. In DB transaction, re-run matching against persisted tracked jobs to avoid duplicates.
4. Insert/update `JobPosting` with `tracking_status` set.
5. Insert/update `JobSourceLink`.
6. Persist classification result/rules.
7. Insert `JobTrackingEvent`.
8. Commit and consume registry entry.

### Business Rules

- `tracking_status IS NULL` means untracked.
- `tracking_status IS NOT NULL` means tracked.
- `manual_keep` is ignored for persistence, retention, and cleanup.
- New untracked ingestion candidates must not create durable job, source-link, decision/rule, or job-specific ingestion metadata rows.
- Existing tracked jobs matched by ingestion must continue to update.

### Persistence Flow

#### Ingestion for tracked match

- Use existing `_upsert_job()` path with a tracked-only lookup predicate.
- Classify persisted job using existing `ClassificationService.classify_job()`.
- Count created/updated/unchanged as persisted effects.

#### Ingestion for new/untracked result

- Do not call `session.add(JobPosting(...))`.
- Do not create `JobSourceLink`.
- Do not call DB-persisting `classify_job()`.
- Store `TransientIngestionJob` in registry.
- Include total fetched count in `SourceRun.jobs_fetched_count`.

#### Tracking transient result

- Create `JobPosting` with all fields from transient candidate, `first_seen_at/last_seen_at/last_ingested_at` from transient run timestamps/current time, and `tracking_status` from request.
- Create `JobSourceLink` with `source_run_id` from transient record.
- Persist decision/rules and update `latest_bucket`, `latest_score`, `latest_decision_id`.
- Insert `JobTrackingEvent(event_type="status_change" or "save" for `saved`; choose one convention and test it).`

### Error Handling

- Ingestion failure behavior remains: mark `SourceRun` failed and update source health.
- Transient registry failures should not partially commit DB job records because no DB job writes occur for transient candidates.
- Tracking transaction rollback must leave transient entry available unless it was already consumed after commit.
- Concurrent tracking attempts for the same transient ID must not create duplicates.

## 11. File Structure

Expected implementation touch points:

- `app/domain/ingestion.py` — split tracked persistence from transient capture.
- `app/domain/transient_ingestion.py` — new runtime registry and dataclasses.
- `app/domain/classification.py` — pure classification result extraction.
- `app/domain/tracking.py` — transient tracking/persistence method.
- `app/schemas.py` — transient list/detail response schemas and optional track response schema.
- `app/web/routes.py` — transient read/track routes and HTML handling.
- `app/web/templates/...` — transient review UI or augment existing pages.
- `app/persistence/models.py` — no schema changes expected.
- `alembic/versions/<next_revision>_cleanup_untracked_jobs.py` — idempotent cleanup migration.
- `tests/unit/...`, `tests/api/...`, `tests/integration/...` — coverage described below.

## 12. Security

- Authentication/authorization follows existing single-user local app behavior.
- Do not expose raw payload details in list responses unless already exposed elsewhere; full detail can include source attribution needed for review.
- Validate transient IDs as opaque strings; never interpolate into SQL.
- Validate tracking statuses against `VALID_TRACKING_STATUSES`.
- Do not accept client-provided candidate fields when tracking transient jobs; persist only server-held runtime data.
- Avoid open redirect issues for `next` by continuing existing redirect handling patterns; consider limiting `next` to local paths if touched.

## 13. Reliability

- Registry must be thread-safe because batch source runs execute concurrently.
- Runtime state loss on restart is intentional and required.
- Replace transient source results only after adapter fetch/classification succeeds. On failed ingestion, prefer leaving previous current runtime set untouched or clearing it only if product confirms; requirement says refresh when ingestion triggers again according to latest output, so on successful zero/new run clear/replace. Document and test failed-run behavior.
- Tracking persistence must be atomic. Consume transient entry only after commit.
- Log ingestion counts: fetched, persisted created/updated/unchanged, transient captured.
- Add monitoring/logging fields via standard logger; no new operational dependency.
- Performance: in-memory storage can grow with latest ingestion output. Since this is local single-user and refreshed per run, no external cache is needed. Consider a simple max-size guard only if existing adapter outputs are unbounded; not required by spec.

## 14. Dependencies

- SQLAlchemy session/model layer.
- Existing adapter contracts and registry.
- Existing classification rules/preferences.
- Existing tracking statuses.
- Existing Alembic migration process and schema guard.
- Existing source batch executor/threading behavior.

## 15. Assumptions

- The app remains single-user/local as stated in the product spec.
- Existing `SourceRun` rows may remain durable for all ingestion runs; the prohibition on ingestion metadata rows applies to job-specific artifacts for newly untracked jobs, not the source-run audit row itself.
- Transient result review can be provided by either a new route/template or an augmented existing jobs/source page, as long as IDs are clearly distinguished from persisted job IDs.

## Technical Assumptions Requiring Confirmation

- Failed ingestion run behavior for previous transient results: recommended behavior is to keep the last successful runtime set if fetch fails, and replace/clear only on successful ingestion completion.
- Whether `SourceRun.jobs_created_count` should be incremented when a transient job is later tracked. Recommended behavior is no; it should represent ingestion-time DB effects only.

## 16. Risks / Open Questions

- Current `ClassificationService` writes directly to DB; refactor must avoid rule drift between pure and persisted paths.
- Existing untracked rows may have `DigestItem`, `Reminder`, or `JobTrackingEvent` dependents even though untracked; cleanup must account for all FK dependents before deleting jobs.
- DB FKs do not show cascade rules in models; migration must delete children explicitly.
- Batch ingestion concurrency can cause registry replacement races if two runs for the same source overlap. Existing batch prevents concurrent batches, but single-source route may still be manually triggered concurrently unless guarded elsewhere.
- Transient IDs become invalid after restart/refresh; UI must handle this gracefully.

## 17. Implementation Notes

### Data cleanup / migration approach

Create a new Alembic revision after `20260429_0004`.

Upgrade steps:

1. Select `target_job_ids = SELECT id FROM job_postings WHERE tracking_status IS NULL`.
2. Select `decision_ids = SELECT id FROM job_decisions WHERE job_posting_id IN target_job_ids`.
3. Delete in child-to-parent order:
   - `job_decision_rules` where `job_decision_id IN decision_ids`
   - `job_decisions` where `job_posting_id IN target_job_ids`
   - `job_tracking_events` where `job_posting_id IN target_job_ids`
   - `reminders` where `job_posting_id IN target_job_ids`
   - `digest_items` where `job_posting_id IN target_job_ids`
   - `job_source_links` where `job_posting_id IN target_job_ids`
   - `job_postings` where `id IN target_job_ids AND tracking_status IS NULL`
4. Do not filter by or preserve `manual_keep`.
5. Make no-op successful when `target_job_ids` is empty.

Downgrade:

- Cannot restore deleted untracked rows. Downgrade should be a no-op with a comment explaining irreversible data cleanup.

### Backend implementation guidance

- Introduce a helper result type from `_resolve_persisted_tracked_match()` instead of overloading `_upsert_job()` with transient behavior.
- Keep DB session flushes only in the persisted branch.
- Build transient records from adapter candidate plus computed keys before any DB object is created.
- For duplicate candidates in one ingestion run, registry should dedupe by `(source_id, external_job_id)` when external ID exists, else normalized URL/canonical key. Keep the last candidate from the latest run.
- For tracking from transient state, perform DB matching again inside the transaction to handle races with another ingestion/tracking action.
- If matching finds an existing tracked job, update source link and tracking status rather than inserting a duplicate.

### Frontend/API impact guidance

- Existing `/jobs` should remain a persisted jobs view unless explicitly given a separate “current ingestion results” section.
- Use a discriminator in templates/API: `is_transient: true` or separate endpoints to avoid integer-vs-UUID confusion.
- Existing keep forms post to `/jobs/{job_id}/keep`; transient cards must post to the new transient tracking endpoint instead.

### Test strategy hooks

Unit tests:

- `IngestionOrchestrator` does not create `JobPosting`, `JobSourceLink`, `JobDecision`, or `JobDecisionRule` for new untracked candidates.
- Existing tracked match is updated and classified.
- `manual_keep=True` with `tracking_status=None` is treated as untracked in cleanup.
- Transient registry replaces source result set on subsequent successful run and clears on successful zero-job run.
- Registry is thread-safe for concurrent source writes.
- `TrackingService.track_transient_job()` persists job/link/decision/rules/event atomically.

API/integration tests:

- `POST /sources/{source_id}/run` followed by DB assertions: fetched count set, no untracked job rows.
- `GET /ingestion/transient-jobs` returns current transient results.
- Tracking a transient job returns created persisted job and survives app/session restart via DB.
- Unknown/expired transient ID returns 404.
- Batch ingestion stores transient results without cross-source overwrites.

Migration tests:

- Existing untracked rows and all dependents are deleted.
- Existing tracked rows survive regardless of `manual_keep`.
- Running cleanup twice succeeds and deletes nothing extra.

### Rollback considerations

- Code rollback after migration cannot restore deleted untracked rows. This is acceptable per product scope but should be noted in release notes.
- If rollback is required before migration, revert code to old persistence behavior and do not run cleanup revision.
- If rollback is required after migration, tracked jobs remain intact; old code may resume persisting new untracked jobs unless the migration/code change is re-applied.
- The cleanup migration downgrade should not attempt restoration.
