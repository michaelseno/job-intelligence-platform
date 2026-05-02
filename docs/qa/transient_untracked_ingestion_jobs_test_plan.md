# Test Plan

## 1. Feature Overview

Feature: transient untracked ingestion jobs.

Branch/context: `feature/transient_untracked_ingestion_jobs`.

Goal: ingestion must persist only tracked jobs, where tracked means `tracking_status IS NOT NULL`. Newly ingested untracked jobs (`tracking_status IS NULL`) must remain visible only through current runtime/app state, must not create durable job-specific records, must be replaced on subsequent ingestion, and must disappear after application restart. If the user assigns any valid non-null tracking status to a transient job, the system must persist that job and its related source link, classification result/rules, ingestion/source-run attribution, and tracking metadata as a normal tracked job.

Primary validation references:

- Product spec: `docs/product/transient_untracked_ingestion_jobs_product_spec.md`
- Technical design: `docs/architecture/transient_untracked_ingestion_jobs_technical_design.md`
- UI/UX spec: `docs/uiux/transient_untracked_ingestion_jobs_design_spec.md`

In-scope validation surfaces:

- Ingestion domain behavior
- Runtime transient ingestion registry
- Classification preview versus persisted classification
- Tracking service transient-to-persisted flow
- API routes for transient list/detail/tracking
- Jobs/source UI behavior for temporary results
- Alembic/data cleanup of existing untracked persisted jobs and dependents
- Restart/runtime-state behavior
- Regression of existing tracked job update and persisted job routes

Out of scope for this plan:

- Changes to source adapter fetch logic
- Changes to classification scoring/rules except persistence-neutral preview parity
- New tracking status values
- Multi-user/session synchronization
- Recovery/archive of deleted untracked jobs

## 2. Acceptance Criteria Mapping

| AC | Requirement summary | Test coverage |
| --- | --- | --- |
| AC-01 | New `tracking_status IS NULL` ingestion result creates no `job_postings` row | Unit ingestion test, API run integration test, DB before/after assertion |
| AC-02 | New untracked result creates no job-specific source-link/classification/metadata rows | Unit ingestion test, API run integration test, DB assertions for `job_source_links`, `job_decisions`, `job_decision_rules`, job-specific ingestion linkage |
| AC-03 | New untracked results are visible from current runtime/app state before refresh/restart | API `GET /ingestion/transient-jobs`, UI `/jobs` temporary result test |
| AC-04 | Subsequent ingestion refreshes transient result set from latest output | Registry unit test, API/UI two-run integration test |
| AC-05 | App restart removes transient untracked visibility | Restart integration test, API/UI post-restart assertions |
| AC-06 | Existing tracked persisted job matched during ingestion is updated normally | Unit and integration tests for tracked match update, source link update, classification persistence |
| AC-07 | `manual_keep=true` and `tracking_status IS NULL` new result is not persisted | Unit/API ingestion test with manual_keep true candidate |
| AC-08 | Existing persisted `manual_keep=true`, `tracking_status IS NULL` job is cleaned up | Migration/cleanup test |
| AC-09 | Existing `tracking_status IS NOT NULL` job survives cleanup regardless of `manual_keep` | Migration/cleanup test with `manual_keep=true/false/null` tracked variants |
| AC-10 | Assigning any non-null tracking status to transient job persists job | API/UI tracking test, DB assertion |
| AC-11 | Tracking transient persists source link, latest classification result, and ingestion metadata | Tracking integration test, transactional DB assertions |
| AC-12 | Transient job tracked and persisted survives restart as tracked job | End-to-end track then restart test |
| AC-13 | Cleanup removes existing DB jobs where `tracking_status IS NULL` | Migration/cleanup DB test |
| AC-14 | Cleanup removes dependent records or prevents orphans for removed untracked jobs | Migration/cleanup DB referential integrity test |
| AC-15 | Cleanup is idempotent and does not delete tracked jobs on repeat run | Migration/cleanup double-run test |

## 3. Test Scenarios

### Unit Tests Expected

Recommended location: `tests/unit/` or existing project unit test structure.

