# Product Specification

## 1. Feature Overview
The Job Intelligence Platform MVP is a single-user, personal web application for discovering, filtering, reviewing, and tracking relevant job opportunities. The product ingests job postings from supported hiring sources, classifies them into actionable buckets, presents transparent scoring and evidence, enables manual overrides, and supports lightweight application tracking and reminders.

The MVP is intended for local/self-hosted use first, with product decisions made to support a clean transition to AWS-hosted deployment later.

## 2. Problem Statement
Job searching across multiple hiring systems is fragmented, repetitive, and difficult to manage consistently. Relevant roles are spread across Greenhouse, Lever, and direct company career pages, with inconsistent job descriptions and unclear sponsorship details. The user needs a system that:
- centralizes job discovery from prioritized sources
- filters roles against explicit preferences and constraints
- avoids silent black-box recommendations by showing why jobs were matched, rejected, or flagged for review
- supports manual judgment when automated decisions are uncertain
- helps the user track next actions and maintain application follow-through

This matters because the user is targeting a focused set of roles and geographies, needs sponsorship, and wants to reduce wasted time reviewing clearly irrelevant postings while still catching ambiguous but potentially viable jobs.

## 3. User Persona / Target User
### Primary User
- A single individual job seeker using the system privately
- Technical background with strong understanding of software roles
- Searching primarily for:
  - Python backend roles
  - Software Development Engineer in Test (SDET) roles
  - QA automation roles
  - test infrastructure roles
  - developer productivity roles
- Prefers global remote opportunities first and Spain-based opportunities second
- Requires employer sponsorship; ambiguous sponsorship status should not be auto-rejected

### Usage Context
- Uses the app regularly to review new opportunities and manage active applications
- Wants a clean dashboard with low-friction workflows
- Is comfortable onboarding sources manually or via CSV
- Needs confidence in why the system made a recommendation

## 4. User Stories
- As a job seeker, I want to add job sources quickly, so that I can aggregate opportunities from multiple hiring systems in one place.
- As a job seeker, I want to upload sources by CSV or enter them manually, so that I can onboard targets in the most convenient format.
- As a job seeker, I want jobs fetched from Greenhouse, Lever, and selected direct company pages, so that I do not need to monitor each site individually.
- As a job seeker, I want roles automatically classified into matched, review, or rejected, so that I can focus attention efficiently.
- As a job seeker, I want sponsorship ambiguity to default to review, so that I do not miss potentially viable roles.
- As a job seeker, I want to see matched rules, rejected rules, evidence snippets, and final score, so that I can trust and audit the classification.
- As a job seeker, I want to manually keep or save a job regardless of automated classification, so that my own judgment overrides the system when needed.
- As a job seeker, I want a clean dashboard showing important job and application views, so that I can work from a single command center.
- As a job seeker, I want a daily digest of new matched and review jobs, so that I can stay current without opening each source manually.
- As a job seeker, I want reminders for saved jobs not acted on and applied jobs needing follow-up, so that I do not lose momentum.
- As a job seeker, I want to track application status from saved through offer, so that I can manage my pipeline end to end.
- As a job seeker, I want source health indicators, so that I can identify broken or stale data feeds quickly.

## 5. Goals / Success Criteria
### Product Goals
- Enable the complete v1 workflow: add source -> ingest jobs -> classify -> view dashboard -> get digest -> track applications.
- Reduce manual effort required to find relevant jobs across multiple ATS sources.
- Make automated decisions explainable and easy to override.
- Provide enough operations visibility to manage source reliability without engineering intervention.

### Measurable / Observable Success Criteria
- The user can onboard at least one source through CSV and at least one source through manual entry.
- The system can ingest jobs from Greenhouse, Lever, and supported direct ATS/company pages in the MVP source list.
- Every classified job shows bucket, final score, matched rules, rejected rules, and evidence from the job text.
- Jobs with unclear sponsorship language are placed in review, not rejected.
- The user can manually save or keep any job regardless of automated classification.
- The daily digest contains new matched and review jobs from the previous ingestion cycle.
- The user can assign and update tracking statuses: saved, applied, interview, rejected, offer.
- The system generates reminders for saved jobs with no action and applied jobs requiring follow-up.
- The source operations view shows last run, success/failure state, jobs fetched count, and empty-result warnings.

## 6. Feature Scope
### In Scope
- Single-user personal job intelligence web app
- Local/self-hosted deployment as primary usage model for MVP
- Product structure that can transition cleanly to AWS later
- Source onboarding via CSV upload and manual form input
- Source support for:
  - Greenhouse
  - Lever
  - common ATS/direct career page patterns
  - 3-5 hand-picked custom direct adapters in MVP
