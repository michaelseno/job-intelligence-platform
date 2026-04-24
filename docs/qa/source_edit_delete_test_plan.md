# Test Plan

## 1. Feature Overview
Validate the new source maintenance workflow that allows users to edit an existing non-deleted source and delete a source from active configuration across HTML and JSON surfaces, while preserving safe behavior for historical jobs, source links, and run history.

## 2. Scope

### In Scope
- Source edit entry points from configured sources list and source detail page.
- Source delete entry points from configured sources list and source detail page.
- HTML edit form rendering, prepopulation, validation, PRG success flow, and messaging.
- HTML delete confirmation rendering, impact summary, confirm/cancel behavior, and success flow.
- JSON/API source update behavior, including partial update semantics.
- JSON/API source delete behavior and not-found handling.
- Validation parity with source creation rules.
- Duplicate detection for updates against other non-deleted sources only.
- `is_active` update behavior and inactive-vs-deleted state separation.
- Exclusion of deleted sources from source management views, jobs source filters, and future ingestion eligibility.
- Safe historical rendering for deleted-source references.

### Out of Scope
- Bulk edit/delete.
- Restore/undelete.
- CSV import updating existing sources.
- Concurrency conflict prevention beyond verifying documented last-write-wins behavior.
- Release/production deployment validation.

## 3. Acceptance Criteria Mapping

| AC | Requirement | Planned Coverage |
|---|---|---|
| AC-01 | Edit/Delete actions visible from sources list | UI integration test on `/sources`; action presence by row state |
| AC-02 | Edit/Delete actions visible from source detail | UI integration test on `/sources/{id}` |
| AC-03 | Edit form prepopulates current values | UI integration + API fixture verification |
| AC-04 | Valid edit persists and returns success state | HTML integration test + API PATCH test |
| AC-05 | Invalid edit shows validation errors and no partial persistence | HTML validation tests + API 400 tests |
| AC-06 | Duplicate edit rejected | Service/integration test + API 400 duplicate test |
| AC-07 | `notes`-only or `is_active`-only update succeeds | HTML/API focused update tests |
| AC-08 | Inactive source remains visible and clearly inactive | UI integration + regression list/detail tests |
| AC-09 | Delete requires confirmation step | UI integration on GET/POST delete flow |
| AC-10 | Delete confirmation shows source identity and impact warnings | UI integration with seeded run/job/tracked-job data |
| AC-11 | Deleted source removed from default sources list | UI integration + query regression tests |
| AC-12 | Deleted source removed from source selectors/filters | UI integration/regression on jobs filter |
| AC-13 | Deleted source cannot be run again | HTML/API/integration run protection tests |
| AC-14 | Historical records remain safe after deletion | Regression tests on jobs/detail/history pages |
| AC-15 | Edit/Delete/Run for nonexistent source returns not found | Route/API negative tests |
| AC-16 | CSV import remains create-only and does not update existing source | Regression test around import behavior |

## 4. Test Strategy

### Test Types Covered
- Functional integration tests for server-rendered HTML routes.
- API tests for JSON update/delete endpoints.
- Domain/service tests for validation, duplicate detection, and delete state transitions where existing suite supports it.
- Regression tests for adjacent source management, jobs filters, and run flows.
- Basic accessibility-focused UI checks for visible labeling and inactive/destructive state clarity.

### Planned Automation Targets
- `tests/api/` for JSON update/delete and API negative cases.
- Existing integration/route test area for HTML route behavior if repository already uses route tests there.
- `tests/ui/` only if browser-level coverage is already available; otherwise use server-rendered response assertions.

### Test Design Principles
- Seed distinct source fixtures to cover active, inactive, duplicate-candidate, deleted, no-history, has-run-history, and has-linked-jobs cases.
- Verify both user-visible response behavior and persisted record state where possible.
- Prefer deterministic seeded data over order-dependent fixtures.
- Reuse existing source-create validation expectations to prove edit parity.

## 5. Test Scenarios

### A. HTML Source List and Detail Entry Points
1. Verify each non-deleted source row on `/sources` exposes `Edit` and `Delete` actions.
2. Verify inactive sources still appear in `/sources` with clear inactive state.
3. Verify deleted sources do not appear in `/sources`.
4. Verify `/sources/{id}` shows `Edit source` and `Delete source` actions for an active source.
5. Verify `/sources/{id}` for an inactive source remains accessible and clearly labeled inactive.

### B. HTML Edit Flow
6. Open `/sources/{id}/edit` and verify all editable fields are prefilled with persisted values.
7. Submit valid full-form edit and verify 303 redirect to detail, success messaging, and updated values shown immediately.
8. Submit edit changing only `notes`; verify success and no unrelated field drift.
9. Submit edit changing only `is_active`; verify success and visible inactive/active status update.
10. Submit edit with missing required fields and verify field-level/page-level errors plus no persistence.
11. Submit edit with unsupported/invalid type-dependent combination and verify validation parity with create rules.
12. Submit edit that changes dedupe-relevant fields to match another non-deleted source and verify duplicate rejection.
13. Submit edit without changing dedupe fields and verify update succeeds.
14. Refresh/resubmit a successful edit flow and verify no misleading duplicate success/failure behavior.

