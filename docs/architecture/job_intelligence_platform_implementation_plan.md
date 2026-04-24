# Job Intelligence Platform MVP Implementation Plan

## Feature Overview
This plan translates the MVP product specification into an implementation sequence for a single-user FastAPI + Jinja + PostgreSQL application. It is organized to reduce downstream ambiguity, preserve architectural flexibility for later AWS migration, and ensure the end-to-end MVP workflow is delivered incrementally.

## Product Requirements Summary
- Deliver the complete MVP workflow from source onboarding through application tracking.
- Prioritize reliable support for Greenhouse, Lever, common ATS patterns, and 3-5 custom adapters.
- Ensure classification is explainable, deterministic, and auditable.
- Deliver operations visibility and local-friendly scheduling/notifications as part of MVP, not a later enhancement.

## Scope

### MVP Delivery Scope
- Source management
- Connector framework and initial adapters
- Ingestion, normalization, deduplication
- Classification engine and evidence capture
- Dashboard and job detail UI
- Manual keep/save and tracking statuses
- Daily digest and reminders
- Source health and operations UI
- Basic observability, testing, and implementation documentation

### Later-Phase Scope
- Broader ATS coverage
- Advanced duplicate resolution UX
- Snooze/suppress reminder UX
- Hosted/AWS deployment implementation
- Auth and multi-user features

## Architecture Overview
Implementation should follow a modular monolith structure with five major workstreams:
1. Platform foundation
2. Source ingestion
3. Classification and workflow state
4. User-facing web experience
5. Scheduling, notifications, and operations

Each workstream should expose clear service boundaries so the application can later evolve from local background execution to AWS-managed scheduling and workers.

## System Components

### Workstream A: Platform Foundation
- App bootstrap and configuration loading
- PostgreSQL integration and migrations
- Base persistence/repository layer
- Template layout and navigation shell
- Structured logging and run/error conventions

### Workstream B: Source Connectors and Ingestion
- Source CRUD and CSV import
- Adapter contract and shared parsing utilities
- Greenhouse connector
- Lever connector
- Common ATS connectors
- Custom company connectors
- Ingestion orchestration and run history

### Workstream C: Classification and Tracking
- Canonical job model
- Deduplication and update handling
- Rules engine and evidence capture
- Automated decision persistence
- Manual keep/save behavior
- Tracking status updates and history

### Workstream D: Web UI
- Dashboard
- Job list/detail and transparency view
- Source management pages
- Source operations pages
- Digest/reminders pages

### Workstream E: Scheduling, Notifications, and Ops
- Local scheduler
- Manual/scheduled execution interoperability
- Daily digest generation
- Reminder generation
- Health state computation
- Operational diagnostics views

## Data Models and Storage Design

### Minimum Schema Delivery Order
Implement schema in this dependency order:
1. `sources`
2. `source_runs`
3. `job_postings`
4. `job_source_links`
5. `job_decisions`
6. `job_decision_rules`
7. `job_tracking_events`
8. `digests`
9. `digest_items`
10. `reminders`

### Schema Implementation Guidance
- Add summary columns required for dashboard reads only after authoritative history tables are defined.
- Add indexes early for likely filter patterns:
  - source active/health lookups
  - job bucket and recency
  - job tracking status
  - current decision lookup
  - source run recency
- Store enough raw payload data to support debugging connector issues.

## API Contracts

### Delivery Principle
Implement HTML-first routes first, then add JSON endpoints only where they simplify UX or testing.

### Initial Route Delivery Order
1. `GET /`
2. `GET/POST /sources`
3. `GET/POST /sources/import`
4. `POST /sources/{id}/run`
5. `GET /jobs`
6. `GET /jobs/{id}`
7. `POST /jobs/{id}/keep`
8. `POST /jobs/{id}/tracking-status`
9. `GET /ops/sources`
10. `GET /ops/runs`
11. `GET /digest/latest`
12. `GET /reminders`

