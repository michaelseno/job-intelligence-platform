# Implementation Plan

## 1. Feature Overview
Fix the backend CSV source import path so valid source rows using common CSV enum casing import successfully and invalid CSV rows return actionable row-level validation results.

## 2. Technical Scope
- Normalize CSV string fields during source import before validation.
- Normalize `source_type` casing for common enum values while preserving existing lowercase behavior.
- Detect malformed rows with extra CSV fields and return row-level invalid results.
- Preserve existing duplicate-skip import behavior.
- Add backend integration test coverage for title-cased source types, duplicate skips, malformed row errors, and the user's CSV column shape.

## 3. Source Inputs
- `docs/bugs/csv_import_sources_zero_imported_bug_report.md`
- `docs/product/job_intelligence_platform_mvp_product_spec.md` CSV import assumptions and acceptance criteria
- Existing backend implementation in `app/domain/sources.py`
- Existing API test conventions in `tests/integration/test_api_flow.py`

## 4. API Contracts Affected
Endpoint: `POST /sources/import`

- Request: multipart upload with `file` CSV, unchanged.
- Response: existing `SourceImportResponse` contract unchanged: `created`, `skipped_duplicate`, `invalid`, `rows`.
- Row-level statuses remain `created`, `skipped_duplicate`, and `invalid`.
- HTTP success status remains `200` for mixed valid/invalid CSV imports.

## 5. Data Models / Storage Affected
No data model or storage schema changes.

Imported sources will continue to persist to the existing `Source` model using normalized/cleaned values already used by source creation.

## 6. Files Expected to Change
- `app/domain/sources.py`
- `tests/integration/test_api_flow.py`
- `docs/backend/csv_import_sources_zero_imported_implementation_plan.md`
- `docs/backend/csv_import_sources_zero_imported_implementation_report.md`

## 7. Security / Authorization Considerations
No authentication or authorization behavior changes are in scope. Uploaded CSV values remain validated by existing source validation before persistence. Error messages will be row-specific and must not expose stack traces for expected malformed CSV rows.

## 8. Dependencies / Constraints
No new dependencies. Use Python standard library `csv.DictReader` and existing validation/service patterns.

## 9. Assumptions
- CSV imports may accept common whitespace/casing variants for `source_type` by normalizing with `strip().lower()` before validation.
- Rows with extra CSV fields from unquoted delimiters are considered malformed and should be returned as row-level invalid results instead of silently truncating or importing partial data.

## 10. Validation Plan
- Run targeted integration tests: `pytest tests/integration/test_api_flow.py -q`.
- Run broader test suite if targeted tests pass and runtime is reasonable: `pytest -q`.
