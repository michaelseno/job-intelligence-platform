# Product Specification

## 1. Feature Overview
Add source management actions that let the user modify an existing source and delete a source from active configuration.

Today the product supports source creation, CSV import, source listing, source detail, and manual ingestion runs, but it does not provide a way to correct source configuration mistakes or remove unwanted sources after creation.

This feature adds:
- edit/update for existing sources
- delete for existing sources
- user-visible safeguards for validation and destructive actions

## 2. Problem Statement
Users can currently add sources but cannot maintain them after creation. This causes several problems:
- a mistyped URL, identifier, or company name requires manual database intervention instead of a normal product workflow
- a source added by mistake cannot be removed from the configured sources list
- users cannot intentionally retire stale or unwanted sources through the UI/API

This matters because source configuration is the entry point for ingestion. If source records cannot be corrected or removed, the product creates avoidable friction, clutter, and operational risk.

## 3. User Persona / Target User
- Primary user: the single-user job seeker operating the app locally/self-hosted
- Secondary operational mindset: the same user acting as their own lightweight admin for source setup and maintenance

## 4. User Stories
- As a job seeker, I want to edit a source's configuration, so that I can fix incorrect source metadata without recreating the source.
- As a job seeker, I want to update whether a source is active, so that I can stop using a source without deleting historical data unintentionally.
- As a job seeker, I want to delete a source I no longer want, so that the configured source list stays accurate and uncluttered.
- As a job seeker, I want clear warnings before deleting a source, so that I understand the impact of the action.
- As a job seeker, I want invalid source edits to be rejected with clear errors, so that I do not save a broken configuration.

## 5. Goals / Success Criteria
- A user can open an existing source and successfully update editable fields through the product.
- A user can delete an existing source through the product without manual database work.
- Source update validation remains consistent with source creation validation.
- Duplicate source configurations are prevented on update as well as on create.
- Deletion flow includes explicit confirmation and impact messaging.
- Default Sources views no longer show deleted sources.

## 6. Feature Scope
### In Scope
- Add edit capability for existing sources in HTML and JSON/API product surfaces.
- Add delete capability for existing sources in HTML and JSON/API product surfaces.
- Reuse create-time validation rules during update.
- Recompute duplicate detection when edit changes dedupe-relevant fields.
- Allow the user to modify at minimum:
  - name
  - source_type
  - company_name
  - base_url
  - external_identifier
  - adapter_key
  - notes
  - is_active
- Provide edit entry points from:
  - configured sources list
  - source detail page
- Provide delete entry points from:
  - configured sources list
  - source detail page
- Provide confirmation UX before deletion.
- Exclude deleted sources from default configured source lists and source filter dropdowns.
- Preserve existing create/import/run workflows unless directly affected by this feature.

### Out of Scope
- Bulk edit or bulk delete of sources.
- Undo/restore of a deleted source in this feature pass.
- Editing sources via CSV import.
- Changes to source ingestion logic beyond what is required to respect updated/deleted source state.
- New adapter families or expanded adapter support.
- Reworking overall source health or run history UX beyond what is required for edit/delete flows.

## 7. Functional Requirements
1. The system must provide an edit action for each non-deleted source.
2. The system must display the current source values in the edit experience.
3. The system must validate edited source data using the same field rules as source creation.
4. The system must reject edits that would make the source a duplicate of another existing non-deleted source.
5. The system must persist successful source edits and make updated values visible immediately after save.
6. The system must allow `is_active` to be changed independently of other fields.
7. The system must provide a delete action for each non-deleted source.
8. The system must require explicit user confirmation before deletion is finalized.
9. The delete confirmation must show an impact summary before confirm, including at minimum:
   - source name
   - whether the source has run history
   - whether jobs are currently linked to the source
10. Deleting a source must remove it from normal source management views and from future ingestion eligibility.
11. Deleting a source must not silently break jobs, tracking history, or historical provenance views.
12. If the product preserves historical data for deleted sources, deleted records must be clearly represented as deleted and must not be editable or runnable afterward.
13. If a user requests edit, detail, run, or delete on a source that does not exist, the system must return a not-found response.
14. If a user attempts to edit or delete a source that is already deleted, the system must return a clear not-allowed or not-found outcome; the behavior must be consistent across HTML and JSON surfaces.
15. CSV import behavior remains create-only; it must not update existing sources.

