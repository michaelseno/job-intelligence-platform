# Planning Issue

## Feature Name
Source Edit/Delete Management

## Problem Summary
The product supports source creation, import, listing, detail, and manual ingestion runs, but it does not yet let users correct source configuration mistakes or remove unwanted sources after creation. This creates operational friction, leaves stale or incorrect sources in active configuration, and forces manual intervention for maintenance tasks that should be available in the normal product workflow.

## Linked Planning Documents
- Product Spec: `docs/product/source_edit_delete_product_spec.md`
- Technical Design: `docs/architecture/source_edit_delete_technical_design.md`
- UI/UX Spec: `docs/uiux/source_edit_delete_design_spec.md`
- QA Plan: `docs/qa/source_edit_delete_test_plan.md`

## Scope Summary
- Add source edit capability for existing non-deleted sources in both HTML and JSON surfaces.
- Add source delete capability with explicit confirmation and impact messaging.
- Preserve validation parity with source creation, including duplicate detection during updates.
- Keep inactive and deleted as separate states, with deleted sources removed from normal management and future ingestion flows.
- Protect historical jobs, source links, and run history from breakage after deletion.
- Add list/detail entry points, dedicated edit and delete pages, and regression coverage for source-adjacent workflows.

## Implementation Notes
- Implement delete as soft delete using `deleted_at`, not hard delete, to preserve historical foreign-key relationships.
- Replace the unconditional dedupe uniqueness behavior with a partial unique index on `dedupe_key` where `deleted_at is null` so deleted sources do not block recreation.
- Extend `SourceService` to own update validation, duplicate checks excluding the current or deleted records, delete-impact summary generation, and delete state transitions.
- Add HTML routes for edit and delete confirmation, plus JSON `PATCH` and `DELETE` support for the same resource family.
- Update source management, jobs filters, source health, and run eligibility queries so deleted sources are excluded from operational views while historical pages can still resolve deleted source references.
- Keep the UX server-rendered and HTML-first with dedicated edit and delete pages that follow existing validation, PRG, and messaging patterns.

## QA Section
- QA Planning Document: `docs/qa/source_edit_delete_test_plan.md`
- Current Status: Planning artifact available; implementation testing not yet executed.
- Required QA focus areas:
  - edit/delete action availability from list and detail surfaces
  - validation parity with source creation and duplicate rejection on update
  - inactive versus deleted state handling and run eligibility rules
  - delete confirmation impact summary and stale request behavior
  - deleted-source filtering across source lists, selectors, dashboards, and run flows
  - historical safety for jobs, provenance, and run history after source deletion
  - CSV import regression to ensure it remains create-only

## Risks / Open Questions
- Query-path leakage risk: deleted sources may still appear in one or more operational views if filtering is not applied consistently.
- Historical safety risk: jobs, source links, or run history may fail or degrade if deleted-source joins are not handled deliberately.
- Validation parity risk: update behavior may diverge from create rules for type-specific requirements or duplicate handling.
- UX decision still needs firm implementation alignment on whether inactive sources hide or disable the run action in HTML surfaces.
- Product/design clarification may still be needed on deleted-source historical accessibility, exact delete-impact counts shown to the user, and JSON delete response shape.

## Current Planning Defaults
- Edit uses a dedicated page with prefilled values and server-side validation.
- Delete uses a dedicated confirmation page with impact summary and explicit destructive confirmation.
- Deleted sources are soft-deleted, excluded from normal management routes, and treated as unavailable for future ingestion.
- Nonexistent and deleted sources return a consistent not-found / unavailable outcome across HTML and JSON surfaces.
- CSV import remains create-only and must not update existing sources.
- Inactive and deleted remain distinct states; inactive sources stay manageable while deleted sources do not.

## Definition of Done
- Planning documents are linked and implementation intent is consolidated into a single planning issue artifact.
- Product, architecture, UX, and QA expectations are aligned around safe source update and delete behavior.
- Key implementation constraints, risks, and defaults are explicit for downstream implementation agents.
- A repository planning issue is documented for tracking, even if GitHub issue creation is not possible from the current repository configuration.
- No code changes, push actions, PR creation, or release actions are included in this planning issue.
