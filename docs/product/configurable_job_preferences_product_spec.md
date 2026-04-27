# Product Specification

## 1. Feature Overview

Create a configurable Job Preferences feature at `/job-preferences` that lets the user define the core criteria used for job filtering, ranking, matching, and classification.

This HITL correction supersedes the prior all-fields-first setup experience. First-time setup must use a simple wizard-style flow for job categories, location, work arrangement, and visa sponsorship. Advanced keyword criteria remain in scope only as optional secondary settings after setup is complete.

Preferences are persisted only in browser `localStorage`. When backend classification or reclassification is required, the browser sends the active preference payload with the request. The backend must not persist preferences.

## 2. Problem Statement

The prior `/job-preferences` setup exposed implementation-level keyword and classification criteria during first-time onboarding. HITL validation determined this was too complex for users. Users need a guided setup that captures high-level job-search intent without requiring them to understand role-family keywords, sponsorship keyword groups, or scoring mechanics.

## 3. User Persona / Target User

- **Primary user:** A job seeker using the platform to identify, rank, review, and track relevant job opportunities.
- **User context:** The current implementation is local/single-user oriented. Preferences are scoped to the current browser/device only.

## 4. User Stories

- As a new job seeker, I want a guided setup wizard, so that I can configure matching criteria quickly without editing advanced keyword rules.
- As a job seeker, I want to select predefined job categories, so that matching reflects my target roles without requiring custom keyword entry.
- As a job seeker, I want to choose countries and work arrangements, so that jobs are filtered and ranked against my location preferences.
- As a job seeker, I want to state whether I require visa sponsorship, so that sponsorship affects matching only when it matters to me.
- As a configured user, I want optional Advanced settings after setup, so that I can refine keyword criteria without making first-time setup complicated.
- As a job seeker, I want saved preferences to persist after refresh, so that I do not need to re-enter them in the same browser.

## 5. Goals / Success Criteria

- First-time `/job-preferences` setup is a four-step wizard, not an all-fields advanced criteria form.
- Setup collects required selections for job categories, location, work arrangement, and visa sponsorship.
- Job categories are selected from predefined options only; no custom/free-text categories are saved.
- Saved wizard selections map to the underlying preference criteria used by classification.
- Preferences are saved in browser `localStorage` and survive refresh in the same browser context.
- Existing active jobs are reclassified immediately after successful Save so filtering/ranking reflects saved criteria.
- Advanced keyword criteria are hidden during first-time setup and available only after setup is complete as a collapsed/secondary section on the same `/job-preferences` page.
- Auth, DynamoDB, cloud/backend preference persistence, custom weights, and unrelated features remain out of scope.

## 6. Feature Scope

### In Scope

- Dedicated `/job-preferences` page.
- Primary navigation item `Job Preferences` after Dashboard and before Jobs.
- First-time four-step wizard:
  1. Job categories.
  2. Location.
  3. Work arrangement.
  4. Visa sponsorship.
- Browser `localStorage` persistence only.
- Per-request submission of active preferences to backend classification/reclassification operations.
- Immediate reclassification of existing active jobs after successful Save.
- Mapping wizard selections to the underlying preference DTO/criteria so existing classification behavior is preserved where possible.
- Optional Advanced settings after setup completion, shown on the same page as collapsed/secondary content.
- Validation for required wizard selections and Advanced keyword normalization.

### Out of Scope

- Authentication.
- AWS DynamoDB or any cloud persistence.
- Backend database/repository persistence for preferences.
- Multi-user account management or server-side per-user preference storage.
- Custom/free-text saved job categories in the first-time wizard.
- Custom scoring weights, custom score deltas, or user-configurable bucket thresholds.
- Preference history, versioning UI, rollback, import, or export.
- New job board/source integrations.
- Unrelated UI redesigns beyond the `/job-preferences` wizard and secondary Advanced settings.

### Future Considerations

- Authenticated per-user persistence.
- AWS DynamoDB-backed preference storage.
- Multi-device preference sync.
- Additional job categories or admin-managed category taxonomy.
- Configurable scoring weights and thresholds after separate product approval.
- Additional preference categories such as salary, employment type, seniority, and excluded companies.

## 7. Functional Requirements

### FR-1: Page access and navigation

The system must provide a dedicated Job Preferences page.

Required placement:
- Route: `/job-preferences`
- Primary navigation label: `Job Preferences`
- Primary navigation order: after Dashboard and before Jobs
- Active navigation key: `job_preferences`

The page must be reachable from primary navigation and missing-preferences redirect flows.

### FR-2: First-time setup wizard replaces all-fields-first setup

When no usable saved preferences exist, `/job-preferences` must show a guided wizard-style setup flow instead of showing all advanced keyword criteria as primary setup fields.

