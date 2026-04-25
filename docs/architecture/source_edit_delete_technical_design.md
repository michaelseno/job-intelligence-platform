# Source Edit/Delete Technical Design

## Feature Overview
Add implementation-ready source maintenance flows that let a user update an existing source and safely delete a source from active configuration without breaking historical jobs, source links, or run history.

This design extends the current FastAPI + Jinja source management flow in `app/domain/sources.py`, `app/web/routes.py`, and the existing source templates.

## Product Requirements Summary
- Users must be able to edit all existing non-deleted sources.
- Users must be able to delete existing non-deleted sources with explicit confirmation.
- Update validation must match create validation.
- Duplicate detection must apply on update, but only against other non-deleted sources.
- Deleted sources must disappear from normal source management lists, source filter dropdowns, and future ingestion eligibility.
- Historical job/run/provenance views must remain safe after deletion.
- HTML and JSON surfaces must return consistent not-found / not-allowed outcomes.

## Scope

### In Scope
- Source update backend service logic and route handlers.
- Source delete confirmation and soft-delete behavior.
- Source list/detail/edit/delete UI changes.
- JSON API support for update and delete.
- Query filtering so deleted sources are excluded from normal operational views.
- Run-flow protection so deleted sources cannot be ingested again.
- Validation, duplicate handling, error mapping, and regression coverage.

### Out of Scope
- Bulk edit/delete.
- Restore/undelete.
- CSV import updating existing sources.
- Reworking historical job detail UX beyond safe handling of deleted sources.
- Full optimistic concurrency/version conflict workflow.

## Architecture Overview
The feature should remain inside the current modular monolith:

1. **Persistence**: add soft-delete metadata to `sources`.
2. **Domain service**: extend `SourceService` with update, delete, delete-impact summary, and filtered query helpers.
3. **Web layer**: add edit and delete routes for HTML, plus JSON update/delete endpoints on the same resource family.
4. **Templates**: add edit page and delete confirmation page; add action entry points from list/detail.
5. **Cross-feature reads**: exclude deleted sources from source management, jobs filter dropdowns, dashboard source counts, and source health lists, while still allowing historical pages to resolve deleted source names.

Recommended architectural decision: implement deletion as **soft delete / tombstone**, not hard delete.

## System Components

### 1. Source Persistence Model
Current `Source` records are referenced by:
- `source_runs.source_id`
- `job_postings.primary_source_id`
- `job_source_links.source_id`

Because these references are historical system-of-record relationships, hard delete is unsafe.

### 2. SourceService
Extend `SourceService` to own:
- filtering of active management records vs deleted records
- create/update shared validation
- duplicate detection excluding current record on update
- delete impact summary calculation
- soft delete state transitions

### 3. Web Routes
Add server-rendered routes for:
- edit form display
- edit form submit
- delete confirmation display
- delete confirm submit

Add JSON routes for:
- source update
- source delete

### 4. Template Layer
Add clear edit/delete affordances to:
- configured sources list
- source detail page

Add separate views for:
- edit form
- delete confirmation

## Data Models and Storage Design

### Source Table Changes
Add nullable tombstone metadata to `sources`:
- `deleted_at timestamptz null`

Optional but not required for this feature pass:
- `deletion_note text null`

For MVP simplicity, `deleted_at` is sufficient.

### Why `deleted_at` Instead of Hard Delete or `is_deleted`
- preserves foreign key integrity and historical joins
- allows clear “deleted vs active” filtering
- supports future restore/audit work if needed
- avoids introducing redundant boolean + timestamp state

### Dedupe Constraint Change
Current design uses a global unique constraint on `sources.dedupe_key`. That conflicts with the product requirement that duplicate checks only consider non-deleted sources.

Refinement to product assumptions:
- replace the unconditional unique constraint with a **partial unique index on `dedupe_key` where `deleted_at is null`**

Reason for refinement:
- without this change, a soft-deleted source would permanently block recreation of the same source config, which conflicts with delete semantics and the “duplicate of another existing non-deleted source” requirement.

### Read Model Rules
- **Active source**: `deleted_at is null`
- **Deleted source**: `deleted_at is not null`
- **Inactive source**: `deleted_at is null and is_active = false`

