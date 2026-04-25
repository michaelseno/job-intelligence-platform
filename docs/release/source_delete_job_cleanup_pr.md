# Pull Request

## 1. Feature Name
Source Delete Job Cleanup

## 2. Summary
Adds asynchronous cleanup after source deletion so non-retained jobs from deleted sources are removed or hidden immediately from user-facing surfaces. Retains only jobs that are both Matched and Active, while marking deleted-source provenance as historical/non-actionable.

Closes #5.

## 3. Related Documents
- Product Spec: docs/product/source_delete_job_cleanup_product_spec.md
- Technical Design: docs/architecture/source_delete_job_cleanup_technical_design.md
- UI/UX Spec: docs/uiux/source_delete_job_cleanup_uiux_spec.md
- QA Test Plan: docs/qa/source_delete_job_cleanup_test_plan.md
- QA Report: docs/qa/source_delete_job_cleanup_qa_report.md
- Backend Report: docs/backend/source_delete_job_cleanup_implementation_report.md
- Frontend Report: docs/frontend/source_delete_job_cleanup_implementation_report.md
- Planning Issue Artifact: docs/release/source_delete_job_cleanup_issue.md

## 4. Changes Included
- Queues source-delete cleanup from API and HTML source deletion flows using FastAPI background tasks.
- Adds cleanup service logic to delete non-retained source-associated jobs and dependent records while keeping matched active jobs.
- Centralizes visible-job filtering for dashboard, jobs, job detail, tracking, reminders, and digest surfaces during pending cleanup.
- Updates delete confirmation and success copy to explain cleanup behavior and retention rules.
- Labels retained deleted-source provenance as historical/deleted and removes deleted sources from actionable filters/controls.
- Adds targeted unit, API, integration, and UI regression tests plus product/design/implementation/QA/release artifacts.

## 5. QA Status
- Approved: YES
- QA sign-off: [QA SIGN-OFF APPROVED]

## 6. Test Coverage
- Targeted pytest suite: 19 passed.
- Compile check passed for application code and targeted tests.
- `git diff --check` passed.
- Coverage includes cleanup retention/deletion matrix, dependent row cleanup, idempotency, visibility filtering, API delete response, dashboard/jobs/tracking/reminders/digest behavior, delete copy, success messaging, and retained provenance labeling.

## 7. Risks / Notes
- FastAPI `BackgroundTasks` are in-process and not durable across process shutdowns; immediate visibility suppression mitigates stale user-facing data until cleanup can be retried.
- Stale `/jobs?source_id=<deleted>` filters reset by omitting deleted source options; no explicit informational alert is shown in this MVP.
- Unrelated duplicate `* 2` files and unrelated deleted historical docs remain intentionally unstaged and are not part of this release.
