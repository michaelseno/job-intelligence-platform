# Bug Report

## 1. Summary

HITL validation rejected the current `/job-preferences` first-time setup as too complicated because it exposes the full hardcoded classification criteria as editable keyword/scoring fields. The correction is to simplify first-time setup into a wizard-style flow for job categories, countries, work arrangement, and visa sponsorship, while moving advanced keyword/scoring criteria into an optional collapsed/secondary section after setup is complete.

## 2. Investigation Context

- Source of report: HITL validation feedback from the human reviewer.
- Branch context: `feature/configurable_job_filter_preferences`.
- Related feature/workflow: configurable Job Filter Preferences, `/job-preferences`, first-time setup, browser `localStorage` preference persistence, classification preference mapping.
- Planning issue: <https://github.com/michaelseno/job-intelligence-platform/issues/10>.
- Current QA status before HITL feedback: automated QA approved the implemented configurable-preferences behavior in `docs/qa/configurable_job_preferences_qa_report.md` with `75 passed` full Python regression evidence.
- Important workflow constraint: this is a HITL correction on the active branch. Do not create a new branch, push, or create a PR for this correction investigation.

## 3. Observed Symptoms

- Failing workflow: first-time `/job-preferences` setup UX.
- Exact HITL feedback: the current setup is too complicated with too many fields.
- Current observed UI shape:
  - `app/web/templates/preferences/job_preferences.html` renders multiple always-visible panels: `Target roles`, `Excluded role keywords`, `Work arrangement and preferred locations`, `Incompatible locations`, `Sponsorship signals`, and `How changes apply`.
  - The page asks first-time users to edit role-family names, multiline keyword lists, remote/location positive keywords, incompatible location keywords, and sponsorship supported/unsupported/ambiguous keyword lists.
- Expected corrected behavior:
  - First-time setup uses a wizard-style flow.
  - Step 1: Job categories with search/typeahead; user may select multiple predefined categories only; no saved custom/free-text categories.
  - Step 2: Location with a country checkbox list; initial list may include reasonable European and Asian tech-hub countries.
  - Step 3: Work arrangement with multi-select options `Remote`, `Hybrid`, `On-site`, and exclusive `Flexible / Any`.
  - Step 4: Visa sponsorship with yes/no question: “I require visa sponsorship”.
  - Setup is complete once job categories, location, work arrangement, and visa sponsorship are saved.
  - Advanced keyword/scoring criteria are hidden during first-time setup and appear after setup as an optional collapsed/secondary section on the same `/job-preferences` page.
- Actual current behavior:
  - First-time setup exposes advanced implementation-level criteria directly instead of a guided simple setup.

## 4. Evidence Collected

Files and artifacts inspected:

- `docs/product/configurable_job_preferences_product_spec.md`
  - Lines 28-34 require `/job-preferences`, local preference use, reclassification, and missing-preference setup.
  - Lines 43-50 and 108-121 require exposing every hardcoded criterion as editable fields.
  - Lines 193-289 define acceptance criteria around showing/editing every criteria category.
- `docs/uiux/configurable_job_preferences_uiux.md`
  - Lines 74-85 define the current information hierarchy with six form sections.
  - Lines 115 and 142-214 specify always-visible textarea/list-input patterns for initial implementation.
  - Lines 224-314 define the save/localStorage/reclassification interactions for the current advanced form.
- `docs/architecture/configurable_job_preferences_architecture.md`
  - Lines 77-83 define browser-owned localStorage preferences supplied to backend requests.
  - Lines 87-121 identify likely components: browser preference store, preferences page, backend preference schema, `ClassificationService`, `IngestionOrchestrator`, and web routes.
  - Lines 137-155 define the current underlying preference object fields that the simplified wizard still needs to map into.
- `docs/qa/configurable_job_preferences_qa_report.md`
  - Lines 11-22 show automated QA approved the prior implementation; this HITL issue is not an unresolved automated test failure.
- `app/web/templates/preferences/job_preferences.html`
  - Lines 35-121 show first-time setup directly renders the full criteria inventory as visible panels and textareas.
- `app/domain/job_preferences.py`
  - Lines 19-32 define current default classification criteria.
  - Lines 41-52 define the persisted/validated underlying `JobFilterPreferences` fields.
  - Lines 120-171 validate the underlying preference object and positive-signal requirement.
