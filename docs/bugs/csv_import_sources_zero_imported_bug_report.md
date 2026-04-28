# Bug Report

## 1. Summary
CSV upload from the Sources UI reports `0 imported` for `/Users/mjseno/Downloads/job_board.csv` with no backend error. The provided CSV uses the documented header names and has unique rows, but all `source_type` values are title-cased (`Greenhouse`, `Lever`) while backend validation only accepts lowercase (`greenhouse`, `lever`). The active UI template also hides row-level invalid results and reads a non-existent result field, so invalid imports are surfaced as a misleading success-style `0 imported` message.

## 2. Investigation Context
- Source of report: user/HITL-style validation on branch `bugfix/csv_import_sources_zero_imported`.
- Related feature/workflow: Sources page CSV upload, button labeled `Import sources`.
- User action: upload `/Users/mjseno/Downloads/job_board.csv` through the UI Import CSV form.
- Backend endpoint: `POST /sources/import` in `app/web/routes.py`.
- Backend service: `SourceService.import_csv()` in `app/domain/sources.py`.
- Acceptance criterion: valid unique CSV rows import as sources; duplicates are skipped. If the CSV format is invalid, provide/fix a valid format so it can import.

## 3. Observed Symptoms
- UI/import response says `0 imported`.
- No backend exception or HTTP error was reported.
- Expected behavior: valid unique rows should create source records; duplicate rows should be skipped with row-level status.
- CSV structure inspection:
  - Header: `name, source_type, base_url, external_identifier, adapter_key, company_name, is_active, notes`.
  - Row count: 47 data rows.
  - Source type values: 21 `Greenhouse`, 26 `Lever`.
  - Missing required `name`, `source_type`, `base_url`, or `external_identifier`: 0 rows.
  - Duplicate normalized source keys: 0 rows.
  - One row has unquoted commas in the notes field, producing extra CSV fields. The current importer ignores extra fields, but the CSV is not strictly valid RFC-style CSV for that row unless the notes value is quoted.

## 4. Evidence Collected
- `docs/product/job_intelligence_platform_mvp_product_spec.md:118-127` documents the baseline CSV columns and row-specific validation requirement.
- `docs/product/job_intelligence_platform_mvp_product_spec.md:129-132` requires valid CSV uploads to create sources and invalid/incomplete input to be flagged clearly.
- `app/domain/sources.py:16` defines accepted source types as lowercase only: `greenhouse`, `lever`, `common_pattern`, `custom_adapter`.
- `app/domain/sources.py:56-57` appends `Unsupported source_type.` when `payload.source_type` is not exactly in `VALID_SOURCE_TYPES`.
- `app/domain/sources.py:191-199` maps CSV row values directly into `SourceCreateRequest`; it does not normalize `source_type` case.
- `app/domain/sources.py:205-213` marks non-duplicate validation failures as `invalid`, so title-cased `Greenhouse`/`Lever` rows become invalid rather than created.
- `app/web/routes.py:586-602` handles `POST /sources/import`, calls `SourceService.import_csv(payload)`, and renders the Sources page for HTML requests.
- `app/web/routes.py:51-54` configures Jinja search order with `app/templates` before `app/web/templates`, so `app/templates/sources/index.html` is the active `sources/index.html` template when both exist.
- `app/templates/sources/index.html:91-95` shows `{% if import_result %}<div class="alert alert--success">Imported {{ import_result.created_count|default(0) }} sources.</div>{% endif %}` and button text `Import sources`.
- `SourceImportResponse` in `app/schemas.py:59-63` exposes `created`, `skipped_duplicate`, `invalid`, and `rows`; it does not expose `created_count`.
- `app/web/templates/sources/index.html:88-107` contains a more complete import summary/table using `import_result.created`, `import_result.skipped_duplicate`, `import_result.invalid`, and row messages, but that template is shadowed by `app/templates/sources/index.html`.
- `tests/integration/test_api_flow.py:95-106` validates API JSON behavior for lowercase `greenhouse` rows, an invalid row, and a duplicate row; it does not cover title-cased source types or the active HTML template behavior.

## 5. Execution Path / Failure Trace
1. User submits the CSV through the Sources UI form in `app/templates/sources/index.html`.
2. `POST /sources/import` reads the uploaded bytes in `app/web/routes.py:586-594`.
3. `SourceService.import_csv()` parses rows with `csv.DictReader` in `app/domain/sources.py:185-199`.
4. For each row, the CSV `source_type` value is passed through unchanged (`Greenhouse` or `Lever`).
5. `SourceService.validate()` checks exact membership in lowercase `VALID_SOURCE_TYPES` at `app/domain/sources.py:56`.
6. Each row fails validation with `Unsupported source_type.` and is counted as invalid, not created.
7. For an HTML request, the route renders `sources/index.html` with `import_result`.
8. Because Jinja searches `app/templates` before `app/web/templates`, the active template is `app/templates/sources/index.html`, which displays `import_result.created_count|default(0)` instead of `import_result.created` and does not display invalid row details. The user sees a misleading `Imported 0 sources.` message rather than actionable validation failures.

