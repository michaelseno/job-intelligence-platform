# Implementation Plan

## 1. Feature Overview
This document defines the backend implementation plan for the Job Intelligence Platform MVP. The backend will be delivered as a modular monolith built with FastAPI and PostgreSQL, optimized for local-first execution while preserving clean seams for later AWS-hosted scheduling and worker evolution.

The backend scope covered here includes source onboarding support, ingestion orchestration, canonical job persistence, deterministic classification with evidence, digest and reminder generation, and source health / operational visibility. This plan is implementation-ready but intentionally excludes application code changes.

## 2. Technical Scope

### 2.1 Delivery Goals
- Support MVP backend flows from source creation/import through ingestion, classification, tracking, digest generation, reminders, and source health visibility.
- Keep the system deterministic, auditable, and transparent for a single local user.
- Use PostgreSQL as the authoritative store from day one.
- Keep scheduling and background execution behind interfaces so the same domain services can later run in AWS-managed job infrastructure.

### 2.2 Backend Module / Service Breakdown
The backend should be implemented as the following domain-aligned modules.

#### A. Configuration and App Bootstrap
Responsibilities:
- Load environment and application settings.
- Configure database, scheduler enablement, timeouts, reminder thresholds, and digest mode.
- Wire FastAPI routes, service dependencies, repositories, and background job registration.

#### B. Source Management
Responsibilities:
- Create and validate source records from manual input and CSV rows.
- Distinguish source families: `greenhouse`, `lever`, `common_pattern`, `custom_adapter`.
- Prevent accidental duplicate source creation.
- Store source configuration and current health summary fields.

MVP source input contract:
- Baseline CSV/manual fields: `name`, `source_type`, `base_url`, optional `company_name`, optional `is_active`, optional `notes`.
- `external_identifier` is required when the selected source family needs a board/company locator.
- `adapter_key` is required for `common_pattern` and `custom_adapter` rows.
- CSV import is create-only in MVP and returns created/skipped-duplicate/invalid outcomes per row.

Primary services:
- `SourceService`
- `SourceValidationService`
- `SourceImportService`

#### C. Source Adapter Registry and Connectors
Responsibilities:
- Resolve adapter implementation by `source_type` and `adapter_key`.
- Enforce a common contract across ATS and custom connectors.
- Encapsulate network fetch, parsing behavior, normalization hints, and structured warnings/errors.

Primary services/interfaces:
- `SourceAdapterRegistry`
- `BaseSourceAdapter`
- `GreenhouseAdapter`
- `LeverAdapter`
- `CommonPatternAdapter` variants
- Named custom adapters for the 3-5 approved sources

#### D. Ingestion Orchestration
Responsibilities:
- Create and finalize `source_runs` records.
- Execute per-source ingestion with timeout, retry, and failure capture.
- Persist raw source payloads and source/job provenance.
- Invoke normalization, deduplication, and classification for affected jobs.
- Update source health summaries after each run.

Primary services:
- `IngestionOrchestrator`
- `SourceRunService`
- `HealthComputationService`

#### E. Normalization and Deduplication
Responsibilities:
- Convert source-specific data into a canonical job shape.
- Preserve raw payload snapshots for audit/debugging.
- Create stable dedupe keys and apply merge rules.
- Detect created vs updated vs unchanged jobs.

Primary services:
- `JobNormalizationService`
- `JobDeduplicationService`
- `CanonicalizationUtils`

#### F. Classification and Evidence
Responsibilities:
- Apply deterministic rules to normalized jobs.
- Produce score, bucket, sponsorship state, matched rules, negative rules, and evidence snippets.
- Enforce the MVP rule that ambiguous or missing sponsorship defaults to `review`.
- Persist immutable automated decision history.

Primary services:
- `ClassificationService`
- `RuleEngine`
- `EvidenceExtractionService`
- `DecisionProjectionService`

#### G. Tracking and Workflow State
Responsibilities:
- Keep manual job retention (`manual_keep`) separate from automated classification.
- Persist tracking status history and current tracking projection.
- Feed reminder eligibility and dashboard workflow views.

Primary services:
- `TrackingService`
- `ManualKeepService`
- `TrackingProjectionService`

#### H. Notifications: Digest and Reminders
Responsibilities:
- Generate daily digest outputs for newly classified `matched` and `review` jobs.
- Generate reminders for saved jobs without action and applied jobs needing follow-up.
- Persist generated notifications and expose them to in-app views, with optional file/email output behind config.

