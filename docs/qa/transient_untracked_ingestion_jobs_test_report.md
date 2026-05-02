# Test Report

## 1. Execution Summary

- Feature: transient untracked ingestion jobs
- Branch: `feature/transient_untracked_ingestion_jobs`
- QA date: 2026-05-01
- QA decision: **APPROVED**
- Feature-specific targeted validation: **15 passed, 0 failed**
- Remediated prior regression-failure scope: **38 passed, 0 failed**
- Full-suite regression validation: **130 passed, 0 failed, 4 warnings**
- Compile validation: **PASS**

QA independently re-ran the transient feature suite, the prior failure/remediation regression scope, the full pytest suite, and Python compile validation after regression-test remediation. The previously blocking full-suite failures are resolved.

Supplemental QA validation scripts included in the executed suite:

- `tests/api/test_transient_untracked_ingestion_jobs_qa.py`
- `tests/integration/test_transient_untracked_cleanup_migration_qa.py`

## 2. Detailed Results

| Command | Result | Evidence |
| --- | --- | --- |
| `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest tests/unit/test_transient_ingestion_jobs.py tests/api/test_transient_untracked_ingestion_jobs_qa.py tests/integration/test_transient_untracked_cleanup_migration_qa.py tests/ui/test_transient_ingestion_jobs_ui.py tests/ui/test_hide_rejected_job_openings_ui.py` | PASS | `15 passed in 0.37s` |
| `python3 -m compileall app tests` | PASS | Application and test files compiled successfully; no compile errors emitted |
| `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest tests/api/test_source_edit_delete_qa.py tests/integration/test_api_flow.py tests/integration/test_html_views.py tests/integration/test_source_edit_delete_html.py tests/ui/test_saas_dashboard_ui_revamp.py tests/ui/test_source_edit_delete_ui_qa.py tests/unit/test_source_batch_run_qa_validation.py` | PASS | `38 passed in 0.94s` |
| `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest` | PASS | `130 passed, 4 warnings in 3.05s` |

### Feature-Specific Coverage Executed

- Ingestion skips DB persistence for new untracked candidates.
- Source-link, classification, and decision-rule records are not created for untracked ingestion-only candidates.
- Transient API list/detail exposes runtime-only untracked jobs.
- Invalid transient tracking status returns `400`, creates no DB rows, and leaves transient item available.
- Subsequent ingestion refreshes the per-source transient set and expires prior transient IDs.
- Simulated restart/registry clear removes untracked transient visibility without DB fallback.
- Tracking a transient job via API persists `JobPosting`, `JobSourceLink`, `JobDecision`, `JobDecisionRule`, `JobTrackingEvent`, and source-run linkage.
- Tracked transient job remains persisted after registry clear.
- Existing tracked match updates without transient duplicate.
- Cleanup migration deletes `tracking_status IS NULL` jobs, including `manual_keep=true`, removes dependents, preserves tracked jobs, and is idempotent.
- UI renders temporary callout/badge, runtime-safe transient detail route, and transient tracking form.
- Hide-rejected UI regression remains passing.

### Remediation Regression Scope Executed

- Stale persisted-job expectations after ingestion remediation.
- Source delete/background cleanup test-session remediation.
- UI shell fixture remediation.
- Batch source-run concurrency stabilization.

## 3. Failed Tests

No failed tests in the executed validation scope.

Full-suite warning evidence:

- `tests/unit/test_schema_guard.py` emitted four Alembic `DeprecationWarning` warnings: `No path_separator found in configuration; falling back to legacy splitting on spaces, commas, and colons for prepend_sys_path.`
- Classification: non-blocking environment/dependency deprecation warning; no test failure and no observed feature impact.

## 4. Failure Classification

No unresolved failures remain.

Previously reported failure groups are closed by re-run evidence:

| Prior failure group | Current result | QA disposition |
| --- | --- | --- |
| Stale tests expecting newly ingested untracked jobs in persisted `/jobs` JSON | PASS in remediation scope and full suite | Closed as remediated Test Bug |
| Source-delete background cleanup using isolated in-memory DB session | PASS in remediation scope and full suite | Closed as remediated Environment/Test Infrastructure Issue |
| UI shell tests bypassing repository `client` fixture | PASS in remediation scope and full suite | Closed as remediated Environment/Test Infrastructure Issue |
| Batch executor threaded SQLite contention | PASS in remediation scope and full suite | Closed as remediated Environment/Test Infrastructure Issue |

## 5. Observations

- The feature-specific transient validation remains green after regression-test remediation.
- The full regression suite is now green under the requested in-memory SQLite execution configuration.
- The runtime registry restart simulation validates the intended non-durable behavior for untracked ingestion results.
- The cleanup migration remains idempotent and preserves tracked jobs regardless of `manual_keep` value.
- No flaky behavior was observed across the re-run commands.

## 6. Regression Check

Confirmed unchanged/passing behaviors:

- Existing tracked job update path during ingestion still persists updates and source-link data.
- Persisted tracked job detail route remains available after transient tracking persistence.
- Source edit/delete API and HTML flows pass after remediation.
- Shared UI shell routes pass using the repository test fixture.
- Source batch run concurrency regression test passes.
- Existing hide-rejected job UI regression test remains passing.
- Python compile check passes for `app` and `tests`.

## 7. Acceptance Criteria Outcome

| AC | Outcome | Evidence |
| --- | --- | --- |
| AC-01 | PASS | Unit/API tests assert no `JobPosting` row after new untracked ingestion. |
| AC-02 | PASS | Unit/API tests assert no `JobSourceLink`, `JobDecision`, or `JobDecisionRule` rows for ingestion-only untracked candidates. |
| AC-03 | PASS | Transient API and UI tests show runtime-visible temporary jobs. |
| AC-04 | PASS | API test verifies second ingestion replaces prior transient set and old ID returns `404`; registry unit coverage validates replacement semantics. |
| AC-05 | PASS | API test clears runtime registry to simulate restart; transient list is empty and detail returns `404` with no DB fallback. |
| AC-06 | PASS | API/unit tests verify existing tracked match updates and creates no transient duplicate. |
| AC-07 | PASS | Ingestion persistence rule is validated for untracked candidates; cleanup/manual_keep tests confirm `manual_keep=true` does not preserve untracked persistence. |
| AC-08 | PASS | Cleanup QA test deletes existing `manual_keep=true`, `tracking_status NULL` job. |
| AC-09 | PASS | Cleanup QA test preserves tracked jobs regardless of `manual_keep`. |
| AC-10 | PASS | API test tracks transient with non-null status and persists job. |
| AC-11 | PASS | API test verifies source link, decision, decision rule, event, and source-run linkage are persisted. |
| AC-12 | PASS | API test clears registry after tracking and verifies persisted job remains accessible through `/jobs/{job_id}`. |
| AC-13 | PASS | Cleanup QA test verifies untracked job rows are removed. |
| AC-14 | PASS | Cleanup QA test verifies no orphaned source-link/classification/event/reminder/digest rows remain for removed jobs. |
| AC-15 | PASS | Cleanup QA test runs migration upgrade twice without deleting tracked jobs or failing. |

## 8. QA Decision

[QA SIGN-OFF APPROVED]

Approval basis: all critical feature tests passed, prior blocking regression failures are remediated, full-suite regression passed, compile validation passed, and no unresolved failures or blocking defects remain.