### Contract Stability Guidance
- Keep route handlers thin and domain-service-driven.
- Define view models separate from ORM/persistence models.
- Treat CSV import and ingestion triggers as domain commands with explicit results.

## Frontend / Client Impact

### Recommended UI Delivery Order
1. Shared layout, nav, and flash/error messaging
2. Source list and manual source creation form
3. CSV import page with row-level validation feedback
4. Dashboard summary cards and recent jobs list
5. Job detail page with transparency blocks
6. Tracking status controls and keep/save actions
7. Source ops/health page
8. Digest and reminders pages

### UI Assumptions
- Jinja templates remain the primary rendering layer.
- JavaScript should be optional and limited to UX enhancements.
- UI labels must clearly separate:
  - automated bucket
  - score
  - evidence
  - manual keep/save state
  - tracking status

## Backend Logic / Service Behavior

### Recommended Service Delivery Order
1. Source validation service
2. Adapter registry and contract
3. Ingestion orchestrator
4. Normalization service
5. Deduplication service
6. Classification service
7. Tracking workflow service
8. Digest service
9. Reminder service
10. Health evaluation service

### Dependency Order Notes
- Do not start UI detail pages before canonical job and decision models exist.
- Do not finalize digest/reminder logic before tracking and recency semantics are defined.
- Do not expand adapters until adapter contract tests pass for Greenhouse and Lever.

## File / Module Structure
Recommended repo/app structure:

```text
app/
  main.py
  config/
  web/
    routes/
    templates/
    forms/
    view_models/
  domain/
    sources/
    ingestion/
    jobs/
    classification/
    tracking/
    notifications/
    operations/
  adapters/
    base/
    greenhouse/
    lever/
    common_patterns/
    custom/
  persistence/
    models/
    repositories/
    migrations/
  scheduler/
  observability/
tests/
  unit/
  integration/
  adapter_contract/
  end_to_end/
docs/
  architecture/
```

Implementation guidance:
- Organize by domain responsibility, not technical layer alone.
- Keep one adapter module per source family/custom source.
- Store classification rules/config in a location that can be versioned and tested.

## Security and Access Control
- Default bind to localhost.
- No authentication in MVP local mode.
- Validate CSV and sanitize rendered source/job content.
- Keep future auth insertion points clear by centralizing request/session assumptions in web layer only.

## Reliability / Operational Considerations
- Every ingestion run must create a persisted run record.
- Every scheduled task must be manually triggerable.
- Scheduled execution must avoid overlapping runs for the same source.
- Failed sources must not block healthy sources.
- Health warnings must include empty-result anomaly detection.
- Tracked jobs must remain visible if sources fail or jobs disappear upstream.

## Dependencies and Constraints

### Delivery Dependencies
- Confirmed list of common ATS patterns / adapter keys.
- Confirmed list of 3-5 custom adapters.
- Reminder threshold defaults.

### Constraint Handling
- Connector breadth must not compromise reliability of core source families.
- Classification logic must remain explainable even if coverage is imperfect.
- Local scheduler assumptions should not leak into core domain services.
- CSV import should remain create-only unless product explicitly approves update-existing behavior later.

## Assumptions
- One engineer or a small team can deliver this as a modular monolith without separate service ownership.
- In-app digest/reminder rendering is sufficient for MVP acceptance if optional email/file delivery is deferred.
- Common ATS pattern support will be explicitly bounded to named patterns.
- Manual keep/save will be treated as a first-class workflow action from initial implementation.
- Manual keep/save initializes tracking status `saved` only when no tracking status exists yet.
- The baseline CSV schema is `name`, `source_type`, `base_url`, `external_identifier`, `adapter_key`, `company_name`, `is_active`, and `notes`, with source-type-specific requiredness.

## Risks / Open Questions

### Risks
- Connector fragility can consume disproportionate engineering time.
- Rules tuning may require multiple iterations to avoid over-rejection.
- Reminder and digest expectations may be underspecified until concrete UX is exercised.
- Local background execution can be hard to validate unless manual triggering is built early.