## 8. Acceptance Criteria
- AC-01: From the configured sources list, each active/non-deleted source shows an Edit action and a Delete action.
- AC-02: From the source detail page, the user can access edit and delete actions for that source.
- AC-03: Opening edit for a source shows the source's current saved values for all editable fields.
- AC-04: Saving a valid edit updates the source and returns the user to a success state with the new values visible.
- AC-05: Editing a source to an invalid configuration returns field-level and/or page-level validation errors and does not persist any partial change.
- AC-06: Editing a source so that its dedupe identity matches another existing source is rejected with a duplicate error.
- AC-07: Updating only `notes` or `is_active` succeeds without requiring unrelated fields to change.
- AC-08: After `is_active` is changed to false, the source remains visible in source management with its inactive state clearly shown and is not treated as deleted.
- AC-09: Clicking Delete does not immediately remove the source; the user must complete a confirmation step.
- AC-10: The delete confirmation explicitly identifies the source being deleted and warns when the source has run history and/or linked jobs.
- AC-11: After deletion is confirmed, the source no longer appears in the default configured sources list.
- AC-12: After deletion is confirmed, the source no longer appears as an available source in jobs filtering or other source selection controls used for future actions.
- AC-13: After deletion is confirmed, the source cannot be run again for ingestion.
- AC-14: After deletion is confirmed, the system continues to behave safely for previously ingested jobs and historical records; no user-facing page should fail because the source was deleted.
- AC-15: Requesting edit, delete, or run for a nonexistent source returns a not-found response.
- AC-16: CSV import still creates new sources and skips duplicates; it does not update an existing source.

## 9. Edge Cases
- User edits a source without changing dedupe fields; update should succeed if otherwise valid.
- User edits a source and changes dedupe fields to match another source.
- User changes source type and causes previously optional/required fields to change validation status.
- User deletes a source that has never been run.
- User deletes a source that has run history but no linked jobs.
- User deletes a source that has linked jobs.
- User deletes a source that is inactive.
- User opens an edit form while another process changes the same source before save.
- User refreshes or resubmits a successful edit/delete request.
- User attempts to run ingestion from a stale page after the source was deleted.
- Existing jobs/tracking pages reference a source that has since been deleted.

## 10. Constraints
- Technical constraints:
  - The current product already has source creation, CSV import, detail, and run flows; this feature must extend that model rather than replace it.
  - Current source validation and duplicate detection are based on source type, base URL, external identifier, and adapter key; update behavior must remain compatible with that logic.
  - The product currently distinguishes active vs inactive sources with `is_active`; deletion must remain distinct from deactivation.
- UX constraints:
  - Destructive actions must be explicit and require confirmation.
  - Edit and delete actions must be easy to find from the primary source management surfaces.
  - Validation copy must be human-readable and specific to the failing condition.
- Business rules:
  - Greenhouse and Lever remain the supported first-class adapters.
  - `common_pattern` and `custom_adapter` remain visible but explicitly unsupported unless existing backend rules allow them.
  - CSV import remains create-only in this pass.

## 11. Dependencies
- SourceService/domain validation logic
- Source list/detail web routes and templates
- Source persistence model and any migration needed to represent deleted state safely
- Jobs/source filter views that currently read available sources
- Run/source health flows that must respect updated/deleted source state
- QA coverage for source create/edit/delete/regression behavior

## 12. Assumptions
- Assumption A1: “Delete source” should be implemented as a user-facing delete that removes the source from active configuration, not as an unsafe hard delete that can orphan historical job or tracking data.
- Assumption A2: Because jobs, source links, and run history already depend on sources, architecture may satisfy delete via soft delete/tombstone or an equivalent safe data-retention strategy.
- Assumption A3: Inactive and deleted are separate states with different intent:
  - inactive = keep record, stop/avoid normal use, user can still manage it
  - deleted = remove from normal management lists and future use
- Assumption A4: Editing source configuration is allowed for all existing non-deleted sources, including changing source type, as long as the updated configuration passes current validation rules.
- Assumption A5: HTML flows should follow existing server-rendered patterns: server-side validation, PRG on success where practical, and user-visible success/error messaging.

## 13. Open Questions
- OQ-01: After deletion, should a dedicated deleted-source detail page remain accessible for historical reference, or should deleted sources become fully inaccessible outside historical job context?
- OQ-02: What exact user-facing impact counts should be shown in delete confirmation (for example: run count, linked job count, tracked job count)?
- OQ-03: Should deleting a source with linked tracked jobs be allowed without additional warning, or should tracked-job presence require stronger confirmation copy?
- OQ-04: Should source edit use a dedicated page, inline form on detail, modal, or reuse the existing source hub form pattern in edit mode?
- OQ-05: For JSON/API surfaces, should delete return the deleted record, a status-only payload, or no body?
