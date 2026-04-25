# Pull Request

## 1. Feature Name
Hide Rejected Job Openings

## 2. Summary
Hide outright rejected job openings from the main actionable Jobs and Dashboard views while preserving matched, review, null, and unknown non-rejected jobs under existing visibility rules. This branch also fixes the source active checkbox parsing blocker that caused checked sources to persist inactive and block Run now.

## 3. Related Documents
- Product Spec: docs/product/hide_rejected_job_openings_product_spec.md
- Technical Design: docs/architecture/hide_rejected_job_openings_technical_design.md
- UI/UX Spec: docs/uiux/hide_rejected_job_openings_uiux_spec.md
- QA Report: docs/qa/hide_rejected_job_openings_test_report.md
- QA Report: docs/qa/source_active_checkbox_run_blocker_qa_report.md
- Planning Issue: https://github.com/michaelseno/job-intelligence-platform/issues/8

## 4. Changes Included
- Adds reusable main-display visibility filtering so explicit `rejected` jobs are excluded from actionable job surfaces.
- Updates Jobs and Dashboard routes/templates so rejected jobs are hidden from lists, counts, previews, and the primary bucket selector.
- Adds backend, integration, and UI regression coverage for rejected-job filtering behavior.
- Fixes source active checkbox parsing so checked sources persist active and no longer block Run now validation.
- Includes product, architecture, UI/UX, QA, backend/frontend implementation, bug, issue, and release documentation artifacts.

## 5. QA Status
- Approved: YES
- [QA SIGN-OFF APPROVED]

## 6. Test Coverage
- Source checkbox/run blocker tests: 7 passed / 0 failed.
- Hide-rejected targeted regression: 13 passed / 0 failed.
- Related regression suites: 17 passed / 0 failed.
- Backend/API/integration suites: 39 passed / 0 failed.
- Full suite: 54 passed / 5 failed.
- Remaining full-suite failures are isolated to `tests/ui/test_saas_dashboard_ui_revamp.py` and classified as unrelated HTML Accept-header/test fixture issues.

## 7. Risks / Notes
- Rejected jobs are hidden from main actionable displays only; records are not deleted or reclassified.
- Direct rejected job detail behavior remains governed by existing source-delete visibility rules.
- Null and unknown non-rejected bucket values remain visible for MVP per the technical design.
- Dashboard rejected-count contract may require future cleanup if product chooses to remove the field entirely.