### Open Questions
- What reminder thresholds are acceptable defaults for saved and applied jobs?
- What exact evidence threshold is expected when text is sparse?

## Implementation Notes for Downstream Agents
- Build contract tests for adapters before expanding source support.
- Use fixture-based parsing tests for every supported connector.
- Persist decision history and workflow history from the first iteration; avoid shortcuts that collapse them into one status field.
- Implement dashboard read models only after authoritative write models and services are stable.
- Make source health visible from the moment ingestion exists.
- Prefer shipping a narrow but stable set of common/custom adapters over broad but brittle support.

## Milestone-Based Delivery Plan

### Milestone 0: Foundation and Scaffolding
Objective: establish app skeleton and persistence foundation.

Deliverables:
- FastAPI app bootstrap
- Jinja template base layout
- PostgreSQL connectivity and migration framework
- Base config loading
- Structured logging setup
- Initial schema for sources, source_runs, job_postings, job_source_links

Acceptance checkpoint:
- App starts locally.
- Database migrations run cleanly.
- Basic placeholder pages render.
- Logging and configuration are environment-driven.

### Milestone 1: Source Management MVP
Objective: allow user to create and import sources safely.

Deliverables:
- Source list page
- Manual source creation form
- CSV upload/import workflow
- Row-level validation and duplicate detection feedback
- Source persistence and edit-safe display

Acceptance checkpoint:
- User can create at least one valid source manually.
- User can import at least one valid source by CSV.
- Invalid rows are reported clearly and not silently persisted.
- Duplicate candidate sources are surfaced to the user.

### Milestone 2: Connector Framework + First-Class ATS Ingestion
Objective: establish reusable adapter architecture and ingest from Greenhouse and Lever.

Deliverables:
- Adapter contract and registry
- Shared fetch/parsing utilities
- Greenhouse connector
- Lever connector
- Source run creation/finalization
- Canonical normalization flow

Acceptance checkpoint:
- Manual run succeeds for representative Greenhouse source.
- Manual run succeeds for representative Lever source.
- Jobs are stored with source attribution and raw payload snapshot.
- Failed runs create visible diagnostic records.

### Milestone 3: Deduplication + Classification Core
Objective: make ingested jobs actionable.

Deliverables:
- Dedupe keys and upsert semantics
- Current-state projection on jobs
- Rules engine with score, bucket, and rule detail persistence
- Sponsorship ambiguity handling to `review`
- Decision evidence snippet extraction

Acceptance checkpoint:
- Every ingested job gets a persisted current decision.
- Decision includes bucket, score, matched/negative rules, and evidence where text exists.
- Sponsorship ambiguity does not auto-reject.
- Strong duplicate cases merge correctly with preserved provenance.

### Milestone 4: Dashboard + Job Review Workflow
Objective: deliver usable job review experience.

Deliverables:
- Dashboard landing page
- Job list filters by bucket and tracking status
- Job detail transparency page
- Manual keep/save action
- Tracking status update flow

Acceptance checkpoint:
- User can review matched, review, and rejected jobs from dashboard.
- User can inspect transparency details for a job.
- User can keep/save a rejected job without losing automated classification.
- User can update tracking statuses across MVP status set.

### Milestone 5: Common ATS Patterns + Custom Adapters
Objective: expand beyond Greenhouse and Lever while controlling scope.

Deliverables:
- Named common pattern connector implementations
- 3-5 custom company adapters
- Pattern-specific tests/fixtures
- Unsupported-source messaging improvements

Acceptance checkpoint:
- Confirmed common pattern sources ingest successfully.
- Confirmed custom adapters ingest successfully.
- Unsupported direct pages are rejected or flagged explicitly, not treated as supported.

### Milestone 6: Digest, Reminders, and Scheduling
Objective: deliver recurring workflow support.