1. **Ingestion skips DB persistence for new untracked candidate**
   - Maps to: AC-01, AC-02
   - Purpose: verify the ingestion orchestrator sends unmatched `tracking_status=None` candidates to runtime registry only.
   - Input: enabled source, adapter result with one normalized job candidate and no existing tracked match.
   - Expected output: no `JobPosting`, `JobSourceLink`, `JobDecision`, or `JobDecisionRule` is added/flushed for the candidate; transient registry receives one item; `SourceRun.jobs_fetched_count` reflects fetched candidate.
   - Validation logic: inspect DB row counts before/after and registry contents.

2. **`manual_keep` is ignored for new untracked persistence**
   - Maps to: AC-07
   - Input: candidate/runtime metadata representing `manual_keep=true`, `tracking_status=None`.
   - Expected output: no persisted job-specific records; transient item is created.
   - Validation logic: DB count remains unchanged for job/link/decision tables.

3. **Existing tracked match follows persisted update path**
   - Maps to: AC-06
   - Input: existing `JobPosting` with non-null `tracking_status`; adapter candidate matching by source/external ID, normalized URL, or canonical key.
   - Expected output: existing job fields/source link/classification are updated; no duplicate job is inserted; no transient item is created for that matched tracked candidate.
   - Validation logic: same job ID remains; updated title/company/url/timestamps/classification fields match latest candidate; link metadata updated.

4. **Existing untracked persisted match is not treated as tracked during migration window**
   - Maps to: AC-01, AC-13
   - Input: existing `JobPosting.tracking_status=None`, candidate matching it.
   - Expected output: orchestrator must not update or preserve the untracked persisted row as a tracked job; candidate is transient or cleanup removes row depending on execution path.
   - Validation logic: no tracked update branch invocation; no new dependent rows for that untracked row.

5. **Transient registry replaces source result set on successful subsequent run**
   - Maps to: AC-04
   - Input: source 1 first run has jobs A/B, second successful run has job C.
   - Expected output: registry for source 1 contains C only; A/B IDs return absent.
   - Validation logic: registry list/detail lookup by old IDs fails; new ID succeeds.

6. **Transient registry clears/replaces on successful zero-job run**
   - Maps to: AC-04 and edge case zero jobs
   - Input: source with existing transient results; successful adapter result with zero jobs.
   - Expected output: no transient results remain for that source.
   - Validation logic: registry count for source is zero.

7. **Transient registry source isolation and thread safety**
   - Maps to: AC-03, AC-04
   - Input: concurrent writes/replacements for different source IDs and overlapping reads.
   - Expected output: no cross-source overwrites; no race exceptions; each source returns only its latest set.
   - Validation logic: assert per-source item sets after concurrent operations.

8. **Classification preview is persistence-neutral and parity-safe**
   - Maps to: AC-02, AC-11
   - Input: candidate data and preference/rule setup.
   - Expected output: preview returns bucket/score/sponsorship/rules without creating DB decision/rule rows; equivalent persisted classification yields same outcome when transient is tracked.
   - Validation logic: DB decision/rule counts unchanged after preview; compare preview snapshot fields to persisted decision fields after tracking.

9. **Tracking service persists transient atomically**
   - Maps to: AC-10, AC-11
   - Input: valid transient ID, valid non-null tracking status, optional note.
   - Expected output: creates/updates `JobPosting`, `JobSourceLink`, `JobDecision`, `JobDecisionRule`, `JobTrackingEvent` in one transaction and consumes transient entry only after commit.
   - Validation logic: all records exist after success; induced DB failure rolls back all records and leaves transient entry available.

10. **Tracking service rejects null/empty/invalid status**
    - Maps to: negative coverage for AC-10
    - Input: transient ID with `tracking_status` null, empty string, or unsupported value.
    - Expected output: validation error; no DB records created; transient item remains available.
    - Validation logic: assert error type/status and unchanged DB counts.