Inactive and deleted remain separate states.

### Historical Data Behavior
- `job_postings.primary_source_id` remains unchanged.
- `job_source_links.source_id` remains unchanged.
- `source_runs.source_id` remains unchanged.
- Historical pages may still fetch deleted `Source` rows to display names/metadata, but those rows are not manageable/runnable.

## API Contracts

### Shared Validation Contract
Update should reuse the same field rules as create:
- `name` required
- `base_url` required
- `source_type` must be supported
- `external_identifier` required for `greenhouse` and `lever`
- `adapter_key` required for `common_pattern` and `custom_adapter`
- adapter-specific validation via registry still applies
- duplicate detection uses dedupe key against **other non-deleted sources only**

### HTML Routes

#### `GET /sources/{source_id}/edit`
Returns server-rendered edit form populated with current values.

Behavior:
- 200 for existing non-deleted source
- 404 for nonexistent source
- 404 for deleted source (chosen for consistent “not available in management UI” behavior)

#### `POST /sources/{source_id}/edit`
Processes edit form.

Request body:
- same fields as source create form

Responses:
- 303 redirect to `/sources/{id}` with success message on success
- 400 with same edit template and field errors on validation failure
- 404 for nonexistent/deleted source

#### `GET /sources/{source_id}/delete`
Displays confirmation page with impact summary.

Response model for template context:
- `source`
- `impact_summary.run_count`
- `impact_summary.linked_job_count`
- `impact_summary.tracked_job_count`
- `impact_summary.has_run_history`
- `impact_summary.has_linked_jobs`

Responses:
- 200 for existing non-deleted source
- 404 for nonexistent/deleted source

#### `POST /sources/{source_id}/delete`
Finalizes soft delete.

Responses:
- 303 redirect to `/sources` with success message on success
- 404 for nonexistent/deleted source

Idempotency decision:
- second delete request after success returns 404 because the record is no longer available in the management surface

### JSON Routes

#### `PATCH /sources/{source_id}`
Partial update for API clients.

Request body fields allowed:
- `name`
- `source_type`
- `company_name`
- `base_url`
- `external_identifier`
- `adapter_key`
- `notes`
- `is_active`

Implementation note:
- accept partial payloads, merge onto existing source, then run full validation on the merged result.

Success response: `200 OK`

```json
{
  "source": {
    "id": 123,
    "name": "Acme Greenhouse",
    "source_type": "greenhouse",
    "company_name": "Acme",
    "base_url": "https://boards.greenhouse.io/acme",
    "external_identifier": "acme",
    "adapter_key": null,
    "notes": "Updated note",
    "is_active": false,
    "deleted_at": null,
    "last_run_at": "2026-04-24T12:00:00Z",
    "last_run_status": "success",
    "last_jobs_fetched_count": 12,
    "consecutive_empty_runs": 0,
    "health_state": "healthy",
    "health_message": "Recent ingestion completed successfully."
  }
}
```

Error responses:
- `404` source not found / deleted
- `400` validation failure

Recommended validation payload:

```json
{
  "detail": {
    "message": "Source update failed.",
    "errors": {
      "external_identifier": ["external_identifier is required for greenhouse and lever sources."],
      "__all__": ["Duplicate source already exists."]
    }
  }
}
```

#### `GET /sources/{source_id}/delete-impact`
Optional JSON helper endpoint for clients that want confirmation metadata before delete.

Response:

```json
{
  "source_id": 123,
  "source_name": "Acme Greenhouse",
  "run_count": 4,
  "linked_job_count": 27,
  "tracked_job_count": 8,
  "has_run_history": true,
  "has_linked_jobs": true
}
```

If the frontend remains fully server-rendered for confirmation, this endpoint can still be implemented for API completeness.

#### `DELETE /sources/{source_id}`
Soft deletes the source.

Success response: `200 OK`

```json
{
  "deleted": true,
  "source_id": 123,
  "deleted_at": "2026-04-24T12:34:56Z"
}
```

Error responses:
- `404` source not found / deleted

## Frontend / Client Impact