- `docs/frontend/configurable_job_preferences_implementation_report.md`
  - Lines 28-37 confirm the implemented UI displays editable criteria and localStorage/client guard behavior.

## 5. Execution Path / Failure Trace

1. A first-time user is redirected to or opens `/job-preferences` with no active saved preferences.
2. The preferences page loads default values from the backend/default preference object.
3. The template renders all advanced criteria categories as editable sections, including role-family names, multiple multiline keyword fields, incompatible location keywords, and sponsorship signal keyword groups.
4. The user must understand implementation-level classification concepts to complete setup.
5. HITL validation determined this creates too much setup complexity and fails the intended user-facing onboarding experience.
6. The corrected flow should collect simple user selections, then map those selections into the existing underlying preference object used by validation, storage, reclassification, and classification.

## 6. Failure Classification

- Primary classification: Requirements Ambiguity / missed UX requirement.
- HITL-specific classification: HITL UX validation failure; correction to current active branch scope, not a new branch feature.
- Severity: High.
- Reproducibility: Always reproducible by opening the current `/job-preferences` first-time setup UI.

Severity justification: the issue blocks HITL acceptance of the core first-time setup workflow. Automated tests pass, but the user-facing setup experience does not meet the human reviewer's usability expectations and must be corrected before release progression.

## 7. Root Cause Analysis

### Most Likely Root Cause

- Immediate failure point: `/job-preferences` first-time setup presents all configurable classification criteria as primary required setup inputs.
- Underlying root cause: the original product/UI requirements prioritized exposing every hardcoded criterion from `app/domain/classification.py` as editable fields. This translated internal classification configuration directly into first-time setup, creating an expert/advanced form instead of a guided onboarding wizard.
- Supporting evidence:
  - Product spec requires users to view/modify every hardcoded criterion (`docs/product/configurable_job_preferences_product_spec.md`, FR-4 and AC-1/AC-2).
  - UI/UX spec explicitly defines all criteria as visible form sections and states not to use accordions for the initial implementation.
  - Current template implements these sections directly.
- Contributing factor: the architecture correctly chose an underlying preference DTO for classification preservation, but the UI did not include a separate simplified input layer that maps user-friendly selections to that DTO.

## 8. Confidence Level

High.

The current specs, implementation report, and template all show that the complex field inventory was implemented intentionally from the prior requirements. HITL feedback provides the corrected requirement: simplify first-time setup into a wizard and demote advanced keyword/scoring controls.

## 9. Recommended Fix

- Likely owner: Frontend-led full-stack correction.
- Supporting owners:
  - Product/UX: update product/UI acceptance criteria to encode the wizard and advanced-section behavior.
  - Backend: adjust preference validation/mapping only if the existing `JobFilterPreferences` schema cannot represent wizard selections cleanly.
  - QA/test: update tests and manual HITL validation coverage.

Likely files/modules impacted:

- Product/UI docs:
  - `docs/product/configurable_job_preferences_product_spec.md`
  - `docs/uiux/configurable_job_preferences_uiux.md`
  - `docs/qa/configurable_job_preferences_test_plan.md`
- Frontend/templates/static JS/CSS:
  - `app/web/templates/preferences/job_preferences.html`
  - `app/templates/preferences/job_preferences.html`
  - `app/web/static/app.js`
  - `app/static/js/app.js`
  - `app/web/static/styles.css`
  - `app/static/css/app.css`
- Preference/domain mapping:
  - `app/domain/job_preferences.py`
  - routes using default preferences and save/reclassification in `app/web/routes.py`
- Tests:
  - `tests/ui/test_configurable_job_preferences_ui.py`
  - `tests/js/job_preferences_helpers.test.mjs`
  - `tests/unit/test_job_preferences_validation.py`
  - `tests/unit/test_classification_preferences.py`
  - `tests/api/test_configurable_job_preferences_api.py`

Expected correction:

1. Replace first-time setup UI with a four-step wizard:
   - Job categories: typeahead/search over predefined category options only.
   - Location: country checkbox list.
   - Work arrangement: multi-select with exclusive `Flexible / Any` behavior.
   - Visa sponsorship: yes/no selection for “I require visa sponsorship”.