Primary services:
- `DigestService`
- `ReminderService`
- `NotificationDeliveryService` (initially `in_app`, optional `file`/`email` later)

#### I. Scheduling and Background Jobs
Responsibilities:
- Schedule local recurring ingestion, digest, and reminder tasks.
- Allow every scheduled action to also be manually triggered.
- Persist execution state and prevent overlapping runs for the same source.

Primary services/interfaces:
- `SchedulerService`
- `JobExecutionService`
- `RunLockService`

#### J. Operations and Observability
Responsibilities:
- Emit structured logs and per-run diagnostics.
- Surface source health states, warning conditions, and run summaries.
- Support diagnosis of failures, repeated empties, and stale sources.

Primary services:
- `OperationalLogService`
- `HealthComputationService`
- `RunDiagnosticsService`

### 2.3 Proposed Package Structure
Recommended package layout:

```text
app/
  main.py
  config/
    settings.py
    logging.py
  web/
    routes/
      dashboard.py
      sources.py
      jobs.py
      operations.py
      digest.py
      reminders.py
    forms/
    view_models/
  domain/
    sources/
      services.py
      models.py
      validators.py
      csv_import.py
    ingestion/
      orchestrator.py
      runs.py
      normalization.py
      deduplication.py
      health.py
    jobs/
      services.py
      models.py
      projections.py
    classification/
      services.py
      rules.py
      evidence.py
      rule_sets/
    tracking/
      services.py
      projections.py
    notifications/
      digest.py
      reminders.py
      delivery.py
    operations/
      diagnostics.py
      health.py
  adapters/
    base/
      contracts.py
      registry.py
      errors.py
    greenhouse/
    lever/
    common_patterns/
    custom/
    shared/
      http.py
      parsing.py
      normalization_helpers.py
  persistence/
    db.py
    models/
    repositories/
    migrations/
  scheduler/
    service.py
    jobs.py
    locks.py
  observability/
    logging.py
    metrics.py
    tracing.py
tests/
  unit/
  integration/
  adapter_contract/
  fixtures/
  end_to_end/
```

Implementation guidance:
- Keep domain services independent of FastAPI request objects.
- Keep adapters isolated from business decision logic.
- Keep repository interfaces close to domain modules, while shared persistence models remain centralized.
- Keep rule configuration versioned and testable under `classification/rule_sets/`.

### 2.4 Domain Model and Persistence Plan
The persistence plan should follow the architecture document’s append-only and audit-friendly approach.

#### Core Tables
1. `sources`
   - Stores configured sources and health summary projections.
   - Includes `source_type`, `adapter_key`, `base_url`, `external_identifier`, `config_json`, `is_active`, and health fields.

2. `source_runs`
   - Stores one record per ingestion attempt.
   - Tracks trigger type, status, timestamps, counts, warning/error totals, empty-result flag, and error details.

3. `job_postings`
   - Canonical job entity used across dashboard, classification, and tracking.
   - Holds summary projections such as `latest_bucket`, `latest_score`, `latest_decision_id`, `manual_keep`, and `tracking_status`.

4. `job_source_links`
   - Preserves per-source provenance, external job identifiers, raw payload snapshots, payload hashes, and source URLs.
   - Enables many-to-one canonical job mapping across duplicate sources.

5. `job_decisions`
   - Immutable automated decision history.
   - Stores `decision_version`, `bucket`, `final_score`, `sponsorship_state`, summary reason text, and `is_current`.

6. `job_decision_rules`
   - Stores rule-level details for each decision.
   - Persists rule key, category, outcome, score delta, evidence snippet, evidence field, and explanation.

7. `job_tracking_events`
   - Stores user workflow history, including save/keep and status changes.
   - Maintains separation between automated classification and user workflow actions.

8. `digests`
   - Stores generated digest instances by date and channel.

9. `digest_items`
   - Stores per-job inclusion in a digest with inclusion reason (`new_matched`, `new_review`).

10. `reminders`
    - Stores generated reminder outputs and current reminder state.

#### Persistence Strategy
- PostgreSQL is the system of record for all domain state.
- Use append-only records for run history, decisions, tracking events, and notifications.
- Use summary/projection fields on `sources` and `job_postings` to support fast dashboard reads.
- Store raw payload JSON for adapter outputs and selected normalized/extracted text for explainability.
- Add indexes early for:
  - active sources and health state
  - source run recency
  - jobs by bucket and recency
  - jobs by tracking status
  - current decision lookup
  - reminders by due status

