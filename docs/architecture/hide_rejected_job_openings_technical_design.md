# Hide Rejected Job Openings Technical Design

## Feature Overview

Hide job openings whose current display classification is `rejected` from the primary user-facing job openings display by default. Rejected jobs remain persisted and remain available to non-main/admin/debug paths unless those paths intentionally reuse the main display query.

The implementation should be primarily backend/query-layer filtering, with a small frontend/template update to avoid exposing a rejected bucket option on the main Jobs page.

## Product Requirements Summary

- The main job openings display must exclude jobs classified as `rejected`.
- Jobs classified as `matched` or `review` must remain visible when they satisfy existing filters.
- Rejected jobs must not be deleted or reclassified by this feature.
- Filtering must happen before user-facing list counts and pagination where those exist.
- Search, sort, source, tracking, and bucket filters must not accidentally reintroduce rejected jobs.
- Direct rejected-job detail access is not changed unless the existing detail route uses the same visibility rules.

## Scope

### In Scope

- Update the Jobs list/API (`GET /jobs`) default query to exclude explicitly rejected jobs.
- Keep rejected jobs hidden even when `bucket=rejected` is supplied to `GET /jobs`.
- Update Dashboard job summaries/previews that represent the actionable jobs surface to use the same non-rejected visibility rule.
- Preserve existing source-delete visibility behavior while adding rejected-status filtering.
- Remove or suppress the `rejected` option from the main Jobs page bucket selector.
- Add tests for API, HTML, search/filter behavior, status transitions, and source-delete compatibility.

### Out of Scope

- Deleting, archiving, or reclassifying rejected jobs.
- Adding a rejected-jobs management page or explicit “show rejected” toggle.
- Changing the classification algorithm.
- Changing ingestion behavior.
- Hiding rejected jobs from every route that references jobs, unless that route is part of the main display or intentionally shares its query.

## Architecture Overview

Current repository findings:

- Stack: FastAPI, SQLAlchemy 2.x, Jinja templates, SQLite/PostgreSQL-compatible schema.
- Canonical display classification currently used by list/dashboard code is `JobPosting.latest_bucket`.
- Classification writes both `job_decisions` and denormalized fields on `job_postings`: `latest_bucket`, `latest_score`, `latest_decision_id`.
- Existing source-delete feature centralizes normal job visibility in `app/domain/job_visibility.py` via `visible_job_predicate()` and `apply_visible_jobs()`.
- `GET /jobs` currently builds from `apply_visible_jobs(select(JobPosting))`, then applies bucket/tracking/search SQL filters, source filtering in memory, and in-memory sort. There is no current pagination or explicit total-count response.
- `GET /dashboard` currently loads all `apply_visible_jobs(select(JobPosting))` jobs and calculates matched/review/rejected counts in memory.
- `GET /jobs/{job_id}` currently uses `apply_visible_jobs()` for source-delete visibility. Product spec says direct detail route behavior should not change for rejected jobs.

Recommended design:

1. Add a reusable actionable-main-display predicate that composes with existing source-delete visibility.
2. Apply that predicate at the base SQL query for `GET /jobs` and Dashboard job summary/previews.
3. Do not apply the new rejected filter to `GET /jobs/{job_id}` or job mutation routes solely because a job is rejected.
4. Update the Jobs HTML bucket filter to show only `All actionable`, `Matched`, and `Review`.

## System Components

### Backend Components Affected

- `app/domain/job_visibility.py`
  - Add helper(s) for main display/actionable jobs, for example:
    - `actionable_job_status_predicate()`
    - `main_display_job_predicate()`
    - `apply_main_display_jobs(query)`
  - The new helper must include the existing source-delete visibility predicate and exclude explicit `latest_bucket == "rejected"`.
- `app/web/routes.py`
  - `dashboard()` should use the main-display helper for actionable job counts/cards.
  - `build_jobs_query()` should use the main-display helper as its base query.
  - `get_job()`, `keep_job()`, and `update_tracking_status()` should continue using `apply_visible_jobs()` only, not the main-display helper, unless product later decides direct rejected detail access should 404.
- `app/domain/notifications.py`
  - No required change for digest generation because it already selects only current decisions with bucket in `matched`/`review`.
  - Reminder generation/listing currently may include rejected tracked jobs if source-visible. This is out of the main Jobs display; do not change unless product defines reminders/tracking as part of the main display.

### Frontend / Template Components Affected

- `app/templates/jobs/list.html`
  - Remove `rejected` from the bucket dropdown.
  - Prefer option label `All actionable` or retain `All buckets` if minimal copy change is preferred. The returned set is no longer all stored buckets.