Deliverables:
- Local scheduler abstraction
- Daily ingestion schedule
- Daily digest generation and persistence
- Reminder generation for saved inactivity and applied follow-up
- Digest/reminders UI pages

Acceptance checkpoint:
- System can generate a daily digest of new matched + review jobs.
- System can generate reminders for saved and applied jobs per configured thresholds.
- Scheduled flows can also be manually triggered for verification.

### Milestone 7: Source Health, Ops, and Hardening
Objective: make the MVP operable and trustworthy.

Deliverables:
- Source ops overview page
- Run history and run detail views
- Health state computation (`healthy`, `warning`, `error`)
- Empty-result warning logic
- Failure messaging polish
- End-to-end validation across supported sources

Acceptance checkpoint:
- Source health shows last run, success/failure, jobs fetched, and empty-result warnings.
- Broken sources are diagnosable from UI.
- Full MVP success workflow works end to end.

## Engineering Workstreams

### Workstream 1: Domain and Persistence
- Schema design
- Migrations
- Repositories
- Summary/read-model projections

### Workstream 2: Connectors and Ingestion
- Adapter contract
- Shared parser helpers
- Connector implementations
- Ingestion orchestration

### Workstream 3: Classification and Workflow Logic
- Rules configuration
- Evidence extraction
- Bucketing logic
- Manual keep/save and tracking separation

### Workstream 4: Web Experience
- Templates
- Route handlers
- Forms and validation
- View models

### Workstream 5: Background Jobs and Operations
- Scheduler abstraction
- Digest/reminder services
- Health evaluation
- Logging/run diagnostics

## Dependency Order

### Critical Path
1. Foundation scaffolding
2. Core schema
3. Source management
4. Adapter contract
5. Greenhouse/Lever ingestion
6. Normalization + dedupe
7. Classification engine
8. Dashboard/job review UI
9. Tracking actions
10. Digest/reminders
11. Common/custom adapters
12. Ops hardening

### Parallelizable Work
- UI shell can proceed alongside persistence setup.
- Classification rule drafting can proceed while Greenhouse/Lever connectors are being built.
- Ops views can start once run records exist.
- Custom adapter fixture preparation can proceed before implementation.

## Testing and Validation Strategy

### Test Layers
- **Unit tests**: normalization helpers, rule evaluation, health logic, reminder eligibility.
- **Adapter contract tests**: every adapter must satisfy shared behaviors and error semantics.
- **Integration tests**: DB persistence, ingestion orchestration, route/service interactions.
- **Fixture tests**: saved HTML/API payload samples for Greenhouse, Lever, common patterns, and each custom adapter.
- **End-to-end tests**: source creation/import -> run ingestion -> classification -> dashboard -> tracking -> digest/reminder visibility.

### Validation Priorities
1. Source onboarding validation correctness.
2. Connector stability on representative fixtures.
3. Deduplication correctness for known duplicate scenarios.
4. Classification transparency completeness.
5. Manual keep/save and tracking separation.
6. Health warning correctness for zero-result and failed runs.
7. Digest/reminder inclusion rules.

### MVP Test Data Guidance
- Maintain source fixtures for each supported adapter.
- Include ambiguous sponsorship examples.
- Include obvious role matches and obvious mismatches.
- Include duplicate-across-source examples.
- Include stale/removed source scenarios.

## MVP vs Later-Phase Boundaries

### Strict MVP
- Local single-user mode
- No auth
- FastAPI + Jinja UI
- PostgreSQL
- Greenhouse + Lever + bounded pattern/custom connectors
- Deterministic rules engine
- In-app digest/reminders acceptable if delivery channel is not finalized
- Source health UI

### Later Phase
- AWS deployment implementation
- Managed queues/workers/scheduler
- Email/push delivery sophistication
- Broader ATS support
- Duplicate review UX
- Reminder snooze/suppression UX
- Multi-user/auth
- Advanced analytics and collaboration