11. **Duplicate/concurrent transient tracking does not create duplicate jobs**
    - Maps to: AC-10, AC-11 and technical duplicate handling
    - Input: two tracking requests for same transient ID or two transient records matching the same canonical key/source external ID.
    - Expected output: one persisted tracked job; second request returns 404/409 or updates existing tracked match safely per contract.
    - Validation logic: unique persisted job count by canonical key/source external ID equals one.

### Integration and API Tests Expected

Recommended location: `tests/api/` and/or existing integration test structure.

1. **POST ingestion run with only untracked jobs**
   - Maps to: AC-01, AC-02, AC-03
   - Steps:
     1. Seed active source and preferences.
     2. Mock adapter to return two new untracked jobs.
     3. Capture DB counts for `job_postings`, `job_source_links`, `job_decisions`, `job_decision_rules`, `source_runs`.
     4. `POST /sources/{source_id}/run` or configured run endpoint.
     5. Query DB and `GET /ingestion/transient-jobs`.
   - Expected:
     - `source_runs` increases by one.
     - Job/link/decision/rule counts do not increase for untracked candidates.
     - transient API returns two items with `tracking_status: null` and runtime IDs.

2. **Transient list filtering by source**
   - Maps to: AC-03
   - Steps: run ingestion for source 1 and source 2, then call `GET /ingestion/transient-jobs?source_id=<id>`.
   - Expected: each response contains only matching source items; invalid non-integer `source_id` returns `422`.

3. **Transient detail endpoint behavior**
   - Maps to: AC-03
   - Steps: call `GET /ingestion/transient-jobs/{transient_job_id}` for a current item and for malformed/unknown IDs.
   - Expected: current item returns details/classification snapshot/source attribution; unknown, malformed, consumed, refreshed-away IDs return `404` and do not query persisted job by that ID.

4. **Tracking transient via API persists all required records**
   - Maps to: AC-10, AC-11, AC-12
   - Steps:
     1. Run ingestion to create transient job.
     2. `POST /ingestion/transient-jobs/{id}/tracking-status` with each representative valid non-null status, at minimum `saved` plus one other valid status if available.
     3. Query DB.
     4. Call persisted job detail endpoint.
   - Expected:
     - API returns `201 Created` for new persisted job or documented `200 OK` for duplicate tracked match.
     - `job_postings.tracking_status` equals submitted status and is non-null.
     - `job_source_links` contains source ID, external job ID/raw payload/source run attribution as applicable.
     - `job_decisions` and `job_decision_rules` exist and match latest classification snapshot or recomputation.
     - `job_tracking_events` exists for the status change/save event.
     - transient ID is consumed and no longer returned in transient list/detail.

5. **Tracking transient invalid request handling**
   - Maps to: negative coverage AC-10
   - Steps: submit null/empty/invalid `tracking_status`, unknown transient ID, and repeated request after consumption.
   - Expected: `400` for invalid status; `404` for absent/consumed transient ID or `409` if implementation uses conflict for concurrent consumption; no duplicate persisted records.

6. **Mixed ingestion: new untracked plus existing tracked match**
   - Maps to: AC-01, AC-02, AC-03, AC-06
   - Steps: seed one tracked persisted job with source link; mock adapter returns matching job with updated data and one new untracked job.
   - Expected: tracked job is updated/classified; one transient item exists for new untracked job; no untracked job row exists.

7. **Subsequent ingestion refreshes transient API results**
   - Maps to: AC-04
   - Steps: first run returns A/B; second successful run returns C; query transient API after each run.
   - Expected: after second run, A/B IDs return `404`; list contains C only for that source.

8. **Restart clears transient state but preserves tracked converted job**
   - Maps to: AC-05, AC-12
   - Steps:
     1. Run ingestion and capture transient ID A.
     2. Restart app/test process or instantiate a fresh app with same DB and empty runtime registry.
     3. Assert A is absent from transient API/UI.
     4. Repeat by tracking transient B before restart, then restart.
   - Expected: untracked A is gone after restart; tracked B remains available through `/jobs` and `/jobs/{job_id}`.

