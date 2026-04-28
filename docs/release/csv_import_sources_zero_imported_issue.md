# Issue

## 1. Feature Name
csv_import_sources_zero_imported

## 2. Classification
Bug / Issue Report

## 3. Summary
CSV source imports from the Sources UI reported `0 imported` for a user-provided job board CSV because title-cased `source_type` values were rejected and the active UI hid row-level import feedback.

## 4. Related Documents
- Bug Report: docs/bugs/csv_import_sources_zero_imported_bug_report.md
- Backend Report: docs/backend/csv_import_sources_zero_imported_implementation_report.md
- Frontend Report: docs/frontend/csv_import_sources_zero_imported_implementation_report.md
- QA Report: docs/qa/csv_import_sources_zero_imported_test_report.md

## 5. Acceptance Criteria
- Import `/Users/mjseno/Downloads/job_board.csv` via the UI Import CSV form using `Import sources`.
- Unique valid rows import as sources.
- Duplicate rows are skipped.
- Invalid or malformed rows show actionable row-level feedback.
- CSV guidance is provided for notes or other values containing commas.

## 6. QA Status
- Approved: YES
- Gate: [QA SIGN-OFF APPROVED]
- HITL: HITL validation successful

## 7. Linked GitHub Issue
- https://github.com/michaelseno/job-intelligence-platform/issues/12