2. Seed predefined job categories from current role-family examples:
   - Python Backend
   - Backend Engineer
   - SDET
   - QA Automation
   - Test Automation
   - Test Infrastructure
   - Developer Productivity / Developer Experience
3. Define an initial country list focused on European and Asian tech hubs.
4. Map wizard selections to the existing `JobFilterPreferences` object so classification behavior is preserved where possible:
   - Selected categories populate role-positive families/keywords.
   - Selected countries populate location-positive signals.
   - Work arrangement selections populate arrangement signals or leave arrangement unrestricted when `Flexible / Any` is selected.
   - Sponsorship yes/no maps to supported/unsupported sponsorship handling while preserving the rule that “no” is neutral unless other disqualifying signals apply.
5. Keep `localStorage` as the only persistence scope.
6. Keep auth, DynamoDB, backend preference persistence, and future account storage out of scope.
7. Move existing advanced keyword/scoring fields into an optional Advanced settings section:
   - Hidden during first-time setup.
   - Visible after setup is complete on the same `/job-preferences` page as collapsed/secondary content.
   - Should not block completion of the simplified setup.

Cautions/constraints:

- Do not introduce custom/free-text saved categories in Step 1.
- Do not treat `Flexible / Any` as an additional restrictive keyword; it means no work-arrangement restriction and must clear `Remote`/`Hybrid`/`On-site` selections.
- Do not introduce backend/cloud preference persistence.
- Preserve reclassification-after-save and per-request preference submission behavior.
- Preserve existing classification behavior where possible by mapping the simplified selections into the current underlying criteria structure.

## 10. Suggested Validation Steps

After implementation, rerun/update validation to cover both the simplified UX and existing regression scope:

Targeted automated checks:

```bash
node --check app/static/js/app.js && node --check app/web/static/app.js
node --test tests/js/job_preferences_helpers.test.mjs
PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py
PYTHONPATH=. uv run --extra dev pytest
```

New/updated test coverage needed:

- First-time `/job-preferences` renders wizard steps instead of the advanced criteria form.
- Job category typeahead only saves predefined categories; arbitrary free-text is not saved.
- Multi-category selection maps to expected role-positive criteria.
- Country checkbox selections map to expected location-positive criteria.
- Work arrangement multi-select supports `Remote`, `Hybrid`, `On-site` and enforces exclusive `Flexible / Any` clearing behavior.
- Visa sponsorship yes/no maps to sponsorship criteria correctly:
  - yes: prefer/require sponsorship signals and reject explicit no-sponsorship jobs.
  - no: sponsorship is neutral unless other disqualifying signals exist.
- Setup completion requires saved categories, location, work arrangement, and visa sponsorship.
- Advanced settings are hidden during first-time setup and appear collapsed/secondary after setup is complete.
- Saved wizard-derived preferences persist in `localStorage` and are submitted to backend reclassification/source-run requests.
- Existing default-equivalent classification/scoring regression tests still pass where mappings are intended to preserve behavior.

Manual HITL validation:

- Empty-storage first-time setup walkthrough on `/job-preferences`.
- Confirm the page feels like a simple guided wizard, not a keyword/scoring configuration form.
- Save valid selections, refresh, and verify saved state remains available.
- Confirm Advanced settings are discoverable only after setup and do not dominate the first-time setup.

## 11. Open Questions / Missing Evidence

- Final initial country list for Step 2 is not specified beyond “reasonable initial list of European and Asian tech-hub countries”. Product/UX should approve the exact list.
- Exact category-to-keyword mapping should be documented so QA can assert deterministic classification behavior.
- Exact representation of work arrangement restrictions in the existing keyword-based preference object needs implementation design, especially for `Hybrid`, `On-site`, and unrestricted `Flexible / Any`.
- Whether advanced settings can directly edit the same underlying keyword object after wizard setup, and how those edits coexist with wizard selections, needs a clear UX/data-model rule.

## 12. Final Investigator Decision

Ready for developer fix.

This is a HITL UX validation correction and missed UX requirement on the current active branch. The root cause is sufficiently evidenced by the prior specs and current implementation. Route next work to Product/UX for updated acceptance criteria and to Frontend-led full-stack implementation for the wizard, mapping, tests, and regression validation.
