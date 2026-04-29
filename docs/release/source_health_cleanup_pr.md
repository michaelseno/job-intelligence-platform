# Pull Request

## 1. Feature Name
source_health_cleanup

## 2. Summary
Fixes source-health noise by cleaning invalid/duplicate source rows, hardening duplicate prevention, repairing Insider Lever parsing, adding a migration schema guardrail, and seeding 13 validated ATS sources.

## 3. Related Documents
- Bug Report: docs/bugs/source_health_cleanup.md
- Migration Blocker Report: docs/bugs/source_health_cleanup_unapplied_migration_blocker.md
- New Sources Validation: docs/bugs/source_health_new_sources_validation.md
- Backend Plan: docs/backend/source_health_cleanup_implementation_plan.md
- Backend Report: docs/backend/source_health_cleanup_implementation_report.md
- QA Plan: docs/qa/source_health_cleanup_test_plan.md
- QA Report: docs/qa/source_health_cleanup_qa_report.md
- Migration Retest: docs/qa/source_health_cleanup_unapplied_migration_blocker_retest.md
- New Sources QA: docs/qa/source_health_new_sources_qa_report.md

## 4. Changes Included
- Adds source health cleanup/backfill logic to soft-delete confirmed bad 404 sources, HubSpot Greenhouse, and duplicate active company/provider rows.
- Enforces active duplicate prevention with `company_provider_key` in service validation and migration-backed partial unique indexing.
- Fixes the Lever adapter to tolerate Insider-style string/mixed `lists[].content` payloads.
- Adds startup schema guardrail to fail fast when PostgreSQL has unapplied Alembic migrations.
- Seeds 13 validated ATS sources idempotently through Alembic migration `20260429_0004`.
- Updates tests and documentation covering cleanup, migrations, schema guardrails, parser behavior, and source seeding.

## 5. QA Status
- Approved: YES
- Latest QA status: [QA SIGN-OFF APPROVED]
- HITL validation: HITL validation successful

## 6. Test Coverage
- Source addition targeted tests: `20 passed, 4 warnings`.
- Unit + adapter contract regression: `49 passed, 4 warnings`.
- Compile check: passed.
- Original cleanup targeted evidence includes duplicate prevention, cleanup idempotency, migration/index coverage, and Insider Lever parser coverage.

## 7. Risks / Notes
- Operators must run `alembic upgrade head` against the active `DATABASE_URL` before local/deployed app usage so migrations through `20260429_0004` are applied.
- Broader API/HTML regression was environment-limited until the local PostgreSQL database is migrated; the new guardrail intentionally blocks stale-schema startup.
- Earlier stash `stash@{0}` for unrelated source batch run docs was not applied and is not included.

## 8. Linked Issue
- Closes #16
