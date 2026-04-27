# Test Plan

## 1. Feature Overview

Feature: Configurable Job Preferences — simplified wizard HITL correction

Feature classification: New Feature correction / same-branch HITL update

Primary upstream artifacts:
- Product Spec: `docs/product/configurable_job_preferences_product_spec.md`
- Architecture: `docs/architecture/configurable_job_preferences_architecture.md`
- UI/UX Spec: `docs/uiux/configurable_job_preferences_uiux.md`
- HITL Correction Report: `docs/bugs/configurable_job_preferences_hitl_simplification.md`

The HITL correction supersedes the prior all-advanced-fields-first setup. First-time `/job-preferences` setup must now use a four-step wizard that collects: job categories, countries, work arrangement, and visa sponsorship. The wizard maps those plain-language selections into the underlying `JobFilterPreferences` DTO used by backend validation, classification, reclassification, source-run request payloads, and browser `localStorage` persistence.

Advanced keyword criteria remain in scope only after setup completion. They must be hidden during first-time setup and available later on the same `/job-preferences` page as collapsed/secondary content. Save-gated behavior, local-only persistence, backend per-request preference submission, immediate active-job reclassification, source-run preference injection, and no backend/cloud preference persistence remain required.

Repository test conventions observed:
- Python/FastAPI application with pytest configured in `pyproject.toml` (`testpaths = ["tests"]`, `addopts = "-q"`).
- Existing test organization uses `tests/unit/`, `tests/api/`, `tests/integration/`, `tests/ui/`, plus lightweight Node tests under `tests/js/`.
- Existing UI tests inspect server-rendered HTML with `BeautifulSoup`; JavaScript helper behavior can be exercised with Node tests. Full browser automation is still not present.
- Existing API/integration tests use FastAPI `TestClient` and in-memory SQLite fixtures from `tests/conftest.py`.

## 2. Acceptance Criteria Mapping

| AC / Requirement | Expected Behavior | Planned Coverage |
|---|---|---|
| AC-1 / FR-2 | First-time setup shows wizard flow for Job categories, Location, Work arrangement, Visa sponsorship; advanced keyword criteria are not primary fields. | UI/template tests for no-saved-preferences page; Node/manual checks for first-load wizard state; assert advanced section absent/hidden during setup. |
| AC-2 / FR-3 | Category search/typeahead allows multiple predefined categories only; free text/custom category is not saved. | Node helper tests for filtering/selection/save payload; UI tests for no “add custom” affordance; manual keyboard typeahead check. |
| AC-3 / FR-3 | Initial categories are available: Python Backend, Backend Engineer, SDET, QA Automation, Test Automation, Test Infrastructure, Developer Productivity / Developer Experience. | UI/template test enumerating options; Node mapping fixture test. |
| AC-4 / FR-4 | Selected categories map deterministically to role-family keyword criteria and preserve once-per-family scoring. | Unit mapping tests; classification tests for selected category jobs; reclassification API test verifies mapped DTO is used. |
| AC-5 / FR-5 | Location step uses country checkbox list from approved European/Asian tech-hub list. | UI/template test for required country options; Node/manual country multi-select persistence across steps. |
| AC-6 / FR-5 | Selected countries map to preferred location criteria. | Unit mapping test; classification/reclassification test with selected country text. |
| AC-7 / FR-6 | Work arrangement options Remote, Hybrid, On-site, Flexible / Any are available. | UI/template test and Node helper test for option inventory. |
| AC-8 / FR-6 | Flexible / Any is exclusive, clears Remote/Hybrid/On-site, and maps to no work-arrangement restriction. | Node tests for exclusivity and generated DTO; manual browser check. |
| AC-9 / FR-6 | Selecting Remote/Hybrid/On-site clears Flexible / Any. | Node tests and manual browser check. |
| AC-10 / FR-7 | Visa sponsorship Yes activates sponsorship criteria so support signals are preferred and explicit unsupported roles are rejected. | Unit mapping + classification tests for supported and unsupported sponsorship text. |
| AC-11 / FR-7 | Visa sponsorship No is neutral; sponsorship text does not change score/bucket/review solely due sponsorship. | Unit classification tests comparing jobs with supported/unsupported/ambiguous sponsorship text under `No`. |
| AC-12 / FR-8 | Setup completion requires all four wizard steps. | Node validation tests; UI/manual step validation; API validation if backend validates wizard metadata. |
| AC-13 / FR-8, FR-11 | Valid wizard Save stores preferences in `localStorage`, marks setup complete, and immediately reclassifies active jobs. | API Save/reclassify tests; Node Save payload/storage tests; manual browser evidence for success state and reclassified count. |
| AC-14 / FR-8 | Defaults/recommendations are not active before successful Save. | Node/localStorage test that no active object is written before Save; manual refresh/navigation check. |
| AC-15 / FR-9 | Advanced settings hidden during first-time setup. | UI/template assertion; manual first-time setup walkthrough. |
| AC-16 / FR-9 | Advanced settings appear after setup as collapsed/secondary content on same page. | UI/template/Node tests with seeded localStorage; manual browser check for collapsed disclosure. |
| AC-17 / FR-9, FR-11 | Advanced edits are optional and save-gated. | Node dirty-state tests; manual edit-without-save check; API confirms backend only receives submitted preferences. |
| AC-18 / FR-9 | Advanced duplicates are normalized/deduplicated case-insensitively. | Unit validator tests and API Save tests for advanced keyword fields. |
| AC-19 / FR-10 | Saved preferences persist after refresh via browser `localStorage`. | Node store tests; manual browser refresh evidence; verify key `job_intelligence.job_filter_preferences.v1`. |
| AC-20 / FR-13 | Missing preferences redirect/block preference-dependent workflows before filtering/matching. | UI guard tests/Node tests; API missing-preference tests for source run/reclassify; manual `/jobs` and `/dashboard` direct access. |
| AC-21 / FR-10 | Backend receives preferences per classification/reclassification request and does not persist them. | API/source-run tests; DB/model inspection; no preference table/session/cookie raw persistence. |
| AC-22 / FR-1 | Primary nav shows `Job Preferences` after Dashboard and before Jobs. | UI/template test on nav order, href, and active key. |

