# Pull Request

## 1. Feature Name
Source edit/delete management

## 2. Summary
Adds source edit and delete workflows across the HTML and JSON surfaces so users can correct source configuration, deactivate sources safely, and remove deleted sources from operational views without breaking historical records.

Also includes the `sources.deleted_at` migration regression fix so the soft-delete schema change applies safely on PostgreSQL-backed environments and keeps source-health flows working after migration.

Closes #1

## 3. Related Documents
- Product Spec: `docs/product/source_edit_delete_product_spec.md`
- Technical Design: `docs/architecture/source_edit_delete_technical_design.md`
- UI/UX Spec: `docs/uiux/source_edit_delete_design_spec.md`
- QA Report: `docs/qa/source_edit_delete_test_report.md`
- QA Release Sign-Off: `docs/qa/source_edit_delete_release_signoff.md`
- Migration Bug Report: `docs/bugs/source-health-deleted-at-schema-mismatch_bug_report.md`
- Migration QA Report: `docs/qa/source_health_deleted_at_schema_mismatch_test_report.md`

## 4. Changes Included
- add soft-delete-aware source update, delete-impact, and delete endpoints plus inactive-run protection
- add server-rendered edit/delete pages, list/detail actions, and active/inactive status messaging
- exclude deleted sources from operational source lists, filters, dashboard/source-health reads, and active dedupe checks
- add Alembic migration support for `deleted_at` plus active-only dedupe uniqueness without recreating `sources` on PostgreSQL
- add automated regression and QA coverage for source edit/delete flows, historical safety, and migration behavior

## 5. QA Status
- Approved: YES

## 6. Test Coverage
- Full repository suite: `".venv/bin/python" -m pytest` → `25 passed in 1.49s`
- Focused source edit/delete QA suites for API, HTML, UI, and service behavior
- Migration regression coverage for Alembic upgrade behavior, active-only uniqueness, and PostgreSQL validation evidence

## 7. Risks / Notes
- Existing non-scope `/dashboard` non-HTML response behavior remains documented outside this release scope.
- PR intentionally excludes unrelated stray files present in the working tree, including `app/web/routes 2.py`.
