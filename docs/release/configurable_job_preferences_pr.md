# Pull Request

## 1. Feature Name
Configurable Job Preferences

## 2. Summary
Adds browser-local configurable job preferences with a simplified four-step `/job-preferences` setup wizard for job categories, location countries, work arrangement, and visa sponsorship. Saved preferences map to backend classification criteria, drive reclassification/source-run workflows, and keep detailed keyword controls in collapsed Advanced settings after setup.

## 3. Related Documents
- Product Spec: docs/product/configurable_job_preferences_product_spec.md
- Technical Design: docs/architecture/configurable_job_preferences_architecture.md
- UI/UX Spec: docs/uiux/configurable_job_preferences_uiux.md
- QA Test Plan: docs/qa/configurable_job_preferences_test_plan.md
- QA Report: docs/qa/configurable_job_preferences_qa_report.md
- Release Issue: docs/release/configurable_job_preferences_issue.md
- HITL Correction Report: docs/bugs/configurable_job_preferences_hitl_simplification.md
- QA Failure Report: docs/bugs/configurable_job_preferences_qa_failures.md
- Visa Neutral Bug Report: docs/bugs/configurable_job_preferences_visa_neutral_bug.md
- Backend Implementation Report: docs/backend/configurable_job_preferences_implementation_report.md
- Frontend Implementation Report: docs/frontend/configurable_job_preferences_implementation_report.md

## 4. Changes Included
- Adds `/job-preferences` wizard UI and navigation placement after Dashboard.
- Adds browser-local preference persistence and source-run preference payload integration.
- Maps wizard selections to backend `JobFilterPreferences` criteria used by classification/reclassification.
- Moves detailed keyword/scoring controls into collapsed Advanced settings after setup.
- Updates classification behavior so Visa = No keeps sponsorship neutral.
- Adds/updates backend, frontend, integration, UI, and JS tests plus release/planning documentation.

## 5. QA Status
- Approved: YES
- QA gate: [QA SIGN-OFF APPROVED]
- HITL gate: HITL validation successful

## 6. Test Coverage
- JS syntax checks: passed
- Node JS tests: 14 passed
- Visa-specific backend tests: 9 passed
- Targeted preference tests: 24 passed
- Full Python regression: 82 passed

## 7. Risks / Notes
- Preferences are intentionally local/browser-based only for this feature; auth, DynamoDB, and backend preference persistence remain out of scope.
- First-time setup uses predefined job categories only; custom/free-text saved categories are out of scope.
- Advanced keyword controls are secondary/collapsed after setup to preserve usability while retaining configurability.
- Source-run/classification workflows depend on submitted browser preference payloads; backend revalidates client-controlled data.

## 8. Linked Issue
- Closes #10
