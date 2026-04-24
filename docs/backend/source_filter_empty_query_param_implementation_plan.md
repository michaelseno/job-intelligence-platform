# Implementation Plan

## 1. Feature Overview
Implement a backend-side fix for the Jobs filter so `/jobs?source_id=` is treated as an unset source filter instead of failing request validation.

## 2. Technical Scope
- Update the `/jobs` query parsing path in `app/web/routes.py`.
- Normalize blank `source_id` input to `None` before integer validation.
- Preserve existing integer parsing and downstream `None` filtering semantics.
- Add integration coverage for empty, valid, and invalid `source_id` inputs.

## 3. Files Expected to Change
- `app/web/routes.py`
- `tests/integration/test_api_flow.py`
- `tests/integration/test_html_views.py`
- `docs/backend/source_filter_empty_query_param_implementation_report.md`

## 4. Dependencies / Constraints
- Follow the bug report guidance in `docs/bugs/source-filter-empty-query-param-bug_report.md`.
- Keep changes scoped to backend behavior on the active branch.
- Do not disturb unrelated untracked files.

## 5. Assumptions
- Blank or whitespace-only `source_id` values should map to the same behavior as an omitted query param.
- Non-numeric non-blank values should continue to fail validation.
- No separate `technical_design.md` file is present in the repository, so the bug report and current route behavior are treated as the approved implementation reference.

## 6. Validation Plan
- Run targeted integration tests covering `/jobs` HTML and JSON responses with blank and valid `source_id` inputs.
- Verify invalid non-blank `source_id` still returns a validation error.