Additional out-of-scope and regression protections:

| Constraint | Planned Coverage |
|---|---|
| No auth, DynamoDB, backend/cloud preference persistence. | Static/review checks; migration/model absence checks; API tests verify preferences travel in request payload only. |
| No custom/free-text saved categories in first-time wizard. | Node and manual tests with unmatched search text; assert saved wizard metadata contains only predefined identifiers/labels. |
| No custom weights or thresholds. | UI/API scope tests confirm no scoring-weight or threshold controls/fields. |
| Manual runtime filters remain separate from Job Preferences. | UI/API regression checks for bucket/tracking/source/search/sort not stored in preference object. |
| Source-run preference injection and active-job reclassification remain. | Node submit-injection tests; API source-run with preferences; Save/reclassification DB assertions. |

## 3. Test Scenarios

### 3.1 Test Data and Fixtures

#### Wizard selection fixtures

| Fixture | Wizard selections | Expected underlying DTO behavior |
|---|---|---|
| `wizard_remote_sponsorship_yes` | Categories: Python Backend + SDET; Countries: Spain + Germany; Work: Remote; Visa: Yes | Role families for selected categories; `location_positives` include selected countries lowercased; `remote_positives` include remote defaults; sponsorship keyword lists active. |
| `wizard_flexible_sponsorship_no` | Category: QA Automation; Country: Portugal; Work: Flexible / Any; Visa: No | Role family for QA Automation; location includes Portugal; no generated work-arrangement restriction; sponsorship supported/unsupported/ambiguous generated lists cleared/neutral. |
| `wizard_hybrid_onsite_no` | Category: Developer Productivity / Developer Experience; Countries: Japan + Singapore; Work: Hybrid + On-site; Visa: No | Category role family active; location countries active; Flexible not set; on-site acceptable and generated incompatible on-site terms removed where mapping supports it; sponsorship neutral. |
| `invalid_wizard_missing_category` | No category, valid other steps | Validation error; setup not complete; no active storage write. |
| `invalid_wizard_missing_country` | Valid category/work/visa, no country | Validation error; setup not complete. |
| `invalid_wizard_missing_work` | Valid category/country/visa, no work arrangement | Validation error; setup not complete. |
| `invalid_wizard_missing_visa` | Valid category/country/work, no visa answer | Validation error; setup not complete. |
| `invalid_custom_category_only` | Search text `Rust Space Wizard`, no predefined selection | No category saved; validation error. |

#### Classification job fixtures