- `app/web/templates/jobs/list.html`
  - Repository contains duplicate template paths. Keep this copy in sync if it is still used by `Jinja2Templates` fallback order.
- Dashboard template does not currently show rejected count; no required template change.

## Data Models and Storage Design

No schema migration is required.

Relevant existing fields:

- `job_postings.latest_bucket`: denormalized current/latest display bucket. Expected values include `matched`, `review`, `rejected`; may be `NULL`.
- `job_postings.latest_decision_id`: points to the latest `job_decisions` row.
- `job_decisions.bucket` and `job_decisions.is_current`: historical classification records. Existing list code does not join this table.

Storage behavior:

- Rejected jobs remain in `job_postings`, `job_decisions`, `job_source_links`, tracking, reminders, and digest history unless affected by unrelated cleanup features.
- Filtering should not mutate `latest_bucket` or decision rows.

## API Contracts

### GET `/jobs`

Request parameters remain unchanged:

- `bucket`: optional string
- `tracking_status`: optional string
- `source_id`: optional integer
- `search`: optional string
- `sort`: optional string

Response remains the existing list of `JobPosting` objects for JSON clients, or the existing HTML page for browser clients.

New behavior:

- Base result set excludes explicit `latest_bucket == "rejected"` before other filters are applied.
- `GET /jobs?bucket=matched` returns matched actionable jobs.
- `GET /jobs?bucket=review` returns review actionable jobs.
- `GET /jobs?bucket=rejected` returns an empty list / no-results HTML state. No 400 is required for backward compatibility, but the HTML UI should stop presenting this option.
- Search/source/tracking filters only operate inside the non-rejected result set.

### GET `/dashboard`

JSON counts and HTML summary/cards should be based on the actionable main-display set:

- `matched_count`: count of visible actionable matched jobs.
- `review_count`: count of visible actionable review jobs.
- `rejected_count`: should be `0` or omitted in a future contract. For backward compatibility, keep the field and return `0` after filtering.
- Dashboard preview cards must not include rejected jobs.

### GET `/jobs/{job_id}`

No behavior change for rejected jobs in this feature.

- A rejected job detail URL remains accessible if the job passes existing source-delete visibility rules.
- A rejected job may still return 404 if hidden/deleted by existing source-delete cleanup rules.

## Frontend / Client Impact

Both backend and frontend changes are needed.

- Backend is required to ensure search, counts, and any future pagination are correct and rejected jobs are not merely hidden visually.
- Frontend/template impact is limited to main Jobs filter copy/options and tests expecting rejected in the dropdown.
- Empty state can reuse the existing `No jobs found` message. If all jobs are rejected, the Jobs page should show the existing no-results state without error language.

## Backend Logic / Service Behavior

### Status Handling

Use `JobPosting.latest_bucket` as the main-display status source for MVP because it is the field currently used by Jobs and Dashboard and is updated by `ClassificationService.classify_job()`.

Default inclusion rule:

```text
main display eligible = source-delete-visible AND latest_bucket IS NOT "rejected"
```

This means:

- `matched`: shown.
- `review`: shown.
- `rejected`: hidden.
- `NULL` / missing classification: shown as actionable/unclassified for MVP.
- Unknown non-`rejected` values: shown for backward compatibility, but should be monitored/tested; product may later choose to restrict to only `matched` and `review`.

Rationale for null/unknown default: the product spec explicitly mandates hiding rejected jobs and identifies null/unknown handling as open. Preserving non-rejected visibility avoids accidentally hiding newly ingested or partially classified jobs.

### Query Predicate Shape

In `app/domain/job_visibility.py`, compose predicates rather than duplicating route logic:

```text
main_display_job_predicate = visible_job_predicate AND actionable_status_predicate
```

When implementing in SQLAlchemy, account for SQL three-valued logic: `latest_bucket != "rejected"` alone does not include `NULL`; include an explicit `IS NULL` branch.

### Counts and Pagination Expectations

- Current code has no pagination and no Jobs total count field.
- Dashboard counts must be calculated after applying the main-display predicate.
- If pagination is added later, `apply_main_display_jobs()` must be applied before `COUNT(*)`, `LIMIT`, and `OFFSET`.
- Avoid UI-only filtering because it would create short pages and inflated counts once pagination/counts exist.

### Source Filtering and Sorting

- Current `source_id` filtering is performed in memory by `filter_jobs_by_source()` after the SQL query. This is acceptable for current no-pagination behavior but is not suitable if pagination/counts are added.
- Future pagination work should move source filtering and sorting into SQL before `COUNT/LIMIT/OFFSET`.