- Job ingestion from configured sources
- Automated job classification into matched, review, rejected
- Transparent scoring and rule evidence display
- Manual override to preserve or save jobs regardless of automated outcome
- Clean dashboard UI
- Daily digest for new matched and review jobs
- Reminder system for saved and applied jobs
- Basic application tracking statuses: saved, applied, interview, rejected, offer
- Source operations and health visibility

### Out of Scope
- Multi-user support
- Public/distributed SaaS release
- Full marketplace or broad user administration capabilities
- Support for all possible ATS vendors in MVP
- Large-scale crawler coverage of arbitrary company websites
- Automated job application submission
- Resume customization or cover letter generation
- Advanced collaboration, sharing, or recruiter communication tools
- Complex analytics beyond MVP workflow visibility
- Full cloud-native AWS deployment in v1

## 7. Functional Requirements
### A. Source Management
1. The system must allow the user to create new sources through manual form input.
2. The system must allow the user to upload sources through CSV.
3. Source configuration must capture enough information to identify source type and fetch jobs from that source.
4. The product must support source types for Greenhouse, Lever, common ATS/direct page patterns, and a limited set of custom adapters.
5. The source management experience must distinguish between supported standard source types and custom source types.
6. The system must persist source records for repeated ingestion runs.
7. The system must expose source health information including:
   - last run timestamp
   - latest run status (success/failure)
   - number of jobs fetched on latest run
   - warning when a run returns zero jobs unexpectedly or repeatedly

#### MVP CSV Import Assumptions
- CSV import is create-oriented for MVP: it creates new sources and reports duplicates/skips; it does not update existing source records in place.
- Baseline CSV columns for MVP are:
  - `name` (required)
  - `source_type` (required; `greenhouse`, `lever`, `common_pattern`, or `custom_adapter`)
  - `base_url` (required)
  - `external_identifier` (required when the source family needs a board token, company slug, or equivalent locator)
  - `adapter_key` (required for `common_pattern` and `custom_adapter`)
  - `company_name` (optional)
  - `is_active` (optional; defaults to active)
  - `notes` (optional)
- Validation must be row-specific and allow mixed valid/invalid rows in one import.

#### Source Management Acceptance Criteria
- A user can add a source via manual form and see it listed as an active configured source.
- A user can upload a valid CSV and have sources created from its rows.
- Invalid or incomplete source input is flagged clearly and does not create a broken source silently.
- Each source record shows source type and health summary.
- Empty-result runs are surfaced as warnings in the UI.

### B. Data Ingestion
1. The system must fetch job postings from configured sources.
2. The system must support ingestion from Greenhouse and Lever as first-class MVP sources.
3. The system must support direct ATS/company pages via common patterns first.
4. The system must support only 3-5 hand-picked custom direct adapters in MVP.
5. Ingestion must normalize fetched jobs into a consistent internal job record for downstream classification and display.
6. Each ingested job must retain source attribution.
7. The system must store enough job content to support evidence-based classification and UI review.
8. The system must make newly ingested jobs available for classification without requiring manual data cleanup.

#### Data Ingestion Acceptance Criteria
- Jobs fetched from any supported source type appear in a normalized format in the application.
- Each ingested job is linked to the source that produced it.
- Job title, company/source context, URL/reference, and text content required for review are available after ingestion.
- Unsupported direct pages are not presented as supported unless a matching common pattern or custom adapter exists.

### C. Classification and Decisioning
1. The system must classify each ingested job into one of three MVP buckets:
   - matched
   - review
   - rejected
2. The classification model must reflect target role preferences:
   - Python backend
   - SDET
   - QA automation
   - test infrastructure
   - developer productivity
3. The classification model must reflect geographic preferences:
   - global remote prioritized
   - Spain secondary
4. Sponsorship handling must follow this rule: if sponsorship availability is unclear, the job defaults to review.
5. The system must support transparent scoring for each job.
6. The transparency view must include:
   - matched rules
   - rejected rules
   - evidence snippets from job text
   - final score
7. The system must preserve bucket assignments even when manual user actions are taken, while allowing the user to keep/save the job.
8. The product must be structured so classification buckets can evolve in future versions without redefining the entire workflow.