The prior requirement that first-time setup visibly expose every hardcoded criterion as editable fields is superseded. Advanced keyword criteria must be hidden during first-time setup.

### FR-3: Wizard Step 1 — Job categories

Step 1 must let the user select one or more predefined job categories.

Input behavior:
- Provide a search/typeahead field for discovering predefined categories.
- Allow multiple category selections.
- Save predefined category identifiers only.
- Do not save custom/free-text categories.
- If the user types text that does not match a predefined category, it must not become a saved category.

Initial predefined categories:
- Python Backend
- Backend Engineer
- SDET
- QA Automation
- Test Automation
- Test Infrastructure
- Developer Productivity / Developer Experience

### FR-4: Job category mapping to role-family criteria

Selected job categories must map deterministically to role-family keyword criteria while preserving role-family grouping and once-per-family scoring behavior.

Initial mapping:

| Wizard Category | Role Family Key | Role Keywords |
| --- | --- | --- |
| Python Backend | `python_backend` | python backend, python engineer |
| Backend Engineer | `backend_engineer` | backend engineer, backend developer |
| SDET | `sdet` | sdet, software development engineer in test |
| QA Automation | `qa_automation` | qa automation, quality assurance automation |
| Test Automation | `test_automation` | test automation |
| Test Infrastructure | `test_infrastructure` | test infrastructure, testing platform, quality platform |
| Developer Productivity / Developer Experience | `developer_productivity` | developer productivity, developer experience, engineering productivity |

### FR-5: Wizard Step 2 — Location

Step 2 must let the user select one or more countries from a checkbox list.

Initial country list:
- Czechia
- Denmark
- Estonia
- Finland
- France
- Germany
- India
- Ireland
- Japan
- Lithuania
- Netherlands
- Norway
- Poland
- Portugal
- Singapore
- South Korea
- Spain
- Sweden
- Switzerland
- Taiwan
- United Kingdom

Selected countries must map to preferred location criteria. The list may be expanded later through a separate approved change, but first implementation must include at least the countries listed above.

### FR-6: Wizard Step 3 — Work arrangement

Step 3 must let the user select work-arrangement preferences.

Allowed options:
- Remote
- Hybrid
- On-site
- Flexible / Any

Behavior:
- Remote, Hybrid, and On-site are multi-select compatible.
- Flexible / Any is exclusive.
- Selecting Flexible / Any must clear Remote, Hybrid, and On-site.
- Selecting Remote, Hybrid, or On-site must clear Flexible / Any.
- Flexible / Any means no work-arrangement restriction and must not be converted into restrictive matching keywords.

### FR-7: Wizard Step 4 — Visa sponsorship

Step 4 must ask: “I require visa sponsorship”.

Allowed answers:
- Yes
- No

Behavior:
- If Yes, classification should prefer/require jobs with sponsorship-support signals and reject jobs that specifically state sponsorship is not available.
- If No, sponsorship should be neutral: sponsorship text must not increase, decrease, reject, or force review solely because of sponsorship signals.

### FR-8: Setup completion requirements

Setup is complete only after the user saves valid values for all four wizard steps.

Completion requires:
- At least one predefined job category.
- At least one country.
- At least one work-arrangement selection, where Flexible / Any counts as a valid selection.
- An explicit visa sponsorship Yes/No answer.

Defaults may be displayed as recommendations or starting state, but no preferences are active until the user clicks Save and Save succeeds.

### FR-9: Advanced settings after setup

After setup is complete, `/job-preferences` must show the saved wizard preferences as the primary configuration and expose Advanced settings as optional collapsed/secondary content on the same page.

Advanced settings may include the existing underlying keyword criteria used by classification, including:
- Role-family keyword groups.
- Negative role keywords.
- Work arrangement keywords.
- Preferred location keywords.
- Incompatible location keywords.
- Sponsorship supported, unsupported, and ambiguous keywords.

Advanced settings rules:
- Advanced settings must be hidden during first-time setup.
- Advanced settings must not block setup completion.
- Advanced settings must not expose custom scoring weights or score thresholds.
- Advanced edits apply only after Save.
- Duplicate keywords in Advanced settings must be normalized and de-duplicated case-insensitively within the same category or role family.

### FR-10: Local persistence and backend request behavior

The system must store one active preference set in browser `localStorage` for the current browser context.

Persistence and request requirements:
- Preferences must survive refresh in the same browser context.
- Preferences must not be persisted to AWS, DynamoDB, backend database tables, backend repositories, or cloud persistence services.
- Backend classification/reclassification requests must receive the active browser-local preference payload per request.
- The backend must use submitted preferences in memory and must not silently fall back to hidden hardcoded criteria when preferences are missing from a preference-dependent request.

### FR-11: Save-gated changes and immediate reclassification

The system must distinguish draft edits from active saved preferences.

