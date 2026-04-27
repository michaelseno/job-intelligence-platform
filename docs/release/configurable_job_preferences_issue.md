# GitHub Issue
## 1. Feature Name
Configurable Job Filter Preferences — Wizard-First HITL Correction

## 2. Problem Summary
Job filtering, scoring, ranking/matching, bucket assignment, and explanations currently depend on fixed criteria hardcoded in `app/domain/classification.py`. Users need configurable preferences, but HITL UX validation rejected the prior all-fields-first setup because it exposed implementation-level keyword/scoring criteria during onboarding.

The corrected scope is wizard-first: first-time setup must guide users through simple selections for job categories, countries, work arrangement, and visa sponsorship. Advanced keyword criteria remain in scope only as optional collapsed/secondary settings after setup is complete. Persistence remains browser-local only, and the implementation must continue to support future auth plus DynamoDB migration without adding backend preference persistence now.

## 3. Linked Planning Documents
- Product Spec: `docs/product/configurable_job_preferences_product_spec.md`
- Technical Design: `docs/architecture/configurable_job_preferences_architecture.md`
- UI/UX Spec: `docs/uiux/configurable_job_preferences_uiux.md`
- QA Test Plan: `docs/qa/configurable_job_preferences_test_plan.md`
- HITL Correction Report: `docs/bugs/configurable_job_preferences_hitl_simplification.md`

## 4. Scope Summary
In scope:
- Add a dedicated `/job-preferences` page and primary navigation entry after Dashboard and before Jobs.
- Replace first-time setup with a four-step wizard:
  1. Job categories selected from predefined options only.
  2. Location selected from a country checkbox list.
  3. Work arrangement selected from `Remote`, `Hybrid`, `On-site`, or exclusive `Flexible / Any`.
  4. Visa sponsorship answered with explicit Yes/No for “I require visa sponsorship”.
- Map wizard selections deterministically to the underlying preference criteria used by classification and reclassification.
- Preserve role-family grouping and existing classification mechanics where possible.
- Store one active preference set in browser `localStorage` only.
- Apply preference edits only after the user clicks Save and Save succeeds.
- Use saved preferences for filtering, ranking/matching, backend classification, reclassification, persisted buckets/scores, and explanations.
- Redirect or block users without usable configured preferences before preference-dependent workflows run.
- Immediately reclassify existing active jobs after successful Save so persisted buckets/scores reflect the active criteria.
- Expose advanced keyword criteria only after setup completion as optional collapsed/secondary settings on the same `/job-preferences` page.
- Preserve existing scoring weights, bucket thresholds/names, low-text confidence behavior, first-match behavior, and manual runtime job-list filters except where wizard-to-criteria mapping intentionally changes selected criteria.

Out of scope:
- Authentication.
- DynamoDB or cloud persistence.
- Backend database/session/cookie persistence of raw preference values.
- Multi-user account support or multi-device sync.
- Custom/free-text saved job categories in the first-time wizard.
- Configurable scoring weights, thresholds, salary, seniority, job type, excluded companies, import/export, history, or rollback.
- New job sources or unrelated UI redesigns beyond the wizard and secondary Advanced settings.

## 5. Implementation Notes
- This issue incorporates HITL UX validation feedback: the previous first-time setup with all keyword/scoring fields visible was too complicated and is superseded by a wizard-first scope.
- Browser storage key should use the versioned architecture contract: `job_intelligence.job_filter_preferences.v1`.
- The browser is the source of truth for saved preference values in this feature.
- Backend classification and reclassification must receive preferences per request and revalidate them because `localStorage` is client-controlled.
- Hardcoded/default criteria may remain only as wizard mapping seeds or advanced/default values; they must not be used as hidden runtime fallback when preferences are missing.
- Predefined job categories must map to role-positive families/keywords while preserving once-per-family scoring behavior.
- Selected countries must map to preferred location criteria.
- `Flexible / Any` must mean no work-arrangement restriction and must not be converted into restrictive matching keywords.
- If visa sponsorship is `No`, sponsorship should be neutral and should not increase, decrease, reject, or force review solely because of sponsorship signals.
- Save flow must validate/normalize preferences, reclassify existing active jobs, and only then promote normalized preferences to active `localStorage`.
- If validation or reclassification fails, active saved preferences must not be replaced.
- Source ingestion and other classification-triggering workflows must include active preferences in the request payload/form data before backend classification runs.
- Manual Jobs filters such as bucket, tracking status, source, search, and sort remain separate from saved Job Preferences.