### Sources List Page (`sources/index.html`)
Add per-row actions:
- `Edit`
- `Delete`
- existing `Run ingestion`

UI rules:
- deleted sources are not listed
- inactive sources remain listed and visibly marked as inactive
- delete action routes to confirmation page, never immediate delete

Recommended display additions:
- status badge or subtitle showing `Active` / `Inactive`

### Source Detail Page (`sources/detail.html`)
Add action row:
- `Edit source`
- `Delete source`
- `Run ingestion`

UI rules:
- deleted sources are not accessible here via normal route
- inactive sources remain viewable/editable

### Edit Page
Add new template, likely `sources/edit.html`.

Behavior:
- reuse current source create fields and validation display pattern
- submit button label becomes `Save changes`
- cancel link returns to source detail
- surface page-level duplicate/adapter validation errors

### Delete Confirmation Page
Add new template, likely `sources/delete_confirm.html`.

Required content:
- source name
- warning that deletion removes source from active configuration and future ingestion
- whether run history exists
- whether linked jobs exist
- optional counts for runs / linked jobs / tracked jobs

Buttons:
- destructive confirm button
- cancel link back to source detail

### Jobs and Other Source Selectors
Update source dropdowns and selectors to exclude deleted sources. This includes at minimum:
- jobs list source filter
- any future source selection controls for user-triggered actions

Historical job cards/details may still show deleted source names via existing direct joins/lookups.

## Backend Logic / Service Behavior

### SourceService Additions
Recommended methods:
- `list_sources(include_deleted: bool = False)`
- `get_source(source_id: int, include_deleted: bool = False)`
- `build_update_payload(source, patch_data)`
- `validate(payload, exclude_source_id: int | None = None)`
- `update_source(source_id, payload_or_patch)`
- `get_delete_impact(source_id)`
- `delete_source(source_id)`

### Filtering Rules
Default service/query methods used by management UI should filter `deleted_at is null`.

Historical read paths should explicitly opt into `include_deleted=True` or continue using direct queries where historical rendering is required.

### Update Algorithm
1. Fetch non-deleted source.
2. Merge incoming values with existing persisted values.
3. Normalize text inputs using existing helpers.
4. Recompute dedupe key.
5. Validate merged payload.
6. Check duplicates against non-deleted rows excluding current source id.
7. Persist updates atomically.
8. Return updated source.

### Delete Algorithm
1. Fetch non-deleted source.
2. Calculate impact summary for confirmation or logging.
3. Set `deleted_at = utcnow()`.
4. Keep `is_active` unchanged or optionally force `is_active = false`.

Recommended choice: **force `is_active = false` during delete**.

Reason:
- keeps state semantically aligned
- protects any existing code paths that still check only `is_active`
- reduces chance of accidental future ingestion by incomplete filtering

5. Commit transaction.
6. Return deleted timestamp / confirmation result.

### Delete Impact Summary Queries
Compute:
- `run_count`: count of `SourceRun` rows for source
- `linked_job_count`: distinct count of `JobSourceLink.job_posting_id` for source
- `tracked_job_count`: distinct count of linked jobs with `JobPosting.tracking_status is not null`

The product spec requires booleans at minimum; counts provide better confirmation messaging and QA observability with minimal extra complexity.

### Run Protection
Update manual run route and orchestrator entry checks:
- deleted source -> `404`
- inactive source -> `409` (or `400`) with clear message such as `Source is inactive and cannot be run.`

Recommended choice: `409 Conflict` for inactive run attempts.

### Historical Rendering Rules
- jobs list/detail should continue to resolve deleted source names where linked
- if a source lookup fails entirely, existing fallback strings remain acceptable
- deleted source should never expose edit/delete/run actions in historical contexts

### Concurrency Decision
Refinement: use **last-write-wins** for MVP update behavior.

Reason:
- current application has no versioned write pattern
- product spec mentions concurrent edits as an edge case but does not require conflict detection
- adding optimistic locking would materially expand scope

Documented limitation:
- a stale edit form can overwrite more recent changes

## File / Module Structure

