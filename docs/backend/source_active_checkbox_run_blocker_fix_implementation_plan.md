# Implementation Plan

## 1. Feature Overview

Fix the source active checkbox form parsing bug that caused checked `is_active=true` submissions to persist inactive sources and block source runs with an inactive-source `409`.

## 2. Technical Scope

- Update backend form parsing to treat common checked checkbox values as truthy.
- Ensure both create and edit source HTML form flows use the corrected parsing path.
- Add regression tests for `true`, `on`, omitted checkbox behavior, edit behavior, and run flow behavior.

## 3. Files Expected to Change

- `app/web/routes.py`
- `tests/integration/test_source_edit_delete_html.py`
- `docs/backend/source_active_checkbox_run_blocker_fix_implementation_report.md`

## 4. Dependencies / Constraints

- Preserve current omitted-checkbox behavior as inactive.
- Do not alter source templates unless backend robustness is insufficient.
- Do not modify or undo the hide-rejected-job implementation.

## 5. Assumptions

- Checked checkbox values of `on`, `true`, `1`, and `yes` should persist `is_active=True`.
- Missing checkbox values represent unchecked and should persist `is_active=False` for HTML form submissions.
- Existing create and edit source flows share `parse_source_form()`, so a parser fix covers both.

## 6. Validation Plan

- Run focused source edit/delete HTML integration tests.
- Run backend unit/API/integration test suites.
- Run the full test suite and document any unrelated existing UI failures.
