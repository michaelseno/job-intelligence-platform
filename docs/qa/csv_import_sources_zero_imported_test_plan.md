# Test Plan

## 1. Feature Overview
Validate the CSV source import bugfix for `/sources/import` and the active Sources UI import panel. The fix must allow common title-cased `source_type` values (`Greenhouse`, `Lever`) to import after normalization, preserve duplicate detection, surface malformed CSV rows as row-level errors, and prevent misleading UI-only `0 imported` messaging.

## 2. Acceptance Criteria Mapping
| Acceptance criterion | Test coverage |
| --- | --- |
| User can import `/Users/mjseno/Downloads/job_board.csv` from the UI Import CSV form using `Import sources`. | Manual/TestClient HTML upload of the provided file with count/schema-only evidence. |
| If CSV format is broken, QA documents exactly what is wrong and how to fix it. | CSV inspection checks headers, row count, required fields, duplicates, source type distribution, and malformed extra-field rows. |
| If upload feature is broken, feature must be fixed and verified. | HTML upload returns HTTP 200 and renders actionable result summary/messages. No upload blocker found. |
| Unique valid rows should import as sources. | API tests for title-cased Greenhouse/Lever and corrected user-shaped CSV rows. Provided CSV valid rows import. |
| Duplicate rows should be skipped. | API duplicate re-upload test and corrected provided CSV re-upload evidence. |
| UI should not misleadingly report only `0 imported` with no explanation when validation errors occur. | UI tests verify created/skipped/invalid labels, row messages, malformed guidance, and absence of `Imported 0 sources`. |

## 3. Test Scenarios
1. Inspect provided CSV schema/counts without exposing row data.
2. Upload provided CSV through HTML import path and verify result summary plus malformed-row guidance.
3. Upload title-cased Greenhouse/Lever rows through backend import endpoint and verify created counts.
4. Re-upload the same valid rows and verify duplicate skip counts.
5. Upload malformed unquoted extra-field CSV row and verify row-level invalid status/message.
6. Upload corrected user-shaped CSV with quoted comma-containing notes and verify success.
7. Verify active UI displays created/skipped/invalid counts and row-level duplicate/invalid messages.
8. Run targeted import regressions and full pytest regression suite.

## 4. Edge Cases
- Title-cased enum values normalized to lowercase before validation.
- Optional notes containing commas must be quoted; unquoted commas create unexpected extra CSV fields.
- Duplicate detection must work after normalization and on full re-upload.
- Mixed import result with created and invalid rows must render warning/validation context instead of success-only messaging.

## 5. Test Types Covered
- Functional API import validation.
- Negative malformed CSV validation.
- Edge-case source type normalization and quoted notes.
- UI integration rendering for import summary and row messages.
- Regression suite execution with unrelated failure classification.

## 6. Coverage Justification
Coverage directly maps to every acceptance criterion and verifies both backend contract behavior and the active HTML template. The provided CSV was inspected/imported using count/schema-only evidence to avoid exposing row data.