## 6. QA Section
QA coverage must verify:
- All updated acceptance criteria in the Product Spec are covered.
- First-time `/job-preferences` renders a guided wizard, not the advanced criteria form.
- Users can select predefined job categories only; arbitrary/free-text categories are not saved.
- Multi-category selections map to expected role-positive criteria.
- Country selections map to expected preferred-location criteria.
- Work arrangement supports `Remote`, `Hybrid`, `On-site`, and exclusive `Flexible / Any` behavior.
- Visa sponsorship Yes/No maps correctly, including neutral sponsorship handling when the user does not require sponsorship.
- Setup completion requires valid selections for all four wizard steps.
- Advanced keyword settings are hidden during first-time setup and appear only after setup as collapsed/secondary content.
- Users can view, edit, validate, save, refresh, and reuse persisted preferences.
- Unsaved edits do not affect filtering/matching behavior.
- Missing preferences redirect/block preference-dependent workflows before hidden defaults can be used.
- Saved preferences replace hardcoded criteria for role, location/work arrangement, and sponsorship matching according to wizard/advanced mappings.
- Backend rejects missing/invalid preference payloads for classification-triggering operations.
- No backend/cloud/DynamoDB/auth preference persistence is introduced.
- Accessibility, storage failure, open redirect, XSS-safe rendering, and manual browser localStorage evidence are covered.

QA sign-off gate from the updated test plan requires all critical unit/API/integration/UI tests, required manual browser checks, and HITL validation of the simplified wizard experience to pass before release progression.

## 7. Risks / Open Questions
- Server-rendered pages cannot directly read `localStorage`; client-side guards and an optional non-sensitive configured marker cookie may cause a brief render before redirect.
- Strict server-side interpretation of “redirect before workflow runs” may conflict with the localStorage-only persistence constraint unless carefully scoped to actions/classification triggers.
- Reclassification on every Save creates additional decision history rows, consistent with current append/current-decision behavior but potentially increasing table volume.
- Current repository conventions do not include a full browser E2E test harness, so some localStorage and client-side wizard behavior requires manual QA/HITL evidence unless tooling is added.
- Exact category-to-keyword, country-to-location, work-arrangement, and sponsorship mappings must remain deterministic and documented so QA can assert behavior.
- Advanced settings must not undermine the simplified first-time setup or reintroduce implementation-level complexity before setup is complete.

## 8. Definition of Done
- `/job-preferences` exists, is reachable from primary navigation, and remains accessible when preferences are missing.
- First-time setup is a four-step wizard for job categories, location, work arrangement, and visa sponsorship.
- Advanced keyword criteria are hidden during first-time setup and available only after setup completion as collapsed/secondary settings.
- Setup cannot complete until valid values are saved for all four wizard steps.
- Saved wizard selections map deterministically to the underlying criteria used by classification/reclassification.
- Saved preferences persist across refresh in the same browser context using `localStorage` only.
- Saved preferences are supplied to backend classification/reclassification/source-run workflows per request.
- Filtering, ranking/matching, scores, buckets, and explanations use saved preferences rather than hidden hardcoded runtime criteria.
- New users without usable saved preferences are redirected or blocked before preference-dependent workflows run.
- Existing active jobs are reclassified immediately after successful Save.
- Existing matching/scoring mechanics and manual job-list filters are preserved except for the intended criteria-source and wizard-mapping changes.
- No auth, DynamoDB, backend DB/session/cookie raw preference persistence, custom weights, custom/free-text saved categories, or out-of-scope criteria are added.
- QA test plan coverage is implemented/executed, HITL validates the simplified wizard UX, and QA sign-off is approved before PR/release progression.