| Fixture | Purpose | Expected Result |
|---|---|---|
| `python_backend_spain_remote_sponsor_supported` | Matches selected category, selected country, Remote, supported sponsorship. | Matched/review according to preserved scoring; role and location/remote/sponsorship rules use wizard-mapped criteria. |
| `old_unselected_category_job` | Matches a category not selected in wizard. | No positive role-family match from unselected category. |
| `unsupported_sponsorship_job_yes` | Explicitly states no sponsorship while Visa = Yes. | Rejected or negative sponsorship outcome according to corrected sponsorship rule. |
| `unsupported_sponsorship_job_no` | Same text while Visa = No. | Sponsorship text is neutral and does not alone reject/decrease/force review. |
| `flexible_any_remote_job` | Remote text with Flexible / Any selected. | No generated work-arrangement restriction; no remote boost solely from Flexible / Any unless advanced criteria explicitly saved. |
| `onsite_acceptable_job` | On-site text with On-site selected. | On-site is not treated as incompatible solely by generated defaults. |
| `low_text_job` | Missing/minimal fields. | Existing low-text behavior remains. |

### 3.2 Backend / Domain Unit Tests

Recommended files:
- `tests/unit/test_job_preferences_validation.py`
- `tests/unit/test_classification_preferences.py`
- New or updated: `tests/unit/test_job_preferences_wizard_mapping.py`

Coverage:
1. Wizard category mapping for every initial category exactly matches Product FR-4 / UIUX mapping.
2. Multiple selected categories merge mapped role keywords and preserve role-family grouping.
3. Unselected categories do not appear in generated role-positive criteria.
4. Country selections map to lowercase `location_positives` and only approved country values are accepted/saved.
5. Remote maps to current remote positive defaults.
6. Hybrid preserves high-level metadata without adding unsupported scoring keywords unless explicitly designed.
7. On-site removes/generated avoids incompatible on-site defaults where required.
8. Flexible / Any maps to unrestricted work arrangement: no generated work positive/negative restriction.
9. Visa Yes keeps sponsorship supported/unsupported/ambiguous criteria active.
10. Visa No clears generated sponsorship supported/unsupported/ambiguous lists and classification is neutral for sponsorship text.
11. Setup validation rejects missing category, country, work arrangement, or visa answer.
12. Custom/free-text category labels are rejected or ignored and never persisted as saved category metadata.
13. Advanced keyword validation still trims, drops blanks, and deduplicates within category/family.
14. Advanced-only fields not represented by wizard remain preserved when wizard saves overwrite generated simple criteria, where technically supported.
15. Classification requires supplied preferences and never silently falls back to hardcoded defaults when preferences are missing.

### 3.3 Backend API / Integration Tests

Recommended files:
- `tests/api/test_configurable_job_preferences_api.py`
- `tests/integration/test_job_preferences_routes.py`
- `tests/integration/test_source_run_requires_preferences.py`
- New or updated: `tests/api/test_configurable_job_preferences_wizard_api.py`

Coverage:
1. `GET /job-preferences` returns setup wizard shell and default wizard metadata/options when no preferences are active.
2. Save/reclassify endpoint accepts wizard-mapped valid preference payload, returns normalized preferences including wizard metadata, and reclassifies active jobs.
3. Save/reclassify rejects invalid wizard payloads or mapped DTOs with missing required step data.
4. Save/reclassify with Visa = No produces neutral sponsorship criteria in normalized response.
5. Save/reclassify with Visa = Yes produces active sponsorship criteria in normalized response and classification decisions reflect unsupported sponsorship rejection.
6. Reclassification failure returns error and does not instruct frontend to promote draft to active storage.
7. `POST /jobs/reclassify` requires supplied active preferences and rejects missing/invalid payloads.
8. `POST /sources/{source_id}/run` checks source existence/deleted/inactive state before missing-preference validation and still requires preferences for runnable sources.
9. Successful source run passes active wizard-derived preferences into classification and persisted decisions reflect selected categories/countries/sponsorship answer.
10. Preference-dependent HTML routes (`/dashboard`, `/jobs`, digest/reminders where applicable) are guarded/marked for missing-preferences setup.
11. `next` parameter accepts only safe same-origin relative paths.
12. No backend preference persistence is created; raw preferences are not stored in DB/session/cookie/cloud persistence.

### 3.4 Frontend / UI Tests

Recommended files:
- `tests/ui/test_configurable_job_preferences_ui.py`
- New or updated JS helper tests: `tests/js/job_preferences_helpers.test.mjs`
- Optional if browser harness is introduced: `tests/ui/test_configurable_job_preferences_wizard_browser.py` or Playwright equivalent.

