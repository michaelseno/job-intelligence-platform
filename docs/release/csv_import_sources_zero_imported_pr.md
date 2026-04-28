# Pull Request

## 1. Feature Name
csv_import_sources_zero_imported

## 2. Summary
Fixes the CSV source import path so user-provided source CSVs with title-cased source types import correctly, duplicate re-uploads are skipped, malformed rows are reported, and the active Sources UI shows actionable import results instead of a misleading `0 imported` message.

## 3. Related Documents
- Product Spec: docs/product/job_intelligence_platform_mvp_product_spec.md
- Technical Design: docs/architecture/job_intelligence_platform_mvp_architecture.md
- Bug Report: docs/bugs/csv_import_sources_zero_imported_bug_report.md
- Backend Report: docs/backend/csv_import_sources_zero_imported_implementation_report.md
- Frontend Report: docs/frontend/csv_import_sources_zero_imported_implementation_report.md
- QA Report: docs/qa/csv_import_sources_zero_imported_test_report.md
- QA Test Plan: docs/qa/csv_import_sources_zero_imported_test_plan.md

## 4. Changes Included
- Normalizes CSV `source_type` values such as `Greenhouse` and `Lever` before backend validation.
- Preserves duplicate detection for repeated imports after normalization.
- Reports malformed CSV rows with unexpected extra fields and guidance to quote values containing commas.
- Updates the active Sources import UI to render created, skipped duplicate, invalid counts, and row-level messages.
- Adds focused API and UI regression coverage for the CSV import bug.
- Adds bug, QA, and release traceability documents for the issue.

## 5. QA Status
- Approved: YES
- QA gate: [QA SIGN-OFF APPROVED]
- HITL gate: HITL validation successful

## 6. Test Coverage
- `PYTHONPATH=. uv run pytest tests/api/test_csv_import_sources_zero_imported.py -q` passed.
- `PYTHONPATH=. uv run pytest tests/ui/test_csv_import_sources_zero_imported_ui.py -q` passed.
- `PYTHONPATH=. uv run pytest tests/integration/test_api_flow.py tests/integration/test_html_views.py -q` passed.
- Full `PYTHONPATH=. uv run pytest -q` completed with 88 passed and 2 unrelated non-blocking UI test-data failures.
- User acceptance evidence: provided CSV imported 46 rows and flagged 1 malformed row; corrected CSV imported 47 rows; corrected re-upload skipped 47 duplicates.

## 7. Risks / Notes
- The original CSV contains one malformed row caused by an unquoted value containing commas. Quote values containing commas to import all 47 rows.
- Known non-blocking failures remain in `tests/ui/test_saas_dashboard_ui_revamp.py::test_job_detail_renders_html_detail_view` and `tests/ui/test_saas_dashboard_ui_revamp.py::test_source_detail_renders_html_detail_view`; both are unrelated seeded-data assumptions where the page/database had no records to link.
- No force-push or hook bypass is used for this release.

## 8. Linked Issue
- Closes #12