9. **SourceRun counter semantics**
   - Maps to: AC-01, AC-02 and design assumptions
   - Steps: run ingestion with only transient untracked candidates, with only tracked updates, and with mixed results.
   - Expected: `jobs_fetched_count` reflects adapter candidates; `jobs_created_count` counts persisted creations only and is not inflated by transient untracked discoveries; update/unchanged counts apply only to persisted tracked effects unless implementation explicitly documents separate transient counts.

10. **Batch ingestion cross-source behavior**
    - Maps to: AC-03, AC-04, regression
    - Steps: run batch ingestion for multiple sources with transient results.
    - Expected: transient results are present for each source; later per-source run replaces only that source's transient set and does not erase other sources unless batch semantics intentionally replace all completed source sets.

### UI Tests Expected

Recommended location: `tests/ui/`.

1. **Jobs page displays transient results as temporary**
   - Maps to: AC-03 and UI spec
   - Steps: run ingestion with untracked results; navigate to `/jobs`.
   - Expected: page displays current transient jobs; informational callout appears with temporary-session copy; each transient row/card has visible `Temporary` badge and screen-reader text; count summary distinguishes tracked and temporary counts.

2. **Persisted tracked jobs are visually distinct from transient jobs**
   - Maps to: AC-06
   - Steps: seed tracked job and transient job; navigate to `/jobs`.
   - Expected: tracked job has normal tracking badge/status and no `Temporary` badge; transient job has temporary labeling and tracking action.

3. **Transient tracking UI converts row/card to persisted job**
   - Maps to: AC-10, AC-11, AC-12
   - Steps: select valid non-empty status on transient row/card and submit.
   - Expected: saving state disables controls and uses `Saving…`/`aria-busy`; success shows “Job tracked and saved.”; temporary badge removed; detail link changes to `/jobs/{persisted_job_id}`; persisted job appears after page reload/restart.

4. **Transient detail navigation is runtime-safe**
   - Maps to: AC-03, AC-05
   - Steps: click details for transient item if implemented.
   - Expected: UI uses transient detail route or inline details, not `/jobs/{integer_db_id}`; after refresh/restart/consumption unavailable detail shows clear error and prompt to rerun ingestion.

5. **Refresh/restart removes stale temporary UI**
   - Maps to: AC-04, AC-05
   - Steps: view transient results, run ingestion again with different results, then restart app.
   - Expected: previous temporary rows disappear after refresh; after restart no stale temporary rows or old persisted untracked rows appear.

6. **Accessibility and responsive behavior**
   - Maps to: UI accessibility requirements
   - Expected: tracking select labels include job title; errors use `role="alert"`; temporary status is visible text, not color-only; keyboard order reaches title/details/source link/select/submit; mobile card shows temporary badge and full-width tracking controls when constrained.

### Migration/Cleanup Tests Expected

Recommended location: migration test suite or `tests/integration/`.

1. **Cleanup removes existing untracked jobs and dependents**
   - Maps to: AC-08, AC-13, AC-14
   - Seed:
     - `job_postings` row with `tracking_status=NULL`, `manual_keep=true`.
     - related `job_source_links`, `job_decisions`, `job_decision_rules`, `job_tracking_events`, `reminders`, `digest_items` where schema supports them.
   - Expected after migration/cleanup: target job row removed; dependent rows removed; no orphaned rows remain.

2. **Cleanup preserves tracked jobs regardless of manual_keep**
   - Maps to: AC-09, AC-15
   - Seed tracked jobs with `tracking_status IS NOT NULL` and `manual_keep=true`, `false`, and `NULL` if nullable.
   - Expected: all tracked jobs and their dependents remain after cleanup.

3. **Cleanup is idempotent**
   - Maps to: AC-15
   - Steps: run cleanup/migration twice against same DB.
   - Expected: second run succeeds as no-op for previously deleted records; tracked rows unchanged; no FK errors.

4. **Cleanup with no untracked jobs succeeds**
   - Maps to: AC-15 and edge coverage
   - Expected: migration completes without error and without modifying tracked rows.

5. **Interrupted/partial cleanup recovery**
   - Maps to: edge case
   - Seed partial state such as missing decision rows but remaining rules impossible/possible per FK settings, or some child tables already deleted.
   - Expected: cleanup completes without relying on every child record existing and leaves no orphaned records.