## File / Module Structure

Likely files to modify downstream:

- `app/domain/job_visibility.py`
  - Add main-display/actionable visibility helpers.
- `app/web/routes.py`
  - Import and use `apply_main_display_jobs` in `dashboard()` and `build_jobs_query()`.
  - Keep detail/mutation routes on `apply_visible_jobs`.
- `app/templates/jobs/list.html`
  - Remove rejected bucket option; update all-buckets label if desired.
- `app/web/templates/jobs/list.html`
  - Mirror template change if duplicate path remains active.
- Tests:
  - `tests/unit/test_job_visibility.py`
  - `tests/integration/test_api_flow.py` or a new integration test for `/jobs` filtering.
  - `tests/integration/test_html_views.py`
  - `tests/ui/test_saas_dashboard_ui_revamp.py` if selectors/snapshots include bucket options.

## Security and Access Control

- This feature is display filtering, not access control.
- Do not rely on hidden list membership to protect rejected job data.
- Direct details remain accessible per product spec; if rejected jobs become sensitive later, a separate authorization/access-control design is required.
- No sensitive job content should be added to telemetry/logs.

## Reliability / Operational Considerations

- The predicate is simple and index-friendly if `latest_bucket` is indexed in the future; no migration is required now.
- Because filtering is centralized in `job_visibility.py`, future routes can opt in consistently.
- Existing source-delete visibility must continue to work; tests should cover composition of deleted-source filtering and rejected-status filtering.
- Stale browser pages may show a job until refresh after its classification changes to rejected; this matches product acceptance requiring refresh/reload after persistence.

## Dependencies and Constraints

- Depends on existing `latest_bucket` denormalization staying synchronized with current `JobDecision` records.
- No durable frontend state-management layer exists; this is server-rendered Jinja plus JSON routes.
- No current pagination implementation exists for `/jobs`.
- Existing source-delete cleanup has its own visibility rules that must not be regressed.

## Assumptions

- `latest_bucket` is the canonical display status for current list surfaces.
- Main job openings display means `GET /jobs` and Dashboard actionable job summaries/previews.
- Null/missing classification should remain visible by default to preserve current behavior and avoid hiding unclassified jobs.
- Direct rejected job detail URLs remain accessible if otherwise source-visible.
- API clients can tolerate `bucket=rejected` returning an empty list instead of a validation error.

## Risks / Open Questions

- Product may prefer strict inclusion of only `matched` and `review`, which would hide null/unknown statuses. Confirm before implementation if possible.
- Dashboard JSON currently exposes `rejected_count`; returning `0` preserves shape but may confuse clients that expected inventory counts.
- Tracking/reminders may still surface rejected jobs outside the main Jobs display if they are tracked. Confirm whether those surfaces should also become actionable-only.
- Duplicate template directories (`app/templates` and `app/web/templates`) can drift; downstream implementation should verify which path is active and update both if necessary.

## Implementation Notes for Downstream Agents

Suggested implementation sequence:

1. Add main-display predicate/helper functions in `app/domain/job_visibility.py` and unit-test them with matched, review, rejected, null, unknown, and deleted-source fixtures.
2. Update `build_jobs_query()` in `app/web/routes.py` to use the new main-display helper as the base query.
3. Update `dashboard()` to load jobs from the new main-display helper before summary counts and preview cards are calculated.
4. Keep `get_job()`, `keep_job()`, and `update_tracking_status()` on existing `apply_visible_jobs()` to preserve direct-detail behavior.
5. Update Jobs list templates to remove the rejected bucket option.
6. Add/adjust integration tests:
   - `/jobs` JSON excludes rejected and includes matched/review/null.
   - `/jobs?bucket=rejected` returns no jobs.
   - Search matching only a rejected job returns no jobs/no-results HTML.
   - Dashboard counts/cards exclude rejected; `rejected_count` remains `0` if field retained.
   - Reclassified job with `latest_bucket` changed to `rejected` disappears after refresh.
   - Reclassified job changed from `rejected` to `review`/`matched` reappears.
   - Source-delete retained matched active job remains visible; source-visible rejected job is hidden from main display.
7. Run existing source-delete cleanup tests to ensure composed visibility does not break retained matched active behavior.

Test implications:

- Fixtures that ingest/classify jobs as rejected and then assume `/jobs` returns the first created job must be updated to use matched/review data.
- HTML tests should assert the rejected option is absent from the main Jobs bucket selector.
- No migration tests are required.