- Editing wizard or Advanced settings must not change filtering/ranking until Save succeeds.
- After Save succeeds, preferences become active in `localStorage`.
- After Save succeeds, existing active jobs must be reclassified immediately using the saved preferences.
- If reclassification fails, active preferences must not be promoted in `localStorage` unless the implementation can guarantee filtering/ranking will not reflect stale classifications.

### FR-12: Preserve classification behavior where possible

The simplified wizard must map to the underlying preference DTO/criteria used by classification. Existing scoring mechanics should be preserved where compatible with the simplified selections.

Preserved mechanics include:
- Role-family grouping and once-per-family contribution.
- Existing score deltas and bucket thresholds unless a wizard requirement explicitly overrides the sponsorship behavior.
- Existing bucket names: `matched`, `review`, `rejected`.
- Existing low-text confidence behavior.

Sponsorship correction:
- The previous always-on sponsorship keyword behavior is superseded by the wizard answer.
- Sponsorship is active only when the user answers Yes to requiring visa sponsorship.
- Sponsorship is neutral when the user answers No.

### FR-13: Missing-preferences redirect

When no usable saved preference set exists, the system must redirect the user to `/job-preferences` before allowing preference-dependent filtering or matching behavior.

Preference-dependent workflows include at minimum:
- Jobs list/filtering workflows that rely on classification outputs.
- Dashboard/recommendation surfaces that rely on classification outputs.
- Source ingestion or any operation that triggers classification/ranking/matching.
- Digest/reminder generation only where eligibility depends on preference-driven classifications.

The `/job-preferences` page itself must remain accessible when preferences are missing.

## 8. Acceptance Criteria

### AC-1: First-time setup uses wizard flow

Given the user has no usable saved preferences  
When the user opens `/job-preferences`  
Then the page presents a wizard-style setup flow for Job categories, Location, Work arrangement, and Visa sponsorship instead of showing the Advanced keyword criteria as primary setup fields.

### AC-2: Job categories are predefined only

Given the user is on Step 1 of first-time setup  
When the user searches/types in the category field  
Then the user can select multiple categories only from the predefined category list and arbitrary custom/free-text categories are not saved.

### AC-3: Initial job category list is available

Given the user is on Step 1 of first-time setup  
When the category selector is displayed  
Then Python Backend, Backend Engineer, SDET, QA Automation, Test Automation, Test Infrastructure, and Developer Productivity / Developer Experience are available as selectable categories.

### AC-4: Category selections map to role families

Given the user saves one or more predefined job categories  
When classification or reclassification runs  
Then the selected categories are mapped to the role-family keyword criteria defined in FR-4 while preserving once-per-family scoring behavior.

### AC-5: Location step uses country checkbox list

Given the user is on Step 2 of first-time setup  
When the location step is displayed  
Then the user can select one or more countries from the checkbox list defined in FR-5.

### AC-6: Country selections map to location preferences

Given the user saves one or more countries  
When classification or reclassification runs  
Then selected countries are used as preferred location criteria.

### AC-7: Work arrangement supports multi-select options

Given the user is on Step 3 of first-time setup  
When the work-arrangement step is displayed  
Then Remote, Hybrid, On-site, and Flexible / Any are available as options.

### AC-8: Flexible / Any is exclusive

Given the user is on Step 3 of first-time setup  
When the user selects Flexible / Any  
Then Remote, Hybrid, and On-site are cleared and Flexible / Any is saved as no work-arrangement restriction.

### AC-9: Restrictive work arrangements clear Flexible / Any

Given Flexible / Any is selected  
When the user selects Remote, Hybrid, or On-site  
Then Flexible / Any is cleared and the selected restrictive work arrangements remain selected.

### AC-10: Visa sponsorship Yes applies sponsorship criteria

Given the user answers Yes to “I require visa sponsorship”  
When classification or reclassification runs  
Then jobs with sponsorship-support signals are preferred/required and jobs that specifically state no sponsorship are rejected.

### AC-11: Visa sponsorship No is neutral

Given the user answers No to “I require visa sponsorship”  
When classification or reclassification runs  
Then sponsorship text does not increase score, decrease score, reject, or force review solely because of sponsorship signals.

### AC-12: Setup completion requires all wizard steps

Given the user has not completed one or more required wizard selections  
When the user clicks Save  
Then the system shows validation errors and does not mark setup complete.

### AC-13: Valid wizard save completes setup

Given the user has selected at least one predefined category, at least one country, at least one work-arrangement option, and a visa sponsorship Yes/No answer  
When the user clicks Save and validation/reclassification succeeds  
Then preferences are saved to `localStorage`, setup is marked complete, and existing active jobs are reclassified.

### AC-14: Defaults are not active before Save

Given first-time setup displays any default or recommended values  
When the user has not clicked Save successfully  
Then those values are not active preferences and must not be used for filtering, ranking, matching, or classification.