### Regression Tests Expected

1. Existing `/jobs`, `/jobs/{job_id}`, `/jobs/{job_id}/tracking-status`, and `/jobs/{job_id}/keep` continue to work for persisted tracked jobs.
2. Existing source run success/failure behavior and source health updates remain intact.
3. Existing classification persistence for tracked jobs is unchanged.
4. Existing filters/sorting on `/jobs` still apply correctly to persisted tracked jobs and do not accidentally expose deleted/untracked DB rows.
5. Existing source adapters and adapter validation behavior remain unchanged.
6. Existing deduplication/matching for tracked persisted jobs does not create duplicate rows.
7. Existing database migrations can upgrade from the previous head revision to the new cleanup revision.

## 4. Edge Cases

1. Ingestion returns zero jobs: no job rows created, transient set for that source is empty, UI shows no temporary callout.
2. Ingestion returns only new untracked jobs: DB has no job-specific inserts; UI/API shows temporary results.
3. Ingestion returns a mix of new untracked and existing tracked matches: tracked jobs update, untracked are transient only.
4. Same job appears from multiple sources before tracking: implementation dedupes or displays source labels clearly; tracking creates one persisted job when matched by canonical/source rules.
5. Same source returns duplicate candidate within one run: registry should dedupe by source/external ID, normalized URL, or canonical key per design; no duplicate persisted rows.
6. User attempts to track a transient job after another ingestion run refreshed it away: API returns `404` or `409`; UI shows “temporary result no longer available” copy; no DB write.
7. User attempts to track after app restart: transient ID unavailable; no DB write.
8. User submits empty/null/invalid tracking status: request rejected; transient item remains; no DB write.
9. User/client includes `manual_keep=true` while tracking transient: manual_keep must not be accepted as persistence signal; persistence depends only on valid non-null tracking status.
10. Existing untracked job has `manual_keep=true`: cleanup deletes it.
11. Existing tracked job has `manual_keep=false` or null: cleanup preserves it.
12. Existing untracked job has source links/classification/reminder/digest/tracking-event dependents: cleanup deletes children first or uses safe cascade with no orphans.
13. Ingestion failure after previous transient results exist: validate documented behavior. Preferred design says failed run does not replace last successful transient set; if implementation clears on failure, UI must show corresponding failure copy. This behavior must be explicitly documented before QA sign-off.
14. Tracking transaction fails midway: rollback leaves no partial persisted job/link/decision/event and transient item remains available for retry.
15. Concurrent requests track the same transient ID: at most one persisted job; second request receives conflict/not found and no duplicate records.
16. Batch source runs occur concurrently: registry access is thread-safe and source result sets do not overwrite each other incorrectly.
17. Restart after tracking succeeds but before UI reload: persisted job is present; transient registry absence does not lose tracked job.

## 5. Test Types Covered

- **Unit:** ingestion persistence gating, tracked matching, transient registry replacement/source isolation/thread safety, classification preview, tracking service validation/atomicity, manual_keep predicate exclusion.
- **Integration:** source run endpoint plus DB assertions, transient API list/detail/tracking, DB transaction behavior, restart with same DB and fresh runtime registry, batch source behavior.
- **API:** `GET /ingestion/transient-jobs`, `GET /ingestion/transient-jobs/{transient_job_id}`, `POST /ingestion/transient-jobs/{transient_job_id}/tracking-status`, existing persisted job endpoints regression, validation/error status codes.
- **UI:** `/jobs` mixed persisted/transient display, temporary callout/badge/counts, transient detail behavior, tracking form states and success/error messages, restart/refresh stale-state handling, accessibility/responsive checks.
- **Migration/Cleanup:** Alembic upgrade cleanup, dependent deletion, idempotency, tracked preservation, no-orphan assertions.
- **Regression:** existing tracked job lifecycle, source ingestion health/run history, classification, persisted job list/detail/tracking/keep, migration chain.
- **Negative:** invalid status, unknown/expired transient ID, malformed source filter, concurrent duplicate tracking, ingestion failure behavior, invalid manual_keep assumptions.

