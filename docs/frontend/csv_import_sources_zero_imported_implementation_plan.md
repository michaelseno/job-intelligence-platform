# Implementation Plan

## 1. Feature Overview
Fix the active Sources CSV import result UI so HTML imports report the backend `SourceImportResponse` accurately and expose row-level validation feedback.

## 2. Technical Scope
- Update `app/templates/sources/index.html`, which is the active `sources/index.html` template.
- Render `created`, `skipped_duplicate`, `invalid`, and `rows` from the backend response contract.
- Use warning/error styling when validation errors prevent imports instead of showing a success-only `0 imported` message.
- Add HTML rendering coverage for created, skipped duplicate, and invalid row results.

## 3. UI/UX Inputs
- Bug report: `docs/bugs/csv_import_sources_zero_imported_bug_report.md`.
- Backend report: `docs/backend/csv_import_sources_zero_imported_implementation_report.md`.
- Existing template conventions in `app/templates/sources/index.html` and `app/templates/macros/ui.html`.

## 4. Files Expected to Change
- `app/templates/sources/index.html`
- `tests/integration/test_html_views.py`
- `docs/frontend/csv_import_sources_zero_imported_implementation_plan.md`
- `docs/frontend/csv_import_sources_zero_imported_implementation_report.md`

## 5. Dependencies / Constraints
- Backend contract remains unchanged: `created`, `skipped_duplicate`, `invalid`, `rows`.
- Do not modify backend logic unless a contract defect is found.
- Keep markup accessible with semantic headings, table headers, live/status alert roles, and visible row messages.

## 6. Assumptions
- The active template should remain under `app/templates/` because route template search order prioritizes that directory.
- Row-level import details can be shown in a compact table within the existing import panel.

## 7. Validation Plan
- Run targeted HTML integration tests for CSV import rendering.
- Run the existing import/API integration test file.
- Run the full test suite if available and report any unrelated failures.