## 6. Failure Classification
- Primary classification: Application Bug.
- Contributing classification: Contract Mismatch / CSV format ambiguity.
- Severity: High.

Severity justification: The CSV import workflow fails for a plausible user-provided CSV that otherwise matches the documented column schema and has unique, complete source rows. The UI masks the validation errors, preventing the user from correcting the issue and blocking CSV-based source onboarding.

## 7. Root Cause Analysis
- Immediate failure point: `SourceService.validate()` rejects every row because `source_type` is title-cased in the CSV and backend validation is case-sensitive.
- Underlying root cause: The importer does not normalize or clearly validate CSV enum values before applying the source contract, while the active UI template hides `SourceImportResponse.rows` and displays a wrong/non-existent `created_count` field.
- Supporting evidence:
  - CSV has `source_type` values `Greenhouse` and `Lever` only.
  - Backend accepts only lowercase source types at `app/domain/sources.py:16` and checks exact membership at `app/domain/sources.py:56`.
  - Import mapping uses `row.get("source_type", "")` without `.strip().lower()` at `app/domain/sources.py:193`.
  - Active template uses `created_count`, which is not part of `SourceImportResponse`, at `app/templates/sources/index.html:91`; schema uses `created` at `app/schemas.py:59-63`.

Confidence label: Confirmed Root Cause for title-case `source_type` rejection and misleading UI result display.

## 8. Confidence Level
High.

The CSV schema and source type values were inspected directly, and the backend validation path deterministically rejects title-cased enum values. The active template mismatch is directly evidenced by template search order and the `created_count`/`created` field mismatch.

## 9. Recommended Fix
- Likely owner: full-stack.
- Backend fix scope:
  - File: `app/domain/sources.py`.
  - Function: `SourceService.import_csv()`.
  - Normalize CSV fields before validation, at minimum `source_type=row.get("source_type", "").strip().lower()` and trim string fields such as `name`, `base_url`, `external_identifier`, `adapter_key`, `company_name`, and `notes`.
  - Preserve duplicate detection behavior after normalization.
  - Decide whether extra CSV fields should produce a row-level invalid result. If strict CSV format is required, rows with `None in row` from `csv.DictReader` should be reported invalid with a clear message about quoting fields containing commas. If not strict, document that extra fields are ignored and still create the source.
- Frontend/template fix scope:
  - File: `app/templates/sources/index.html` or template resolution cleanup in `app/web/routes.py`.
  - Replace `import_result.created_count|default(0)` with `import_result.created`.
  - Display skipped duplicate and invalid counts plus row-level messages, equivalent to `app/web/templates/sources/index.html:88-107`.
  - Avoid success styling when `created == 0` and `invalid > 0`; show an error/warning summary.
  - Consider removing or reconciling the duplicate `app/templates/sources/index.html` and `app/web/templates/sources/index.html` templates so the intended UI is not shadowed.
- CSV correction if no backend normalization is desired:
  - Change `source_type` values to lowercase `greenhouse` and `lever`.
  - Quote any `notes` field containing commas.

## 10. Suggested Validation Steps
- API-level validation:
  - Upload a CSV with title-cased `Greenhouse` and `Lever` source types and unique source keys; expected: rows are created or clear row-level validation explains the required lowercase format.
  - Upload the corrected lowercase CSV; expected: 47 rows created if no duplicates already exist.
  - Re-upload the same corrected CSV; expected: `created == 0`, `skipped_duplicate == 47`, `invalid == 0`.
  - Include a row with a comma in `notes`; expected behavior should match the chosen strictness decision (quoted field succeeds; unquoted extra fields either clearly invalid or documented/handled safely).
- UI validation:
  - Use the `Import sources` button in the active Sources page.
  - Confirm the UI shows created, skipped duplicate, and invalid counts using actual `SourceImportResponse` fields.
  - Confirm row-level invalid messages are visible when rows fail validation.
  - Confirm no success-only `Imported 0 sources.` message is shown when all rows are invalid.
- Regression checks:
  - Existing mixed valid/invalid/duplicate import test behavior in `tests/integration/test_api_flow.py` should remain intact.
  - Add coverage for title-cased source types and HTML import summary rendering.

## 11. Open Questions / Missing Evidence
- The existing database state at the time of the user import was not inspected. However, CSV duplicate analysis found no duplicate keys within the CSV itself, and duplicate-only behavior would produce `skipped_duplicate`, not row-level `invalid`.
- Product decision needed: should CSV enum values be case-insensitive, or should the UI provide/download an exact valid template and clearly reject non-lowercase values? The recommended product-friendly behavior is to accept common case variants by normalizing.
- Product decision needed: should unquoted commas in optional notes invalidate the row, or should extra fields be ignored/truncated? Current importer ignores extra fields silently.

## 12. Final Investigator Decision
Ready for developer fix.

The CSV is partially invalid relative to the current strict backend contract because `source_type` values are title-cased, and one notes field contains unquoted commas. The feature also has defects: the importer is unnecessarily case-sensitive without actionable UI feedback, and the active UI template displays a non-existent response field while hiding row-level import errors.
