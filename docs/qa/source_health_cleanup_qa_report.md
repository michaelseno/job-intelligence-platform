# Test Report

## 1. Execution Summary
- Total targeted tests: 13
- Targeted passed: 13
- Targeted failed: 0
- Broader source regression tests: 44 executed, 42 passed, 2 failed due local database schema/environment mismatch during background cleanup task
- Compile check: passed

## 2. Detailed Results
| Test / validation | Outcome | Evidence |
|---|---:|---|
| `PYTHONPATH=. uv run --with-editable . pytest tests/unit/test_sources.py tests/unit/test_source_health_cleanup.py tests/adapter_contract/test_lever_adapter.py tests/integration/test_source_health_migrations.py` | Passed | `13 passed in 1.22s` |
| `PYTHONPATH=. uv run --with-editable . python -m compileall app alembic` | Passed | Completed listings for `app` and `alembic` without errors. |
| Broader source regression command covering unit/API/integration/adapter source tests | Environment-limited | `42 passed, 2 failed in 1.60s`; failures are `psycopg.errors.UndefinedColumn: column sources.company_provider_key does not exist` from local PostgreSQL used by background cleanup, not from the in-memory test session. |
| Changed-file scope inspection | Passed | Changed files are backend/domain/persistence/adapter, Alembic, tests, and docs only. No frontend templates/routes/static files changed. |
| Code inspection: cleanup idempotency/safety | Passed | Cleanup selects non-deleted sources, backfills stable keys, soft-deletes only configured removal identifiers and duplicate active groups, and commits once. Existing unit test confirms second cleanup run returns no new removals/duplicates. |
| Code inspection: migration ordering | Passed | Migration adds nullable `company_provider_key`, runs cleanup/backfill, then creates active unique index. Integration test verifies column and index. |

## 3. Failed Tests
### Broader regression environment failures
- `tests/api/test_source_edit_delete_qa.py::test_deleted_and_nonexistent_source_endpoints_return_not_found`
- `tests/integration/test_source_edit_delete_html.py::test_source_delete_html_flow_hides_deleted_source_from_management_surfaces`

Error excerpt:
```text
psycopg.errors.UndefinedColumn: column sources.company_provider_key does not exist
SQL: SELECT ... sources.company_provider_key ... FROM sources WHERE sources.id = %(pk_1)s::INTEGER
```

Reproduction steps:
1. Run the broader source regression command in the current workspace with the local `.env` PostgreSQL database not upgraded to the new migration.
2. Trigger source delete flow tests.
3. Background task `run_source_delete_cleanup()` opens `app.persistence.db.SessionLocal()` against local PostgreSQL instead of the pytest in-memory SQLite fixture.
4. ORM model expects `sources.company_provider_key`; local DB schema does not yet contain it.

## 4. Failure Classification
| Failure | Classification | Root cause hypothesis | Severity / impact |
|---|---|---|---|
| Two broader regression failures above | Environment Issue / test harness isolation issue | Local PostgreSQL schema has not been upgraded to migration `20260429_0003`, and the existing background cleanup task bypasses the pytest session override. | Non-blocking for this bugfix validation after migration; blocks using that local DB without running migrations. |

No targeted acceptance-criteria test failed.

## 5. Observations
- The implementation treats removed sources as soft-deleted (`deleted_at` set, `is_active=False`), matching existing source deletion conventions.
- HubSpot Greenhouse is included in `REMOVED_GREENHOUSE_IDENTIFIERS`, satisfying the confirmed removal decision.
- Insider Lever is not in the removal identifiers and is covered by Lever parser contract tests.
- Duplicate prevention is enforced in service validation and with a migration-backed partial unique index on `company_provider_key` for non-deleted rows.
- No frontend issue was proven; implementation made no frontend changes.

## 6. Regression Check
- Targeted source-health cleanup, duplicate prevention, Lever adapter, and migration integration coverage passed.
- Broader source regression was mostly successful but exposed an environment/test isolation limitation when the local PostgreSQL database is not migrated.
- Existing duplicate template files remain unchanged; they were previously identified as maintainability noise, not the source-health root cause.

## 7. QA Decision
Approved for the implemented backend/data-ingestion bugfix, with the operational limitation that deployed/local PostgreSQL databases must run Alembic migration `20260429_0003` before application code using the new ORM model is exercised.

[QA SIGN-OFF APPROVED]