### 2.5 Ingestion Orchestration and Connector Design

#### Adapter Contract
Every adapter should implement:
- `validate_config(source)`
- `fetch_jobs(source, run_context)`
- optional `fetch_job_detail(candidate, run_context)` when list payloads are incomplete
- `normalize_candidate(candidate)` or equivalent mapping support
- structured warnings and exceptions

The registry should resolve adapters by `source_type` plus optional `adapter_key` so the system can cleanly support standard, common-pattern, and custom connectors.

#### Ingestion Flow
Per source, the orchestrator should execute:
1. Validate source configuration.
2. Create `source_run` with `running` status.
3. Acquire source-scoped execution lock.
4. Fetch source records with adapter timeout and bounded retries.
5. Persist raw payload snapshots / hashes in `job_source_links`.
6. Normalize external records into canonical candidate jobs.
7. Resolve duplicate vs new vs updated job state.
8. Upsert canonical job and provenance links.
9. Re-classify only affected jobs.
10. Compute counts, warnings, empty-result semantics, and run result.
11. Update source summary health fields.
12. Release execution lock and finalize run.

#### Connector Scope Guidance
- First-class support should be built for Greenhouse and Lever.
- Common pattern connectors should only cover named patterns approved in architecture scope.
- Custom adapters should be one module per approved company/source, not a generic crawler framework.
- Unsupported pages should fail explicitly with actionable validation errors rather than degrading silently.

### 2.6 Normalization and Deduplication Pipeline

#### Canonical Normalized Fields
Each normalized job should include:
- source identity: source id, adapter key, external id, original url
- display fields: title, company, location, remote state, employment type
- classification fields: plain-text description, sponsorship text, normalized title tokens, location tokens
- provenance fields: payload hash, first seen timestamp, last seen timestamp, source run id

#### Normalization Rules
- Convert HTML and rich text to normalized plain text for classification.
- Preserve original URLs and compute a normalized URL for dedupe.
- Represent unknown sponsorship and remote/location state explicitly, not as negative values.
- Preserve enough textual content to support evidence extraction in the UI.

#### Deduplication Strategy
Apply the layered approach from the technical design:
1. exact external id match within the same source family
2. normalized canonical URL match
3. high-confidence fingerprint match using company + normalized title + location + description hash prefix

MVP guidance:
- Auto-merge only high-confidence matches.
- Preserve separate rows for lower-confidence similarity cases.
- Track provenance from every contributing source in `job_source_links`.

#### Job Lifecycle Handling
- Maintain `first_seen_at`, `last_seen_at`, and `last_ingested_at` on canonical jobs.
- Do not mark jobs removed on first absence.
- Promote absent jobs to `stale`, then `removed`, only after configured missed-run thresholds.
- Keep saved/applied jobs visible even when stale or removed upstream.

### 2.7 Classification and Evidence Pipeline

#### Classification Approach
Use a deterministic rule engine with explicit score deltas and hard guardrails. No ML or opaque ranking should be introduced in MVP.

#### Rule Families
- role alignment positive
- role mismatch negative
- location positive
- location negative
- sponsorship
- quality/confidence modifiers

#### Decision Behavior
- `matched`: strong role alignment with acceptable location and no explicit sponsorship conflict.
- `review`: ambiguous sponsorship, incomplete location, mixed signals, or low-confidence relevance.
- `rejected`: explicit mismatch conditions with sufficient evidence.

Mandatory product rule:
- Ambiguous or missing sponsorship must not reject a job by itself; it must route the job to `review` when otherwise relevant.

#### Evidence Handling
- Persist evidence at the rule level in `job_decision_rules`.
- Prefer snippets from title, description, location, and sponsorship text.
- Distinguish text-supported evidence from inference when direct snippets do not exist.
- Ensure at least one evidence snippet exists for strong text-based positive or negative rule conclusions when source text is available.

#### Decision Persistence
- Every automated evaluation creates a new `job_decisions` record.
- Only one decision is marked `is_current` per job.
- `job_postings.latest_bucket`, `latest_score`, and `latest_decision_id` are projections for fast reads.
- Manual keep/save or tracking updates must never overwrite automated decision history.

### 2.8 Scheduling and Background Job Approach

#### MVP Runtime Pattern
- Use an in-process scheduler suitable for local execution.
- Back every scheduled execution with persisted run/job records.
- Support manual invocation of all scheduled tasks for testing and local control.