#### Classification Acceptance Criteria
- Every ingested job receives one of the three MVP buckets.
- Every classified job displays a final score and the reasons contributing to that decision.
- At least one evidence snippet is shown for each rule-based conclusion when source text supports it.
- Jobs with explicit mismatch conditions may be rejected when rules support rejection.
- Jobs with unclear sponsorship status are assigned to review rather than rejected.
- The user can save/keep a rejected or review job without removing the original automated classification record.

### D. Dashboard and Review Experience
1. The product must provide a clean dashboard as the primary landing experience.
2. The dashboard must allow the user to review jobs by classification bucket.
3. The dashboard must provide visibility into newly matched and review jobs.
4. The dashboard must support access to job detail views that show classification transparency.
5. The dashboard must support access to tracking status information.
6. The dashboard must not require navigating source-by-source to see prioritized opportunities.

#### Dashboard Acceptance Criteria
- The landing experience presents summary views for matched, review, and rejected jobs.
- The user can open a job and inspect decision transparency details.
- The user can identify newly relevant jobs without visiting each configured source.
- The UI remains focused and uncluttered rather than exposing unnecessary administration-first workflows.

### E. Manual Override and Job Retention
1. The user must be able to manually save or otherwise keep any job regardless of automated classification.
2. Manual override must be available from job review surfaces, not hidden in an admin-only area.
3. Manual user intent must prevent accidental loss of jobs that the user wants to monitor.
4. The product must distinguish between automated classification outcome and user-managed tracking status.
5. Manual keep/save is a retention action and must not replace the stored automated classification.

#### Manual Override Acceptance Criteria
- A user can save a job that was classified as rejected.
- Saving or keeping a job does not erase the original classification bucket or decision explanation.
- Saved jobs remain visible for later action and reminders.

### F. Application Tracking
1. The system must support the following MVP tracking statuses:
   - saved
   - applied
   - interview
   - rejected
   - offer
2. The user must be able to assign and update a tracking status for a job.
3. Tracking status must be separate from classification bucket.
4. The dashboard must allow the user to review jobs by tracking status.

#### Tracking Acceptance Criteria
- A user can move a job from saved to applied to interview, or to rejected/offer as appropriate.
- Classification bucket and tracking status can coexist without ambiguity.
- The user can identify which saved jobs still need action.

### G. Notifications: Daily Digest and Reminders
1. The system must provide a daily digest.
2. The daily digest must include newly identified matched jobs.
3. The daily digest must include newly identified review jobs.
4. The system must provide reminders for saved jobs that have not been acted on.
5. The system must provide reminders for applied jobs that require follow-up.
6. Notification content must be aligned to actionability rather than raw system logs.

#### Notification Delivery Assumptions for MVP
- In-app digest and reminder views are the required MVP delivery mechanism.
- Optional local email or file export may be added later behind configuration, but is not required for MVP acceptance.
- Digest eligibility should be based on jobs that became newly eligible since the previous digest window.
- Reminder eligibility should be based on tracking-state timestamps, not classification bucket alone.

#### Notification Acceptance Criteria
- The daily digest includes only new jobs in matched and review buckets for the digest period.
- Saved jobs with no user action are included in reminder outputs when reminder conditions are met.
- Applied jobs requiring follow-up are included in reminder outputs when reminder conditions are met.

### H. Operations and Reliability Visibility
1. The product must provide a source operations UI.
2. The source operations UI must display health information per source.
3. Health information must include:
   - last run
   - success/failure
   - jobs fetched
   - empty-result warnings
4. The operations experience must help the user diagnose when a source is stale, broken, or returning no jobs.

#### Operations Acceptance Criteria
- Each configured source exposes the required health fields.
- A failed source run is visibly distinguishable from a successful run.
- Empty-result conditions are flagged as warnings rather than hidden.

### I. Workflow State Separation
1. The system must preserve three distinct concepts throughout the MVP:
   - automated classification bucket
   - manual keep/save retention intent
   - tracking status
2. Manual keep/save may initialize tracking to `saved` when no tracking status exists yet.
3. Manual keep/save must not overwrite an existing tracking status.
4. Reminder eligibility must be driven by tracking state and workflow timestamps, not bucket alone.

## 8. Acceptance Criteria
- The user can onboard sources using both CSV upload and manual entry in the MVP.
- The system supports Greenhouse, Lever, and defined direct ATS/company page strategies in the MVP.
- Jobs are ingested, normalized, and visible in the app after a source run.
- Every job is classified into matched, review, or rejected.
- Sponsorship ambiguity defaults to review.
- Every classification exposes matched rules, rejected rules, evidence snippets, and final score.
- The user can manually keep/save any job regardless of automated classification.
- The dashboard provides a clean overview of prioritized jobs and tracking state.
- The daily digest includes new matched and review jobs.
- Reminders cover both saved jobs not acted on and applied jobs needing follow-up.
- Tracking supports saved, applied, interview, rejected, and offer statuses.
- Source operations show last run, success/failure, jobs fetched, and empty-result warnings.
- The full v1 success flow is possible end to end: add source -> ingest jobs -> classify -> view dashboard -> get digest -> track applications.

