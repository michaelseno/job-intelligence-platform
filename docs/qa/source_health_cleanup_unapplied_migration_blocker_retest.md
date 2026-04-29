# Test Report

## 1. Execution Summary
- Retest scope: HITL blocker correction for unapplied migration guardrail plus original source-health cleanup regression.
- Targeted tests executed: 17
- Targeted passed: 17
- Targeted failed: 0
- Compile check: passed
- Broader source regression: environment-limited by intentionally stale local PostgreSQL; failure mode is now the expected actionable schema guardrail, not an opaque `/sources` ORM undefined-column route failure.

## 2. Detailed Results
| Test / validation | Outcome | Evidence |
|---|---:|---|
| `PYTHONPATH=. uv run --with-editable . pytest tests/unit/test_schema_guard.py tests/unit/test_sources.py tests/unit/test_source_health_cleanup.py tests/adapter_contract/test_lever_adapter.py tests/integration/test_source_health_migrations.py` | Passed | `17 passed, 4 warnings in 1.22s` |
| `PYTHONPATH=. uv run --with-editable . python -m compileall app alembic` | Passed | Completed app/Alembic compile traversal without errors. |
| Manual stale DB guardrail check via `validate_database_schema_current(get_settings().database_url)` | Passed | Message: `Database schema is out of date for this application version. Run alembic upgrade head against the same DATABASE_URL before starting the server. Current DB revision: 20260424_0002; required head revision: 20260429_0003.` |
| Broader source regression command covering unit/API/integration/adapter source tests | Environment-limited / expected guardrail | `20 passed, 24 errors`; every TestClient startup error shown was `DatabaseSchemaOutOfDateError` with `alembic upgrade head`, current revision `20260424_0002`, and required head `20260429_0003`. This confirms fail-fast behavior before route-level ORM queries. |
| README/runbook inspection | Passed | `README.md` documents startup schema guardrail and instructs running `alembic upgrade head` against the server `DATABASE_URL`. |
| Startup integration inspection | Passed | `app/main.py` lifespan calls `validate_database_schema_current(settings.database_url)` for non-SQLite databases before scheduler startup/request handling. |

## 3. Failed Tests
No targeted acceptance-criteria tests failed.

### Environment-limited broader regression errors
The broader regression suite cannot complete while the configured local PostgreSQL remains intentionally stale. This is now the expected guardrail behavior:

```text
app.persistence.schema_guard.DatabaseSchemaOutOfDateError: Database schema is out of date for this application version. Run `alembic upgrade head` against the same DATABASE_URL before starting the server. Current DB revision: 20260424_0002; required head revision: 20260429_0003.
```

This is not the prior blocker failure (`psycopg.errors.UndefinedColumn` during `/sources` query). The first actionable signal is now startup schema validation.

## 4. Failure Classification
| Failure / limitation | Classification | Root cause hypothesis | Severity / impact |
|---|---|---|---|
| Broader TestClient/API/integration tests error at startup in current local environment | Environment Issue / Expected Guardrail | Local PostgreSQL is still at Alembic revision `20260424_0002`; repository head is `20260429_0003`. The new guard correctly blocks startup until migration is applied. | Non-blocking for guardrail validation; broader route regression requires running `alembic upgrade head` first. |

## 5. Observations
- Original source-health cleanup behavior remains covered by the 17-test targeted suite: invalid external sources, HubSpot removal, duplicate prevention, duplicate cleanup idempotency/keeper selection, migration column/index, and Lever parser robustness.
- Schema guard unit tests cover stale revision message, current revision allowance, metadata-only test DB behavior, and non-SQLite startup targeting.
- The manual stale DB check used the actual configured local `DATABASE_URL` and reproduced the exact expected actionable message with current and required revisions.
- No frontend changes were introduced or required for this blocker correction.

## 6. Regression Check
- Original targeted cleanup tests still pass after guardrail remediation.
- Compile regression passes for application and migration code.
- Broader route-level regression is intentionally blocked by stale DB guardrail until the local database is migrated; this is the desired prevention of opaque `/sources` 500s.

## 7. QA Decision
Approved. The HITL blocker remediation changes the first failure from an opaque route-level `UndefinedColumn` to a fail-fast actionable schema message that tells the operator to run `alembic upgrade head` and includes current/required revisions. Original source-health cleanup acceptance criteria remain green in targeted automated coverage.

[QA SIGN-OFF APPROVED]
