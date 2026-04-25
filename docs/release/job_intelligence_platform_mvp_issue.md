# Planning Issue

## Feature Name
Job Intelligence Platform MVP

## Problem Summary
Job searching is fragmented across Greenhouse, Lever, and direct career pages, making it difficult to consistently discover, review, and track relevant roles. The MVP implementation anchor is a single-user, local-first web application that centralizes source onboarding, ingestion, explainable classification, manual keep/save decisions, application tracking, reminders, digests, and source health visibility.

## Linked Planning Documents
- Product Spec: `docs/product/job_intelligence_platform_mvp_product_spec.md`
- Technical Design: `docs/architecture/job_intelligence_platform_mvp_technical_design.md`
- Implementation Plan: `docs/architecture/job_intelligence_platform_implementation_plan.md`
- UI/UX Spec: `docs/uiux/job_intelligence_platform_mvp_uiux_spec.md`
- Frontend Plan: `docs/frontend/job_intelligence_platform_frontend_implementation_plan.md`
- Backend Plan: `docs/backend/job_intelligence_platform_backend_implementation_plan.md`
- QA Plan: `docs/qa/job_intelligence_platform_mvp_test_plan.md`

## Scope Summary
- Deliver the core MVP workflow: add source -> ingest jobs -> classify -> review in dashboard -> keep/save -> track applications -> review digest/reminders.
- Support source onboarding by manual form and CSV import.
- Implement connector coverage for Greenhouse, Lever, named common ATS patterns, and a bounded set of custom adapters.
- Normalize and deduplicate jobs into canonical records with source attribution and run history.
- Classify jobs into `matched`, `review`, or `rejected` with deterministic rules, score output, evidence snippets, and sponsorship ambiguity defaulting to `review`.
- Provide server-rendered FastAPI + Jinja UI for dashboard, jobs, sources, tracking, digest/reminders, and source health.
- Persist application tracking separately from automated classification and preserve manual keep/save behavior.
- Include local-first scheduling, digest/reminder generation, and source health / operational observability.

## Implementation Notes
- Primary implementation anchor is a modular monolith using FastAPI, Jinja templates, PostgreSQL, and internal background execution.
- Recommended workstreams are: platform foundation; source ingestion; classification and workflow state; user-facing web experience; scheduling, notifications, and operations.
- Delivery should prioritize schema and service dependencies in order so UI detail pages and notifications are built on stable canonical job, decision, and tracking models.
- Frontend should remain HTML-first with minimal progressive enhancement and clear separation of automated bucket, tracking status, and source health.
- Backend services should preserve deterministic, auditable behavior with immutable run and classification history.
- QA should validate adapter contract coverage, ingestion idempotency, classification transparency, sponsorship handling, reminder/digest correctness, and end-to-end workflow success.

## QA Section
- QA Planning Document: `docs/qa/job_intelligence_platform_mvp_test_plan.md`
- Current Status: Planning artifact available; implementation testing not yet executed.
- Required QA focus areas:
  - source onboarding validation and duplicate prevention
  - ingestion, normalization, attribution, deduplication, and idempotency
  - explainable classification and sponsorship ambiguity behavior
  - dashboard/detail UX clarity and workflow correctness
  - tracking, reminders, digest generation, and source health visibility
  - end-to-end MVP flow and failure-path coverage

## Risks / Open Questions
- Connector fragility may consume substantial implementation time, especially for common patterns and custom adapters.
- Common ATS pattern list, custom adapter list, and reminder thresholds still need confirmation.
- Rules tuning may require iteration to avoid over-rejection while preserving explainability.
- Local background execution and non-overlapping run behavior must be validated early to avoid hidden operational issues.
- UX must prevent confusion between classification bucket, tracking status, and source health.

## Current Planning Defaults
- CSV import uses a baseline create-only schema centered on `name`, `source_type`, `base_url`, `external_identifier`, `adapter_key`, `company_name`, `is_active`, and `notes`.
- MVP digest/reminder delivery is required in-app; optional file/email output is deferred.
- MVP scheduler approach is in-process, local-first, with persisted run state and manual trigger parity.
- Manual keep/save remains distinct from automated bucket and only initializes tracking status `saved` when no tracking status already exists.

## Definition of Done
- Planning documents are linked and implementation sequencing is clear.
- Core MVP architecture, scope boundaries, and workstreams are documented and aligned.
- Backend, frontend, UX, and QA expectations are anchored to the same implementation objective.
- A repository issue exists to track implementation against these planning artifacts.
- No code changes, release actions, PR creation, or deployment actions are included in this planning issue.