### AC-15: Advanced settings hidden during first-time setup

Given the user has no completed setup  
When `/job-preferences` is displayed  
Then Advanced keyword criteria are hidden from the first-time wizard flow.

### AC-16: Advanced settings appear after setup

Given the user has completed setup  
When the user opens `/job-preferences`  
Then Advanced settings are available on the same page as collapsed or secondary content and do not dominate the primary wizard-derived preferences.

### AC-17: Advanced edits are optional and save-gated

Given the user has completed setup and opens Advanced settings  
When the user edits Advanced keyword criteria without saving  
Then filtering and ranking continue to use the previously saved active preferences.

### AC-18: Advanced duplicate keywords are de-duplicated

Given the user enters duplicate Advanced keywords within the same category or role family using different casing  
When the user clicks Save  
Then the saved preferences contain one normalized instance of each duplicate keyword and scoring semantics are unchanged.

### AC-19: Saved preferences persist after refresh

Given the user has saved valid preferences  
When the user refreshes the browser and returns to `/job-preferences` in the same browser context  
Then the saved preferences are loaded from `localStorage` and displayed.

### AC-20: Missing preferences redirect before filtering

Given the user has no usable saved preferences  
When the user attempts to access a preference-dependent filtering or matching workflow  
Then the app redirects the user to `/job-preferences` before the workflow runs.

### AC-21: Backend receives preferences per request

Given a backend classification or reclassification operation is triggered from the browser  
When the operation request is sent  
Then the request includes the active saved preferences and the backend uses those submitted preferences without persisting them.

### AC-22: Navigation placement is visible

Given the user is viewing the primary navigation  
When the navigation is rendered  
Then `Job Preferences` appears after Dashboard and before Jobs and links to `/job-preferences`.

## 9. Edge Cases

- User has no browser-stored preferences and directly opens a preference-dependent URL.
- User has no browser-stored preferences and triggers source ingestion/classification.
- User starts the wizard, edits selections, then refreshes or navigates away without saving.
- User searches for a category that is not predefined.
- User selects Flexible / Any and then selects Remote, Hybrid, or On-site.
- User selects Remote, Hybrid, or On-site and then selects Flexible / Any.
- User attempts to save without a category, country, work arrangement, or visa sponsorship answer.
- User answers No to visa sponsorship and a job contains sponsorship or no-sponsorship text.
- User answers Yes to visa sponsorship and a job explicitly states no sponsorship.
- Browser `localStorage` is unavailable, disabled, full, or cleared.
- Saved preference schema is missing wizard fields because it was created before this HITL correction.
- Reclassification after Save fails after validation succeeds.
- Advanced settings contain duplicate keywords with different casing.
- Same keyword appears in separate role families; family grouping must not be collapsed across families.

## 10. Constraints

- Persistence is browser-local only and must use `localStorage`.
- Do not implement authentication, DynamoDB, backend database persistence, backend repository persistence, or cloud persistence for preferences.
- Do not implement custom weights or user-configurable scoring thresholds.
- Do not save custom/free-text job categories from first-time setup.
- First-time setup must be wizard-first; the prior all-fields-first setup is superseded.
- Advanced settings must be hidden during first-time setup and optional after setup.
- Preference changes apply only after Save.
- Existing active jobs must be reclassified immediately after successful Save.
- Manual runtime job-list filters must remain separate from Job Preferences.
- Preserve role-family grouping.
- Preserve existing classification behavior where possible by mapping wizard selections to the underlying preference DTO/criteria.

## 11. Dependencies

- Existing classification logic and preference DTO/criteria mapping.
- Existing job list/dashboard surfaces that consume `latest_bucket`, `latest_score`, and current job decisions.
- Existing source ingestion flow that triggers classification.
- Browser `localStorage` using the Architecture-selected key/versioning strategy.
- Backend validation/classification endpoint or request contract that accepts preferences per request without persisting them.
- Reclassification capability for existing active jobs after Save.
- UI/UX update to replace first-time advanced criteria form with wizard flow.
- QA updates for wizard behavior, mapping, persistence, and reclassification.

## 12. Assumptions

- Saved preferences are scoped to the current browser/device and will not follow the user to another browser or device in this feature.
- The initial category-to-keyword mapping in FR-4 is sufficient to preserve current role matching behavior where possible.
- The initial country list in FR-5 is acceptable as the first European/Asian tech-hub country list for this feature.
- Advanced keyword fields directly edit the same underlying criteria object used by wizard mapping after setup is complete.
- If preserving exact explanatory text conflicts with replacing hardcoded references such as “MVP preferences,” implementation may update wording while preserving rule outcomes, score deltas, and bucket results where compatible with the wizard requirements.

## 13. Open Questions

None. The HITL correction requirements are sufficient for product handoff.