#### Scheduled Task Set
- Daily ingestion sweep across active sources
- Daily digest generation
- Daily reminder generation
- Optional health refresh / stale-state reconciliation

MVP scheduler assumptions:
- In-process scheduler owned by the FastAPI app runtime.
- Persisted run/execution records are required; no business-critical scheduler state may live only in memory.
- All scheduled flows must have equivalent manual trigger paths for local validation.
- Single running app instance is the expected MVP deployment shape.

#### AWS-Ready Boundary
Scheduling and background execution should be accessed through internal interfaces so they can later map to:
- EventBridge or equivalent scheduler
- queue-backed workers
- PostgreSQL/RDS as the retained source of truth

Required design rules for that migration path:
- no business-critical state may live only in memory
- runs must be resumable or safely retryable
- ingestion and notification jobs must be idempotent

### 2.9 Notification and Reminder Backend Flow

#### Digest Flow
1. Daily digest job selects jobs first classified into current `matched` or `review` buckets within the digest window.
2. Create one `digests` row per digest date and channel.
3. Create `digest_items` rows for included jobs.
4. Persist summary text / metadata for in-app rendering.
5. Optionally render to file/email if enabled later, without changing selection logic.

MVP digest delivery decision:
- `in_app` is the required channel.
- Optional file/email delivery is deferred and must reuse the same persisted digest selection logic if implemented later.

#### Reminder Flow
1. Evaluate tracked jobs for reminder eligibility.
2. Generate reminders for:
   - `saved` jobs without recent user action
   - `applied` jobs that have exceeded follow-up threshold
3. Create or refresh `reminders` rows with due dates and status.
4. Expose reminders in the in-app reminders view.
5. Allow dismissal/completion without altering the underlying job decision.

Reminder eligibility rules for implementation alignment:
- `manual_keep` by itself does not create a reminder; it only matters insofar as it may initialize tracking to `saved`.
- Reminder generation uses tracking status plus timestamps from tracking events / job workflow state.
- Reminder snooze is not required for MVP.

#### Workflow Separation Rule
- Classification answers “how relevant is this job?”
- Tracking answers “what is the user doing with this job?”
- Reminders answer “what action is overdue?”

These concerns must stay separated in persistence and service design.

Additional workflow rule:
- If a user invokes keep/save on an untracked job, backend should create the durable retention flag and initialize tracking status `saved`.
- If the job already has tracking status `saved`, `applied`, `interview`, `rejected`, or `offer`, keep/save must not overwrite that status.

### 2.10 Error Handling, Observability, and Idempotency Guidance

#### Error Handling
- Adapter failures must be captured as structured run errors and attached to `source_runs`.
- CSV validation failures must be row-specific and non-silent.
- Parse anomalies should generate warnings even when a run completes successfully.
- Empty-result anomalies should be warning-level when a source historically returns jobs.
- A failing source must not block ingestion of other active sources.

#### Observability
- Emit structured logs with source id, run id, adapter key, and event type.
- Persist run counts for fetched/created/updated/unchanged jobs.
- Store warning and error detail summaries suitable for UI presentation.
- Compute human-readable `healthy`, `warning`, and `error` states for each source.
- Track operational indicators including:
  - last successful run timestamp
  - latest run status
  - jobs fetched count
  - consecutive empty runs
  - parse warning/error counts

#### Idempotency
- Source run finalization must tolerate retried execution safely.
- Job upsert logic must be deterministic for repeated ingestion of the same payload.
- Digest generation should avoid duplicate digest rows for the same date/channel combination.
- Reminder generation should avoid duplicate pending reminders for the same job/reminder type/window.
- Manual re-run of a source should create a distinct `source_run`, but repeated payloads should not duplicate canonical jobs.

### 2.11 Testing Strategy

#### Test Layers
- **Unit tests** for normalization helpers, rule scoring, sponsorship override behavior, health computation, and reminder eligibility.
- **Adapter contract tests** for every connector, including shared error semantics and config validation behavior.
- **Fixture-based tests** for Greenhouse, Lever, each approved common pattern, and each custom adapter.
- **Integration tests** for ingestion orchestration, dedupe/upsert behavior, decision persistence, and digest/reminder persistence.
- **Route/service tests** for source import, manual run triggers, job keep/save, and tracking updates.
- **End-to-end tests** for the core flow: source onboarding -> ingestion -> classification -> dashboard-ready reads -> tracking -> digest/reminders.

