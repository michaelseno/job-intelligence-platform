# Pull Request

## 1. Feature Name

Transient untracked ingestion jobs

## 2. Summary

Untracked ingestion jobs are now transient until a user explicitly tracks them, while tracked jobs continue to persist and update normally. Tracking a transient job persists the job, source linkage, classification, decision/tracking metadata, and source-run attribution; a cleanup migration removes existing persisted untracked jobs and dependent records.

## 3. Related Documents
- Product Spec: docs/product/transient_untracked_ingestion_jobs_product_spec.md
- Technical Design: docs/architecture/transient_untracked_ingestion_jobs_technical_design.md
- UI/UX Spec: docs/uiux/transient_untracked_ingestion_jobs_design_spec.md
- QA Report: docs/qa/transient_untracked_ingestion_jobs_test_report.md
- QA Test Plan: docs/qa/transient_untracked_ingestion_jobs_test_plan.md
- Planning Issue: docs/release/transient_untracked_ingestion_jobs_issue.md
- Bug Report: docs/bugs/transient_untracked_ingestion_jobs_full_suite_failures_bug_report.md
- Backend Report: docs/backend/transient_untracked_ingestion_jobs_implementation_report.md
- Frontend Report: docs/frontend/transient_untracked_ingestion_jobs_implementation_report.md

## 4. Changes Included
- Added runtime-only transient ingestion storage for newly discovered untracked jobs.
- Updated ingestion persistence so new untracked jobs do not create durable job/source/classification records.
- Preserved existing tracked-job ingestion update behavior.
- Added transient job list/detail API and UI affordances, including temporary labeling and tracking actions.
- Added transient tracking flow that persists job, source link, classification/decision metadata, tracking event, and source-run linkage.
- Added cleanup migration for existing persisted untracked jobs and dependent records while preserving tracked jobs.
- Added and remediated unit, API, integration, UI, and migration regression coverage.

## 5. QA Status
- Approved: YES
- QA sign-off: [QA SIGN-OFF APPROVED]
- HITL validation: HITL validation successful

## 6. Test Coverage
- Full regression suite: 130 passed, 0 failed, 4 non-blocking warnings.
- Targeted transient feature suite: 15 passed, 0 failed.
- Prior remediation regression scope: 38 passed, 0 failed.
- Compile validation: PASS for `app` and `tests`.

## 7. Risks / Notes
- Runtime-only transient jobs are intentionally lost on refresh/restart until tracked.
- UI copy labels temporary jobs to reduce user confusion.
- Cleanup migration is destructive only for persisted jobs with `tracking_status IS NULL` and owned dependents; tracked jobs are preserved.
- Full suite warnings are Alembic deprecation warnings with no observed feature impact.

## 8. Linked Issue
- Closes #20