## 6. Coverage Justification

This plan covers all validated requirements by validating both absence and presence conditions:

- Absence of durable records for newly ingested untracked jobs is proven through direct DB before/after assertions across job, source-link, classification, and job-specific metadata tables.
- Presence of transient visibility is proven through API and UI tests that read only runtime state, then verify replacement on new ingestion and loss after restart.
- Tracked-job continuity is protected through matched-update tests and persisted endpoint regressions.
- The `manual_keep` non-rule is tested in both new ingestion and cleanup paths so it cannot accidentally preserve or persist untracked jobs.
- Cleanup safety is tested with child dependents, tracked preservation, no-target runs, and repeated execution to protect production/local upgrade scenarios.
- Tracking from transient state is validated transactionally, including persistence of all related artifacts and survival after restart.
- UI tests verify that users can distinguish temporary versus persisted records and that user-facing copy does not imply untracked durability.

## 7. DB Assertion Matrix

Use table names from `app/persistence/models.py`; adjust only if implementation names differ.

### Before Ingestion

- Capture counts and relevant rows for:
  - `job_postings`
  - `job_source_links`
  - `job_decisions`
  - `job_decision_rules`
  - `job_tracking_events`
  - `source_runs`
  - `reminders`
  - `digest_items`
- Seed at least:
  - one existing tracked job with `tracking_status IS NOT NULL`
  - one existing untracked job with `tracking_status IS NULL`, including `manual_keep=true`, for cleanup-specific tests
  - dependent records for cleanup targets

### After Ingestion of New Untracked Jobs

- Assert no `job_postings` row exists by candidate normalized URL, canonical key, source external ID, company/title unique test marker.
- Assert no `job_source_links` row exists for candidate source/external ID unless linked to an already tracked job.
- Assert no `job_decisions` or `job_decision_rules` rows exist for the candidate.
- Assert no job-specific ingestion metadata rows exist solely for the candidate.
- Assert `source_runs` row exists for the ingestion execution and `jobs_fetched_count` reflects adapter candidates.
- Assert persisted-created counters do not count transient untracked candidates.

### After Ingestion of Existing Tracked Match

- Assert same `job_postings.id` remains.
- Assert fields expected to update have latest values.
- Assert `tracking_status` remains non-null unless deliberately changed by existing behavior.
- Assert `job_source_links` updated/inserted for tracked job as pre-feature behavior requires.
- Assert latest classification fields and decision/rule rows are updated/persisted.
- Assert no transient duplicate appears for the matched tracked job.

### After Tracking a Transient Job

- Assert one persisted `job_postings` row exists for the transient candidate.
- Assert `tracking_status IS NOT NULL` and equals submitted valid status.
- Assert `job_source_links.job_posting_id` points to persisted job and includes source/run/external/raw metadata where applicable.
- Assert `job_decisions.job_posting_id` points to persisted job.
- Assert `job_decision_rules.job_decision_id` points to persisted decision.
- Assert `job_postings.latest_decision_id/latest_bucket/latest_score` reference persisted classification outcome.
- Assert `job_tracking_events.job_posting_id` exists for the tracking action.
- Assert transient registry no longer returns the consumed ID.
- Assert repeated tracking of the same ID does not create additional `job_postings` rows.

### After Cleanup/Migration

- Assert all `job_postings.tracking_status IS NULL` rows seeded for cleanup are gone.
- Assert tracked jobs with any `manual_keep` value remain.
- Assert no orphaned rows remain in:
  - `job_source_links`
  - `job_decisions`
  - `job_decision_rules`
  - `job_tracking_events`
  - `reminders`
  - `digest_items`
- Assert second cleanup/migration execution succeeds and row counts remain stable.

## 8. Cleanup/Migration Validation

Minimum implementation-ready cleanup test data set:

