# Implementation Report

## 1. Summary of Changes
Added backend support for source patch/update, delete-impact reporting, and soft deletion. Operational source queries now exclude deleted sources, duplicate checks ignore tombstoned records, and manual runs reject inactive sources.

## 2. Files Modified
- `app/persistence/models.py`
- `app/schemas.py`
- `app/domain/sources.py`
- `app/domain/operations.py`
- `app/web/routes.py`
- `tests/unit/test_sources.py`
- `tests/integration/test_api_flow.py`
- `docs/backend/source_edit_delete_implementation_plan.md`
- `docs/backend/source_edit_delete_implementation_report.md`

## 3. Key Logic Implemented
- Added `deleted_at`-aware active-source filtering and a partial unique index for active `dedupe_key` values.
- Added partial update merge logic in `SourceService` using `SourceUpdateRequest`.
- Reused full validation for updates while excluding the current source from duplicate checks.
- Added delete impact summary counts for runs, linked jobs, and tracked jobs.
- Implemented soft delete by setting `deleted_at` and forcing `is_active = false`.
- Added JSON endpoints: `PATCH /sources/{id}`, `GET /sources/{id}/delete-impact`, and `DELETE /sources/{id}`.
- Updated run eligibility and operational source lists to treat deleted sources as unavailable.

## 4. Assumptions Made
- Historical pages should continue to resolve deleted source rows through direct source lookups already used by job/run views.
- Fresh test/local schema creation is sufficient for validating the partial unique index metadata change in this repository state.
- Frontend/template changes for edit/delete screens are handled separately if needed.

## 5. Validation Performed
- Created a temporary virtual environment outside the repo.
- Installed project and dev dependencies with `pip install -e '.[dev]'` inside that temp environment.
- Ran `python -m pytest tests/unit/test_sources.py tests/integration/test_api_flow.py tests/integration/test_html_views.py`.
- Ran full `python -m pytest`.
- Result: `20 passed`.

## 6. Known Limitations / Follow-Ups
- I did not modify frontend templates/styles in this task.
- The repository currently contains unrelated pre-existing modified/untracked files; they were left untouched.
- If production schema migration files are managed outside current tracked state, a matching migration should be confirmed separately.

## 7. Commit Status
- No commit created, per task instructions.