## 9. Edge Cases
- A source is configured correctly but returns zero jobs because the company has no openings.
- A source returns zero jobs because parsing failed; the system must not silently treat this as normal.
- A direct ATS/company page partially matches a common pattern but lacks expected fields.
- A job posting contains ambiguous or contradictory sponsorship language.
- A job is a strong role match but location or sponsorship details are missing.
- A job is a poor role match but the user wants to keep it manually.
- A source is uploaded twice through CSV, creating potential duplicate source records.
- A job appears across multiple sources or URLs with overlapping content.
- A job posting is updated after first ingestion.
- A job is removed from the external source after being saved or applied.
- A job contains insufficient text to support strong evidence snippets.
- A reminder condition triggers for a job that the user already decided to ignore temporarily.

## 10. Constraints
### Technical Constraints
- MVP is single-user only.
- MVP is local/self-hosted first.
- Product structure should support clean migration to AWS later, but AWS deployment is not required in v1.
- Source coverage is intentionally limited to Greenhouse, Lever, common ATS patterns, and only 3-5 custom adapters.

### UX Constraints
- UI should be a clean dashboard-oriented experience.
- Source operations must surface health clearly without requiring technical logs to understand source state.
- Classification explanations must be easy to inspect and not hidden behind opaque scoring.

### Business / Product Rules
- Primary target opportunities are global remote; Spain is secondary.
- Sponsorship is required by the user.
- If sponsorship is unclear, the default automated decision must be review.
- Automated classification must not prevent user retention of a job.

## 11. Dependencies
- Availability and accessibility of Greenhouse and Lever job listings
- Stability of supported common ATS/direct page structures
- Availability of source data sufficient for evidence extraction and classification
- Defined CSV input format for source onboarding using the MVP baseline schema in this document unless explicitly revised
- Defined list of 3-5 hand-picked custom direct adapters for MVP
- Notification delivery mechanism for digest and reminders
- Persistent data storage for sources, jobs, classifications, and tracking statuses

## 12. Assumptions
- The MVP will be used by one person only, with no concurrent multi-user requirements.
- The user is willing to configure and maintain their own local/self-hosted environment.
- Greenhouse and Lever represent a meaningful portion of target job opportunities for the user.
- Common ATS patterns plus 3-5 custom adapters are sufficient to validate the direct-source strategy in MVP.
- A rules-based or similarly explainable decision model is preferable to opaque ranking for the MVP.
- Digest and reminder functionality can be delivered in-app in a way that is practical for a local/self-hosted deployment.
- The user prefers incomplete but explainable coverage over broad but unreliable scraping.
- Common ATS support is a named allowlist of explicitly implemented patterns, not open-ended support for arbitrary direct pages.
- Local scheduling may use an in-process scheduler for MVP as long as run state is persisted and manually triggerable.
- Manual keep/save is separate from automated bucket and may default a job into tracking status `saved` only when no tracking status exists yet.

## 13. Open Questions
- Which specific direct ATS/common page patterns are included in MVP support?
- Which 3-5 custom direct adapters are prioritized for MVP?
- How should duplicate jobs across sources be handled from the user’s perspective?
- What exact digest run time should be used in local deployments?
- What exact timing rules should trigger reminders for saved jobs and applied follow-ups?
- What minimum evidence threshold is required before showing a rule as supported by job text?
- How should jobs with stale or removed source URLs be displayed once they are already tracked?

## Additional Product Sections Requested for Engineering Handoff

### Problem Summary
The user currently needs to search across multiple fragmented hiring systems for a narrow set of technical roles while balancing remote geography preferences and sponsorship needs. Manual review is time-consuming, sponsorship signals are often unclear, and there is no single place to discover, explain, prioritize, and track opportunities.

### Product Vision
Create a personal job intelligence web app that continuously gathers relevant jobs from prioritized sources, explains why each job is or is not a fit, supports user judgment through overrides, and helps the user move from discovery to application tracking in one workflow.