### Existing Files to Update
- `app/persistence/models.py`
- `app/schemas.py`
- `app/domain/sources.py`
- `app/domain/operations.py`
- `app/domain/ingestion.py`
- `app/web/routes.py`
- `app/web/templates/sources/index.html`
- `app/web/templates/sources/detail.html`
- `app/web/templates/jobs/list.html` (indirectly through context filtering only, likely no template change required)
- `tests/unit/test_sources.py`
- route/integration test files for source CRUD flows
- new Alembic migration under `alembic/versions/`

### New Files Expected
- `app/web/templates/sources/edit.html`
- `app/web/templates/sources/delete_confirm.html`
- additional test module if current suite separates route tests from unit tests

## Security and Access Control
- The app is single-user/local with no auth in MVP; no new auth layer is introduced.
- Treat delete as destructive but allowed to the current user.
- Do not expose deleted sources in normal listing endpoints by default.
- Continue server-side validation for all HTML and JSON writes.
- Escape/encode validation errors and notes content using existing template safety defaults.

## Reliability / Operational Considerations
- Soft delete avoids referential breakage and preserves provenance.
- Forcing `is_active = false` on delete adds defense in depth.
- Partial unique index protects against race conditions better than app-only duplicate checks.
- HTML actions should follow PRG to reduce duplicate form resubmission side effects.
- Second delete submission after successful redirect should safely resolve as not found.
- Source health/ops pages should exclude deleted sources from default operational counts.

## Dependencies and Constraints
- Current source validation logic in `SourceService.validate`
- Adapter registry validation behavior
- Existing server-rendered source form conventions
- Existing route structure using shared HTML/JSON endpoints
- Alembic migration support for schema/index changes
- SQLite test setup must remain compatible with updated model metadata/index definitions

## Assumptions
- Deletion is a soft delete implemented via `deleted_at`.
- Deleted sources are inaccessible from normal source management routes after deletion.
- Historical pages may still show deleted source names/details pulled from linked records.
- Update API supports partial JSON patches but the HTML form posts full field values.
- Inactive sources remain editable and visible in source management.
- Inactive sources should not be runnable for ingestion going forward.

## Risks / Open Questions
- **Schema migration risk**: converting from unique constraint to partial unique index must be handled carefully in Alembic and validated against existing data.
- **UI consistency risk**: if any source list/query path is missed, deleted sources may still appear in filters or dashboards.
- **Historical wording risk**: pages that show a deleted source may need subtle copy/badge later if product wants explicit deleted labeling in historical views.
- **API consistency question**: if the team wants to avoid introducing `PATCH`, a full `PUT` contract is also workable, but `PATCH` better supports `notes`/`is_active` only updates.
- **Concurrency limitation**: stale edit submissions can overwrite recent changes.
- **Unsupported adapter edits**: changing `source_type` may surface new validation failures for previously valid records; this is intended and should be clearly messaged.

## Implementation Notes for Downstream Agents

### Backend Agent
- Add `deleted_at` to `Source` model and migration.
- Replace global dedupe uniqueness with partial unique index on non-deleted rows.
- Extend `SourceService.validate` to accept `exclude_source_id` and ignore deleted records.
- Implement source update, delete, and impact-summary methods.
- Ensure default source queries exclude deleted rows.
- Update run route/service to reject deleted and inactive sources.
- Extend `SourceResponse` and add any helper schemas needed for update/delete responses.
- Add route/integration tests for create/update/delete/regression cases.

### Frontend Agent
- Add edit/delete links on source list and detail pages.
- Build server-rendered edit page using existing form style and error presentation.
- Build delete confirmation page with impact summary and destructive CTA.
- Show inactive state clearly in list/detail pages.
- Preserve CSV import messaging that import remains create-only.

### QA Agent
- Verify edit from list and detail entry points.
- Verify valid edit, invalid edit, duplicate edit, and type-change validation cases.
- Verify `notes`-only and `is_active`-only updates.
- Verify delete confirmation content for sources with and without runs/jobs.
- Verify deleted sources disappear from sources list, jobs source filter, and run eligibility.
- Verify deleted sources do not break job detail, run history, or provenance rendering.
- Verify repeated delete/edit/run requests on deleted source return consistent not-found behavior.
- Verify inactive sources remain visible/manageable but cannot be run.