#### Priority Validation Scenarios
- duplicate source detection during manual entry and CSV import
- exact-match and fingerprint deduplication behavior
- sponsorship ambiguity routing to `review`
- evidence persistence for positive and negative rules
- source health degradation on repeated empty runs
- reminders generated from tracking state, not classification bucket alone
- digest inclusion limited to newly relevant `matched` and `review` jobs

### 2.12 Backend Milestone Plan
The backend implementation should follow the architecture milestone order with backend-specific deliverables.

#### Milestone 0: Foundation
- FastAPI app wiring, settings, logging, database integration, migration framework
- Initial schema for `sources`, `source_runs`, `job_postings`, `job_source_links`

#### Milestone 1: Source Management
- Source CRUD foundations
- CSV import service and validation feedback model
- Duplicate detection and source summary projections

#### Milestone 2: Core Connector Framework
- Adapter contract and registry
- Greenhouse and Lever adapters
- Source run orchestration and error handling

#### Milestone 3: Canonical Jobs and Deduplication
- Normalization service
- Canonical job persistence
- Source provenance links
- High-confidence duplicate merge logic

#### Milestone 4: Deterministic Classification
- Rules engine
- Evidence extraction
- Decision persistence and latest-decision projection
- Sponsorship ambiguity override to `review`

#### Milestone 5: Tracking and Workflow State
- Manual keep/save flow
- Tracking event history and current tracking projection
- Reminder eligibility primitives

#### Milestone 6: Notifications and Scheduling
- Local scheduler abstraction
- Daily ingestion sweep
- Digest generation and reminder generation
- In-app notification persistence

#### Milestone 7: Source Health and Operational Hardening
- Health state computation
- Empty-result anomaly logic
- Run diagnostics views/read models
- Retry/idempotency hardening and end-to-end validation

## 3. Files Expected to Change
Planned backend implementation work is expected to affect, at minimum, the following areas when coding begins:

- `app/main.py`
- `app/config/`
- `app/web/routes/`
- `app/domain/sources/`
- `app/domain/ingestion/`
- `app/domain/jobs/`
- `app/domain/classification/`
- `app/domain/tracking/`
- `app/domain/notifications/`
- `app/domain/operations/`
- `app/adapters/base/`
- `app/adapters/greenhouse/`
- `app/adapters/lever/`
- `app/adapters/common_patterns/`
- `app/adapters/custom/`
- `app/persistence/models/`
- `app/persistence/repositories/`
- `app/persistence/migrations/`
- `app/scheduler/`
- `app/observability/`
- `tests/unit/`
- `tests/integration/`
- `tests/adapter_contract/`
- `tests/fixtures/`
- `tests/end_to_end/`

This planning task itself creates only:
- `docs/backend/job_intelligence_platform_backend_implementation_plan.md`

## 4. Dependencies / Constraints
- Must follow the MVP product specification and architecture documents exactly.
- Backend stack is FastAPI + PostgreSQL.
- MVP is single-user and local-first.
- No authentication is required in local MVP.
- Scheduling must work locally first but remain replaceable for AWS later.
- Source support is bounded to Greenhouse, Lever, named common ATS patterns, and 3-5 approved custom adapters.
- Classification must be deterministic, auditable, and transparent.
- Unsupported sources must fail explicitly rather than silently.
- Do not introduce an ML-based ranking system or a generic crawler framework in MVP.

## 5. Assumptions
- In-app digest and reminder views are sufficient for MVP, with optional file/email delivery remaining a configuration-backed extension.
- The approved custom adapter list and common-pattern list will be finalized before implementation of those specific connectors.
- Reminder threshold defaults will come from configuration rather than per-job user customization in MVP.
- SQL migrations, repositories, and ORM details may be chosen during implementation so long as they preserve the schema and service boundaries described here.
- Background scheduling may use a lightweight in-process mechanism in MVP provided execution state is persisted in PostgreSQL.

## 6. Validation Plan
Because this task is documentation-only, validation for this artifact is limited to planning completeness and alignment checks.

Planned validation for the document:
- confirm alignment with the MVP product spec
- confirm alignment with the technical design data model and service boundaries
- confirm milestone plan matches the architecture implementation plan sequence
- confirm the plan preserves the local-first / AWS-ready boundary
- confirm no backend scope beyond approved MVP requirements has been introduced

Planned validation once implementation begins:
- migration and schema validation
- adapter contract test execution
- ingestion integration testing with fixtures
- classification rule and evidence validation
- digest and reminder generation tests
- source health and run diagnostics verification