### Goals and Non-Goals
#### Goals
- Centralize relevant job discovery
- Prioritize opportunities with transparent, auditable logic
- Preserve ambiguous but potentially viable opportunities through review-first handling
- Support ongoing application management through dashboard, digest, and reminders

#### Non-Goals
- Building a consumer-scale job board
- Supporting teams, recruiters, or public users
- Supporting every ATS or arbitrary website in MVP
- Replacing the user’s judgment with opaque automation

### MVP Scope and Out-of-Scope Summary
#### MVP Scope
- Single-user personal web app
- Supported source onboarding and ingestion
- Transparent classification and evidence display
- Manual keep/save override
- Dashboard, digest, reminders, and tracking
- Source health and operations visibility

#### Out-of-Scope Summary
- Multi-user accounts
- public launch
- broad crawler ecosystem
- auto-apply workflows
- advanced analytics and collaboration

### End-to-End User Workflow
1. User adds one or more sources using manual entry or CSV upload.
2. User runs or reviews ingestion for configured sources.
3. System fetches and normalizes jobs from supported sources.
4. System classifies jobs into matched, review, or rejected.
5. System shows transparent reasoning with matched rules, rejected rules, evidence, and final score.
6. User reviews jobs from the dashboard, focusing first on matched and review.
7. User manually saves/keeps any job worth monitoring, regardless of automated bucket.
8. User updates tracking statuses as the application progresses.
9. System sends daily digest containing new matched and review jobs.
10. System sends reminders for saved jobs needing action and applied jobs needing follow-up.
11. User monitors source health and addresses broken or stale sources when warnings appear.

### Decision Model and Transparency Requirements
- The decision model must produce a bucket outcome and final score for every job.
- The decision model must expose both positive and negative reasoning, not only the final result.
- Transparency must include:
  - which rules matched
  - which rules triggered rejection or negative scoring
  - which snippets from the job text support those rules
  - what final score was assigned
- Sponsorship ambiguity is a special-case rule: ambiguous or missing sponsorship data cannot auto-reject a job and must result in review unless stronger explicit rejection criteria override for unrelated reasons that the product owner later confirms.
- The product must preserve separation between automated decision and user intent.

### Data Source Strategy (Product Perspective)
#### Priority Order
1. Greenhouse
2. Lever
3. Common ATS/direct career page patterns
4. 3-5 hand-picked custom direct adapters

#### Product Rationale
- Greenhouse and Lever provide immediate value because they cover a significant set of modern hiring workflows.
- Common ATS/direct pattern support expands coverage without requiring a bespoke adapter for every company.
- Limiting custom direct adapters in MVP keeps scope controlled while validating high-value targets.
- CSV and manual source onboarding allow the user to incrementally expand coverage without waiting for a complex integration interface.

### Success Criteria and Measurable Outcomes
- The user can configure sources and successfully ingest jobs without engineering assistance.
- The user receives actionable matched and review job lists on a recurring basis.
- The user can understand why a job was bucketed without inspecting raw source content manually.
- The user can maintain an application pipeline from saved to offer within the same product.
- The user can detect source failures or empty feeds through the operations UI.

### Risks
- Direct ATS/company page variability may reduce reliability of common-pattern support.
- Sponsorship language may be too inconsistent for precise automated determination.
- Local/self-hosted notification workflows may be less reliable or convenient than cloud delivery.
- Overly aggressive rejection logic could hide viable jobs if transparency and review defaults are not handled carefully.

### Prioritized Release Scope Suitable for Engineering Handoff
#### P0 - Required for MVP
- Source onboarding via manual form
- Source onboarding via CSV upload
- Greenhouse ingestion
- Lever ingestion
- Common ATS/direct pattern ingestion for selected supported patterns
- 3-5 custom direct adapters
- Normalized job storage
- Classification into matched/review/rejected
- Sponsorship ambiguity default to review
- Transparent reasoning: matched rules, rejected rules, evidence snippets, final score
- Clean dashboard with classification views
- Manual keep/save override
- Tracking statuses: saved, applied, interview, rejected, offer
- Daily digest with new matched + review jobs
- Reminders for saved inactivity and applied follow-up
- Source operations UI with last run, success/failure, jobs fetched, empty-result warning

#### P1 - Important but Deferrable if Needed
- More refined dashboard summaries and filtering
- Better duplicate handling and stale job presentation
- Reminder suppression/snooze behavior
- Richer source validation during onboarding

#### P2 - Future Evolution, Not MVP
- Multi-user support
- AWS-native deployment and hosted operations
- Broader ATS coverage
- Collaboration and sharing
- Advanced analytics and optimization features
