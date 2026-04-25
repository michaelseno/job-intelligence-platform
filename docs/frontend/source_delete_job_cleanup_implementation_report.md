# Implementation Report

## 1. Summary of Changes
Implemented frontend/template updates for source delete job cleanup. The delete confirmation now warns that cleanup is asynchronous and that only Matched + Active jobs are retained, the post-delete success message states that non-retained jobs are hidden from Dashboard and Jobs, and retained jobs with deleted-source provenance are labeled with a neutral “Deleted source” badge.

QA remediation update: restored the canonical runtime jobs templates under `app/templates/jobs/`, removed the route-level jobs-template fallback, and aligned the `app/templates` source delete confirmation with the UI/UX cleanup copy so the active Jinja search path no longer depends on `app/web/templates/jobs/*` for normal rendering.

## 2. Files Modified
- `app/web/templates/sources/delete_confirm.html`
- `app/templates/sources/delete_confirm.html`
- `app/templates/jobs/list.html`
- `app/templates/jobs/detail.html`
- `app/web/templates/jobs/list.html`
- `app/web/templates/jobs/detail.html`
- `app/web/routes.py`
- `tests/ui/test_source_edit_delete_ui_qa.py`
- `docs/frontend/source_delete_job_cleanup_implementation_plan.md`
- `docs/frontend/source_delete_job_cleanup_implementation_report.md`

## 3. UI Behavior Implemented
- Source delete confirmation uses destructive cleanup copy and explicitly states that linked jobs are cleaned up in the background.
- Confirmation copy states the strict retention rule: only jobs that are both Matched and Active are retained.
- Success flash states cleanup has started and non-retained jobs are hidden from Dashboard and Jobs immediately.
- Retained jobs can show deleted-source provenance as historical/non-actionable via a muted “Deleted source” badge in job list and job detail source evidence.
- Deleted sources remain excluded from normal source filter options; no disabled deleted-source option was added.
- Jobs HTML now resolves from the primary `app/templates/jobs/` runtime location, matching the rest of the selected `app/templates` design system and avoiding the previous `TemplateNotFound: jobs/list.html` failure mode.

## 4. Assumptions Made
- The backend provides immediate visibility suppression, so no client-side filtering, polling, or cleanup progress UI was added.
- Exact “will be removed” and “retained” counts are not available in the existing delete impact summary, so no exact cleanup counts were fabricated.
- Existing external posting links remain actionable because they target the job posting, not source management or ingestion actions.

## 5. Validation Performed
- QA remediation validation using the repository `.venv` completed successfully: `.venv/bin/python -m pytest tests/api/test_source_delete_job_cleanup_api.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/ui/test_source_edit_delete_ui_qa.py tests/integration/test_source_edit_delete_html.py` → `11 passed`.
- Full targeted source cleanup QA suite completed successfully: `.venv/bin/python -m pytest tests/unit/test_source_delete_cleanup.py tests/unit/test_job_visibility.py tests/api/test_source_delete_job_cleanup_api.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/ui/test_source_edit_delete_ui_qa.py tests/unit/test_source_edit_delete.py tests/api/test_source_edit_delete_qa.py tests/integration/test_source_edit_delete_html.py` → `19 passed`.
- Syntax validation completed successfully: `.venv/bin/python -m compileall app tests/unit/test_source_delete_cleanup.py tests/api/test_source_delete_job_cleanup_api.py tests/integration/test_source_delete_job_cleanup_surfaces.py tests/api/test_source_edit_delete_qa.py tests/integration/test_source_edit_delete_html.py tests/ui/test_source_edit_delete_ui_qa.py`.
- Whitespace validation completed successfully: `git diff --check`.

## 6. Known Limitations / Follow-Ups
- Stale `/jobs?source_id=<deleted>` currently resets the dropdown by omission of the deleted source option but does not add an explicit informational alert.
- If product later requires exact pre-delete removal/retention counts, backend impact summary data will need to be extended first.
- The repository still contains unrelated duplicate `* 2` files and unrelated deleted documentation files noted by QA; those were not changed as part of this scoped remediation.

## 7. Commit Status
Not committed per user instruction. No push or PR was created.