Automated HTML/UI coverage:
1. Primary nav renders `Dashboard`, `Job Preferences`, `Jobs` in that order.
2. First-time `/job-preferences` page header is `Set up Job Preferences` and status is `Setup required`.
3. Wizard progress indicates four steps in order: Job categories, Location, Work arrangement, Visa sponsorship.
4. First-time page renders only the current wizard step as primary content and does not render advanced keyword sections as always-visible primary panels.
5. Step 1 includes search/typeahead input labeled `Search job categories` and all required predefined categories.
6. Step 1 contains no `Add custom category` UI and no hidden control that would save arbitrary free text.
7. Step 2 includes approved country checkbox list. The Product list must be covered; if UI/UX list differs, QA must flag discrepancy before sign-off.
8. Step 3 includes Remote, Hybrid, On-site, Flexible / Any.
9. Step 4 includes required Yes/No radio group for “I require visa sponsorship”.
10. Save button appears on final step; Continue/Back controls follow wizard navigation rules.
11. Post-setup view, when seeded with saved preferences, shows primary summary sections and an `Advanced settings` disclosure collapsed by default.
12. Advanced settings are hidden during first-time setup and do not block setup completion.
13. Manual runtime job filters (`bucket`, `tracking_status`, `source`, `search`, `sort`) do not appear as preferences fields.
14. No out-of-scope salary, job type, experience-level, custom weights, thresholds, DynamoDB, auth, import/export controls are present.

Node/JS helper coverage:
1. Category typeahead filters predefined categories case-insensitively.
2. Arbitrary search text is not saved as a category.
3. Multi-category selection toggles and serializes only predefined identifiers/labels.
4. Country selections persist across step navigation and map to location criteria.
5. Flexible / Any clears Remote/Hybrid/On-site.
6. Remote/Hybrid/On-site clear Flexible / Any.
7. Visa Yes/No maps to correct sponsorship-generated lists.
8. Editable dirty-state ignores metadata such as `configured_at` but detects actual wizard/advanced edits.
9. Source-run submit reads active `localStorage` at submit time and injects `job_preferences_json`.
10. `JobPreferencesStore.isUsable()` rejects missing wizard fields, unsupported schema, and positive-signal-free or incomplete setup payloads.

Manual browser coverage required unless full browser automation is added:
1. Empty `localStorage`, open `/job-preferences`: wizard appears, Advanced settings hidden, no active preferences written before Save.
2. Complete all four steps with valid selections; Save writes normalized preferences to `localStorage` only after backend success and shows reclassified count.
3. Refresh after Save: post-setup view displays saved wizard summary, Active status, last saved timestamp, and collapsed Advanced settings.
4. Start wizard, navigate Back/Continue, refresh before Save: setup remains incomplete and no active preferences exist.
5. Type unmatched category text and attempt Continue: custom value is not saved; validation requires predefined category.
6. Verify Flexible / Any exclusivity both directions in a real browser.
7. Visa Yes and No helper text/meaning are visible and understandable.
8. Edit Advanced settings after setup without Save: active preferences and matching behavior remain unchanged.
9. Save Advanced edits: normalized values persist; duplicate keywords collapse; wizard summary remains coherent.
10. Change wizard selections after Advanced edits and Save: generated simple criteria are overwritten while advanced-only fields are preserved where possible.
11. localStorage unavailable/full shows blocking error and disables/prevents Save.
12. Missing preferences redirect/guard from `/jobs` or `/dashboard` to `/job-preferences?next=<path>`.
13. Source-run form submits current active preferences from `localStorage`, including after another tab updates preferences.

### 3.5 Accessibility Checks

Automated/template checks:
1. One `<h1>` and one visible `<h2>` for the current wizard step.
2. Wizard progress exposes current step text and uses `aria-current="step"` when implemented as a list.
3. Step changes move focus to the new step heading in JS/browser tests or manual evidence.
4. Category, country, work arrangement, and visa controls use visible labels; checkbox/radio groups use `<fieldset>`/`<legend>` or equivalent accessible grouping.
5. Typeahead is keyboard operable and does not require mouse-only selection.
6. Help/error text is connected via `aria-describedby`.
7. Invalid step groups set `aria-invalid="true"` where supported and show step-level error summary with `role="alert"`.
8. Success confirmation receives focus after Save.
9. Save/reclassification loading state is announced via button text and/or `aria-live="polite"`.
10. `localStorage` blocking errors use `role="alert"`.
11. Flexible / Any exclusivity is reflected in checkbox state and helper text, not color alone.
12. Advanced settings disclosure is keyboard operable and exposes expanded/collapsed state; native `<details>/<summary>` is preferred.
13. Mobile layout keeps wizard controls readable and tap targets usable.