| Seed case | tracking_status | manual_keep | Dependents | Expected cleanup result |
| --- | --- | --- | --- | --- |
| Untracked kept legacy job | `NULL` | `true` | link, decision, rules, event, reminder, digest item | job and owned dependents removed |
| Untracked normal legacy job | `NULL` | `false` | link and decision | job and owned dependents removed |
| Tracked saved job | `saved` or equivalent valid status | `true` | link, decision, rules | all records preserved |
| Tracked non-kept job | non-null valid status | `false` or `NULL` | link | all records preserved |
| No-target DB | no `NULL` statuses | any | any | cleanup no-op success |

Validation requirements:

- Run migration through the same Alembic mechanism used by the app, not only direct helper invocation.
- Confirm upgrade from the prior revision to the cleanup revision.
- Confirm cleanup predicates do not reference `manual_keep` as a retention rule.
- Confirm downgrade behavior is documented as no-op/irreversible data cleanup if applicable.
- Confirm cleanup can be re-run or the migration logic is otherwise idempotent in test harness.

## 9. Restart and Runtime-State Behavior Validation

Restart validation must prove transient data is not durable.

Required approach:

1. Start app/test client with clean runtime registry and persistent test DB.
2. Run ingestion with new untracked jobs.
3. Confirm DB has no job-specific rows for those jobs.
4. Confirm transient API/UI shows current temporary jobs.
5. Simulate restart by creating a new app process/application instance with the same DB and a fresh runtime registry. If the test framework cannot launch a subprocess, explicitly reinitialize the registry and app dependency container in a way equivalent to process startup and document the limitation.
6. Confirm transient API returns empty/no previous jobs and detail for old transient ID returns `404`.
7. Confirm `/jobs` does not show previous transient jobs or fallback persisted untracked jobs.
8. Repeat with a transient job tracked before restart; confirm it appears after restart as a normal persisted tracked job with no `Temporary` badge.

Required evidence:

- Test logs showing pre-restart transient ID(s), post-restart transient API response, and persisted DB row state.
- UI screenshot or HTML assertion showing no stale temporary result after restart.
- DB query output proving tracked converted job survived restart.

## 10. Required Evidence for QA Sign-Off

QA sign-off must not be granted without the following evidence captured in the final test report:

1. **Automated test execution output**
   - Exact commands run.
   - Full pass/fail summary.
   - Any skipped tests with justification.

2. **Acceptance criteria traceability**
   - Matrix showing AC-01 through AC-15 mapped to executed tests and outcomes.

3. **DB assertion evidence**
   - Before/after row counts and targeted row queries for ingestion-only, tracking, and cleanup scenarios.
   - Proof that no untracked candidate rows or dependents were persisted.
   - Proof that tracked converted jobs and existing tracked matched jobs persisted correctly.

4. **API evidence**
   - Request/response status codes and bodies for transient list/detail/tracking success and failure paths.
   - Evidence for invalid status, unknown/expired ID, and invalid source filter.

5. **UI evidence**
   - Screenshots or saved HTML/test assertions for `/jobs` showing temporary callout, `Temporary` badge, count summary, tracking form, success/error handling, and absence after restart/refresh.
   - Accessibility assertions for labels, alert roles, visible non-color-only temporary state, and keyboard-reachable controls.

6. **Migration evidence**
   - Alembic upgrade logs.
   - Cleanup before/after DB queries.
   - Idempotency/double-run result.
   - No-orphan query results.

7. **Restart evidence**
   - Logs proving runtime registry is empty after restart while DB remains unchanged for untracked candidates.
   - Proof tracked transient conversion survives restart.

8. **Regression evidence**
   - Existing persisted job, source ingestion, classification, tracking status, and keep-route tests passed.

9. **Failure classification if any test fails**
   - Each failure must be classified as Application Bug, Test Bug, Environment Issue, or Flaky Test.
   - Include root cause hypothesis, reproduction steps, logs/error messages, and severity.

QA decision rule:

- Approve only if all critical AC-mapped tests pass, cleanup is proven safe/idempotent, no blocking defects remain, and evidence proves untracked jobs are transient-only while tracked jobs persist and update correctly.
- Do not approve if any AC-01, AC-02, AC-05, AC-10, AC-11, AC-13, AC-14, or AC-15 validation fails or is unexecuted without approved exception.