### C. JSON/API Update Flow
15. `PATCH /sources/{id}` with valid partial payload for `notes` only; verify 200 and merged persisted result.
16. `PATCH /sources/{id}` with valid partial payload for `is_active` only; verify 200 and state transition.
17. `PATCH /sources/{id}` with full payload changing dedupe fields; verify success when unique.
18. `PATCH /sources/{id}` with invalid payload; verify 400 with field and/or `__all__` errors.
19. `PATCH /sources/{id}` causing duplicate conflict; verify 400 duplicate response.
20. `PATCH /sources/{id}` for nonexistent source; verify 404.
21. `PATCH /sources/{id}` for deleted source; verify same 404/not-available outcome as HTML.

### D. HTML Delete Flow
22. Open `/sources/{id}/delete` for source with no runs/jobs and verify source naming plus zero-history messaging.
23. Open `/sources/{id}/delete` for source with run history and linked jobs; verify counts/flags and warning copy.
24. Cancel from delete confirmation and verify return to detail page with no state change.
25. Confirm delete and verify redirect to `/sources`, success flash, and source absence from default list.
26. Confirm delete for inactive source and verify deletion succeeds distinctly from prior inactive state.
27. Re-submit delete for already deleted source and verify 404/not-found outcome.

### E. JSON/API Delete Flow
28. `DELETE /sources/{id}` for active source; verify 200, `deleted=true`, and `deleted_at` populated.
29. `DELETE /sources/{id}` for nonexistent source; verify 404.
30. `DELETE /sources/{id}` for already deleted source; verify 404.
31. If implemented, `GET /sources/{id}/delete-impact` returns expected impact summary fields and counts.

### F. Run Eligibility and Historical Safety
32. Attempt ingestion run for deleted source and verify not-found response and no run created.
33. Attempt ingestion run for inactive source and verify blocked outcome with clear message/state.
34. Verify deleted source no longer appears in jobs source filter or other future-action selectors.
35. Verify historical jobs linked to deleted source still render without page failure.
36. Verify run history/provenance views referencing deleted source remain stable and do not expose edit/delete/run actions.

### G. CSV Import Regression
37. Import CSV containing existing source-equivalent row and verify import does not update existing source.
38. Verify CSV import continues create-only semantics and duplicate skipping behavior after feature changes.

## 6. Edge Cases
- Edit only `notes`.
- Edit only `is_active`.
- Change `source_type` so required fields change (`external_identifier` vs `adapter_key`).
- Delete source with no run history.
- Delete source with run history but no linked jobs.
- Delete source with linked jobs and tracked jobs.
- Delete an already inactive source.
- Stale edit submission after another update (documented last-write-wins behavior).
- Stale delete submission after successful deletion (must return 404, not success).
- Attempt run from stale page after delete.

## 7. Negative Cases
- Missing required edit fields.
- Invalid URL/base URL format if enforced by existing validation.
- Unsupported source type.
- Missing `external_identifier` for `greenhouse`/`lever`.
- Missing `adapter_key` for `common_pattern`/`custom_adapter` when applicable.
- Duplicate dedupe identity against another non-deleted source.
- Edit/delete/run against nonexistent source.
- Edit/delete against already deleted source.
- API partial update that becomes invalid after merge.

## 8. Regression Targets
- Source creation validation and duplicate detection behavior unchanged.
- CSV import remains create-only.
- Source list rendering, detail rendering, and run history rendering unchanged for non-target behaviors.
- Manual ingestion run still works for active non-deleted sources.
- Jobs list filter dropdown excludes deleted sources but still functions for active/inactive expected states.
- Historical job/source provenance continues to resolve deleted source references safely.
- Default source/service queries do not accidentally leak deleted rows into dashboards or source-health views.

## 9. Environment / Data Prerequisites

### Environment
- Local test database with latest migration set applied, including `deleted_at` support and updated dedupe index behavior.
- Ability to run backend test suite (`pytest`) and any route/integration test targets.
- If browser/UI automation exists, environment must support `playwright` or current UI test runner.

### Seed Data Needed
- Source A: active greenhouse source with no runs/jobs.
- Source B: active lever source with existing run history only.
- Source C: active source with linked jobs and at least one tracked job.
- Source D: inactive non-deleted source.
- Source E: alternate source whose dedupe identity can be matched to trigger duplicate rejection.
- Source F: deleted/tombstoned source for not-found and filtering assertions.
- Historical job records and source runs tied to deleted candidate source for safe rendering checks.
- CSV fixture containing one new source row and one duplicate-equivalent row.

## 10. Execution Notes
- Execute happy path, negative, and regression scenarios in isolated database state or transactionally reset fixtures.
- Capture HTTP status, redirect targets, flash/error text, and persisted state assertions for every automated scenario.
- For list/filter assertions, verify deleted-source absence and inactive-source presence separately to avoid false positives.
- For duplicate tests, confirm conflict is against another non-deleted source only; equivalent deleted source should not block recreation/update if implementation follows design.

## 11. Risks and Focus Areas for Later QA Execution
- Query-path leakage risk: deleted sources may still appear in one or more lists, filters, dashboards, or selectors.
- Validation parity risk: edit may diverge from create for type-dependent fields or duplicate handling.
- Historical safety risk: deleted-source joins may break jobs, provenance, or run history pages.
- State distinction risk: inactive sources may be treated as deleted, or deleted sources may remain runnable.
- Stale action risk: resubmitted delete/edit/run requests may produce inconsistent not-found/success behavior.

## 12. Test Types Covered
- Functional correctness
- Validation errors
- Edge cases
- Negative scenarios
- API/UI behavior consistency