Manual accessibility smoke checks:
1. Complete the entire wizard using keyboard only.
2. Use keyboard to search/select category options without saving custom text.
3. Screen reader announces step progress, step errors, loading, storage errors, and save success count.
4. Expand/collapse Advanced settings by keyboard after setup.

### 3.6 Regression Scope

1. Existing classification mechanics remain preserved where compatible: role-family grouping, once-per-family scoring, bucket names, score thresholds, low-text behavior.
2. Sponsorship behavior is intentionally changed by wizard answer: Yes activates sponsorship criteria; No is neutral.
3. Source ingestion still creates source runs, upserts/deduplicates jobs, and writes current decisions when valid preferences are supplied.
4. Source-run deleted/nonexistent/inactive errors retain existing semantics before missing-preference validation where applicable.
5. Jobs page filters/search/sort/tracking/source filtering remain separate from saved preferences.
6. Dashboard counts/previews continue to use persisted latest bucket/score outputs after reclassification.
7. Hidden rejected job behavior remains intact when wizard preferences change bucket outcomes.
8. Source-delete visibility/cleanup behavior remains unchanged.
9. Direct job detail routes remain governed by current visibility rules.
10. Digest/reminder behavior remains unchanged except where eligibility depends on reclassified persisted decisions and valid preferences are required.
11. Navigation and template shells remain visually consistent except for required Job Preferences wizard changes.
12. No Alembic migration, SQLAlchemy preference persistence model, DynamoDB integration, auth requirement, custom score weights, or backend preference repository is introduced.

## 4. Edge Cases

| Edge Case | Expected Result | Coverage |
|---|---|---|
| No saved preferences and direct `/jobs` or `/dashboard` access. | Redirect/client-guard to wizard at `/job-preferences?next=<relative_path>`; no hidden defaults used. | Integration + JS/manual. |
| No saved preferences and source ingestion run. | Existing runnable source returns missing-preferences error before adapter fetch; nonexistent/deleted source still returns source error first. | API/integration. |
| User refreshes mid-wizard before Save. | Setup remains incomplete; no active preferences written. | Manual/JS. |
| Category search has no predefined match. | Show no-results text; no add-custom action; typed text not saved. | UI + JS/manual. |
| User attempts Continue with no category. | Step error: “Select at least one job category.” | JS/manual. |
| User attempts Continue with no country. | Step error: “Select at least one country.” | JS/manual. |
| User attempts Continue/Save with no work arrangement. | Step error: “Choose at least one work arrangement.” | JS/manual. |
| User attempts Save with no visa Yes/No. | Error: “Choose whether you require visa sponsorship.” | JS/manual. |
| Flexible / Any selected after Remote/Hybrid/On-site. | Other options cleared; saved as unrestricted. | JS/manual + mapping unit. |
| Remote/Hybrid/On-site selected after Flexible / Any. | Flexible cleared; restrictive selections remain. | JS/manual. |
| Visa No with sponsorship/no-sponsorship job text. | Sponsorship text is neutral and does not alone score/reject/review. | Unit classification. |
| Visa Yes with explicitly unsupported sponsorship text. | Job is rejected/negatively classified per sponsorship requirement. | Unit/API classification. |
| Existing saved preference lacks wizard metadata from pre-HITL version. | Treat as repair/setup required or show “Advanced custom preferences active” with Advanced review path per UIUX; Save required before wizard summary if unusable. | UI/manual + store usability tests. |
| Advanced duplicate keywords with different casing. | Deduplicate case-insensitively within same category/family. | Unit/API/JS. |
| Same keyword in separate role families. | Preserve in each family; family grouping not collapsed. | Unit mapping/classification. |
| Wizard save after Advanced edits. | Wizard-generated role/location/work/sponsorship criteria overwritten by current wizard answers; advanced-only fields preserved where possible. | JS/unit/manual. |
| Backend reclassification fails during Save. | Do not write draft to `localStorage`; keep prior active preferences and show blocking error. | API/manual. |
| Final localStorage write fails after backend success. | Show browser persistence failure; do not mark setup complete/Active. | Manual/JS error simulation. |
| Raw HTML/script in advanced keyword field. | Render escaped as text; no script execution. | Security/UI. |
| Unsafe `next=https://evil.example` or `//evil.example`. | Rejected/ignored; only safe relative continuation allowed. | API/integration. |

## 5. Test Types Covered

- Functional coverage: wizard rendering, step navigation, required selections, wizard-to-DTO mapping, advanced secondary settings, Save flow, local persistence, reclassification, source-run injection.
- Negative coverage: missing wizard selections, custom/free-text category attempts, invalid preferences, missing preferences on classification-triggering routes, unsafe `next`, backend reclassification/localStorage failures.
- Edge case coverage: Flexible / Any exclusivity, sponsorship Yes/No divergence, old saved schema without wizard metadata, Advanced/wizard overwrite interaction, duplicate keywords, same keyword in multiple role families.
- Integration coverage: browser-to-backend Save, backend validation/reclassification, source ingestion with submitted preferences, Dashboard/Jobs after persisted decision updates.
- Regression coverage: classification mechanics where compatible, source-run error precedence, Jobs filters, dashboard, hide-rejected behavior, source-delete cleanup, no backend preference persistence.
- Accessibility coverage: wizard progress, focus management, grouped controls, keyboard typeahead/chips, alert/status semantics, disclosure behavior, responsive layout.
- Security/privacy coverage: no backend/cloud preference persistence, no raw preference cookie/session storage, server-side revalidation, open redirect prevention, XSS-safe rendering.

Recommended commands once the correction is implemented:

```bash
node --check app/static/js/app.js && node --check app/web/static/app.js
node --test tests/js/job_preferences_helpers.test.mjs
PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py
PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_wizard_mapping.py
PYTHONPATH=. uv run --extra dev pytest tests/unit/test_classification_preferences.py tests/unit/test_classification.py
PYTHONPATH=. uv run --extra dev pytest tests/api/test_configurable_job_preferences_api.py tests/api/test_configurable_job_preferences_wizard_api.py
PYTHONPATH=. uv run --extra dev pytest tests/integration/test_job_preferences_routes.py tests/integration/test_source_run_requires_preferences.py
PYTHONPATH=. uv run --extra dev pytest tests/ui/test_configurable_job_preferences_ui.py
PYTHONPATH=. uv run --extra dev pytest
```

If exact new test filenames differ, run the implemented equivalent suites plus the full regression suite.

Manual execution evidence to capture for QA report:
- Screenshots or DOM evidence for first-time wizard Step 1-4, validation errors, setup required state, save success, post-setup summary, and collapsed Advanced settings.
- Browser devtools evidence of `localStorage["job_intelligence.job_filter_preferences.v1"]` before Save, after Save, after refresh, and after failed Save.
- Stored preference evidence showing `wizard` metadata and mapped underlying criteria.
- Network evidence that Save/source-run/reclassify requests include active preferences and no backend persistence endpoint/table is used.
- Backend test output and route logs for successful/failed reclassification and source-run preference validation.

QA sign-off gate for this correction:
- First-time setup is demonstrably wizard-first and Advanced settings are hidden.
- All four wizard steps are required for setup completion.
- Category selection is predefined-only; no custom saved categories.
- Wizard selections map deterministically to underlying criteria and classification behavior matches Product/UX requirements.
- Visa sponsorship Yes and No behaviors are both proven.
- Advanced settings are available only after setup, collapsed/secondary, optional, save-gated, and normalized.
- Saved preferences persist only in browser `localStorage`; backend receives preferences per request and does not persist them.
- Source-run preference injection and active-job reclassification remain working.
- Full regression suite passes with no blocking accessibility/security/privacy defects.

## 6. Coverage Justification

The updated coverage shifts QA emphasis from direct first-time editing of internal keyword fields to validating the corrected user-facing wizard and its deterministic mapping into the existing backend preference DTO. Unit tests protect mapping and classification semantics, API/integration tests prove backend validation/reclassification/source-run behavior, static UI and Node tests cover wizard structure and client-side behavior, and manual/browser checks cover localStorage lifecycle, focus, keyboard, and real UX acceptance. Regression scope preserves the previously approved backend/localStorage/per-request architecture while ensuring the HITL usability correction does not break existing classification, source ingestion, Jobs/Dashboard, hidden-rejected, or source-delete behavior.

Known remaining QA risk: the repository still lacks full browser automation. Node helper tests can cover deterministic JavaScript mapping/state functions, but final HITL sign-off should include manual browser evidence for the complete wizard, localStorage refresh, focus movement, and responsive/accessibility smoke checks.
