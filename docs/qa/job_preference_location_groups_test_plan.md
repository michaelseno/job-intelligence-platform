# Test Plan

## 1. Feature Overview

Feature: Job Preference Location grouped country selector  
Branch: `feature/job_preference_location_groups`  
Classification: Frontend Revamp / UI Enhancement  
Primary artifact: `docs/uiux/job_preference_location_groups_design_spec.md`

The Location section of `/job-preferences` will change from a flat country checkbox list to a searchable accordion grouped checklist backed by static frontend ISO 3166-1 country/region data. Users can select entire regions, refine individual countries, search by country/region/aliases, and save existing country-based preferences without backend/API/data model changes.

### Scope

- Location section rendering in setup mode and edit mode.
- Global ISO 3166-1 country availability through frontend static data.
- Region accordion grouping and ordering.
- North America membership for United States / US, Canada, and Mexico.
- Region select-all / deselect-all behavior.
- Region checkbox checked, unchecked, and indeterminate/mixed states.
- Individual country checkbox behavior.
- Search/filter behavior across country labels, country IDs, aliases/keywords, and region labels.
- Selected country count and optional selected-region summary updates.
- Existing saved country preferences loading, reset, wizard navigation, save/reload persistence.
- Existing validation requiring at least one selected country.
- Country-based payload contract preservation.
- Accessibility and responsive usability of the grouped selector.
- Static country data integrity: one country, one primary region; stable IDs; no duplicate checkbox values.

### Out of Scope

- Backend endpoints, DTOs, database schema, or data model changes.
- Saving region IDs as persisted preferences.
- City/state/province/custom free-text location selection.
- Classification scoring semantic changes beyond existing country keyword mapping.
- New backend-provided country/region taxonomy.
- Performance/load testing beyond basic frontend responsiveness for the static list.

## 2. Acceptance Criteria Mapping

| AC ID | Acceptance Criteria | Planned Validation |
|---|---|---|
| AC1 | Location displays ISO 3166-1 countries globally, not only previous subset. | Data integrity automated test plus UI sample checks across all required regions. |
| AC2 | Countries are grouped under user-facing regions including Europe, Asia, North America, Australia / New Zealand, Africa, South America, Middle East. | UI rendering test verifies required region headings and country counts. |
| AC3 | North America contains United States / US, Canada, Mexico without duplicate top-level country groups. | Data/UI test verifies membership and no separate selectable US/Canada/Mexico region groups. |
| AC4 | Selecting a region selects every country in that group and updates selected count. | UI interaction test on at least North America and a large region. |
| AC5 | Deselecting a region removes every country in that group and updates selected count. | UI interaction test after full group selection and from partial state. |
| AC6 | Selecting only some countries in a region displays partial/mixed state. | UI interaction/accessibility test validates `indeterminate` or `aria-checked="mixed"` and count. |
| AC7 | Individual country checkboxes remain selectable and persist through wizard navigation. | UI wizard navigation test toggles countries, moves forward/back, confirms draft state. |
| AC8 | Search filters countries/regions without clearing hidden selections. | Search interaction test with selected hidden countries and no-results state. |
| AC9 | Previously saved country preferences display as checked after grouped list introduction. | Regression test seeds saved preferences for legacy IDs and verifies checked state. |
| AC10 | Existing saved preferences remain active and unchanged until user saves modified draft. | Regression test changes draft, cancels/resets/reloads without save; verifies active preferences unchanged. |
| AC11 | Save payload remains country-based; no backend/API/data model change. | API request interception/unit test verifies `selected_countries`/`location_positives` country values only and no `selected_regions` persisted. |
| AC12 | Location validation still blocks completion when zero countries are selected. | Negative UI test clears all and attempts Continue/Save. |
| AC13 | Grouped selector is keyboard-operable and screen-reader understandable. | Manual and automated accessibility checks for labels, focus order, accordion semantics, mixed state, live count, error association. |
| AC14 | Mobile layout stacks controls with readable labels and usable tap targets. | Responsive manual/automated viewport checks at mobile, tablet, desktop widths. |

## 3. Test Scenarios

### Functional Test Cases

| Test ID | Purpose | Preconditions | Steps / Input | Expected Output | Validation Logic | Type |
|---|---|---|---|---|---|---|
| FLG-F-001 | Verify required region accordions render. | User can access `/job-preferences`. | Open Location section in setup mode. | Region accordions include Europe, Asia, North America, Australia / New Zealand, Africa, South America, Middle East. | Assert visible region names and checkbox controls. | Automated UI |
| FLG-F-002 | Verify global ISO country coverage is available. | Static country data loaded. | Inspect rendered country checkbox values and frontend country data. | ISO 3166-1 countries are represented; previous subset limitation is removed. | Compare country IDs/count against expected ISO source fixture or implementation constant. | Automated data/unit |
| FLG-F-003 | Verify North America membership. | Location section open. | Expand North America. | United States / US, Canada, and Mexico appear as countries under North America. | Assert country labels/IDs exist in North America only. | Automated UI/data |
| FLG-F-004 | Verify no duplicate top-level North America country groups. | Location section open. | Review top-level accordions. | US/United States, Canada, Mexico are not separate selectable top-level groups. | Assert top-level region names exclude those country-only groups. | Automated UI |
| FLG-F-005 | Select a full region. | Location section open with no countries selected. | Check North America region checkbox. | All North America country checkboxes become checked; region count is total/total; selected summary increases by total count. | Assert all child checkbox states and summary/count values. | Automated UI |
| FLG-F-006 | Deselect a full region. | North America fully selected. | Uncheck North America region checkbox. | All North America country checkboxes become unchecked; count is 0/total; selected summary decrements. | Assert child states and summary/count. | Automated UI |
| FLG-F-007 | Deselect a partially selected region. | Select only Canada under North America. | Click North America region checkbox while mixed. | All North America countries become deselected; mixed state clears; count 0/total. | Assert no child selected and region unchecked. | Automated UI |
| FLG-F-008 | Select individual country and update parent state. | Location section open. | Expand Europe; select Spain only. | Spain checked; Europe becomes mixed; selected summary says `1 country selected.` if no other selections. | Assert checkbox, parent mixed state, and summary text. | Automated UI |
| FLG-F-009 | Complete a partial group to full by individual countries. | Region has all but one country selected. | Select remaining country. | Region checkbox becomes checked, not mixed; count total/total. | Assert region checked and `indeterminate=false` or no `aria-checked=mixed`. | Automated UI |
| FLG-F-010 | Verify wizard navigation preserves draft selections. | Setup mode. | Select countries, navigate to another step, return to Location. | Previously selected countries remain checked and summaries are correct. | Assert draft state after navigation. | Automated UI |
| FLG-F-011 | Verify Clear all locations behavior if implemented. | One or more countries selected and Clear all visible. | Click Clear all locations. | All countries unchecked; region states clear; summary says `No countries selected.`; button disabled. | Assert all selected values empty and validation not shown until Continue/Save. | Automated UI/manual if optional |
| FLG-F-012 | Verify disabled state during save/reclassification. | Save request can be delayed/mocked. | Select country and click Save. | Search, region checkboxes, country checkboxes, and clear action are disabled while saving. | Assert native `disabled` attributes during pending request. | Automated UI |

### Search / Filter Test Cases

| Test ID | Purpose | Preconditions | Steps / Input | Expected Output | Validation Logic | Type |
|---|---|---|---|---|---|---|
| FLG-S-001 | Search by country label. | Location section open. | Type `Spain`. | Europe expands; Spain is visible; non-matching countries hidden unless region match applies. | Assert visible country rows and expanded group. | Automated UI |
| FLG-S-002 | Search is case-insensitive. | Location section open. | Type mixed-case country query, e.g. `sOuTh KoReA`. | South Korea is visible and selectable. | Assert result appears regardless of case. | Automated UI |
| FLG-S-003 | Search by stable ID. | Location section open. | Type `united_kingdom`. | United Kingdom result appears. | Assert ID-based filtering works. | Automated UI |
| FLG-S-004 | Search by alias/keyword. | Location section open. | Type alias such as `US` if implemented as alias for United States. | United States appears under North America. | Assert alias maps to country; no duplicate saved value. | Automated UI/data |
| FLG-S-005 | Search by region label. | Location section open. | Type `North America`. | Whole North America group is visible and expanded. | Assert all North America countries visible. | Automated UI |
| FLG-S-006 | Hidden selections remain selected. | Select Spain, then search `Canada`. | Spain is hidden; Canada visible. Clear search. | Spain remains checked and selected count includes Spain throughout. | Assert summary remains unchanged/incremental and Spain checked after clear. | Automated UI |
| FLG-S-007 | Region select while search active selects full group. | Search query narrows inside North America, e.g. `Canada`. | Check North America region checkbox. | All North America countries are selected, not only Canada. | Clear search and assert all North America children checked. | Automated UI |
| FLG-S-008 | No results state. | Location section open. | Type unlikely query `zzzz-no-country`. | Message `No countries or regions match your search.` appears; selected summary unchanged. | Assert no-results copy and retained selection state. | Automated UI |
| FLG-S-009 | Clearing search restores list. | Search active. | Clear search input. | Full grouped list returns with expected default/previous expansion behavior. | Assert required regions visible and selected values retained. | Automated UI |

### Regression Test Cases for Existing Saved Preferences

| Test ID | Purpose | Preconditions | Steps / Input | Expected Output | Validation Logic | Type |
|---|---|---|---|---|---|---|
| FLG-R-001 | Legacy saved IDs render checked. | Seed saved preferences with `spain`, `united_kingdom`, `south_korea`, `hong_kong`, `czech_republic`. | Open `/job-preferences` edit mode. | Corresponding countries are checked in their groups; parent regions show partial/full states accurately. | Assert checkbox values and region counts/mixed states. | Automated UI |
| FLG-R-002 | Existing saved preferences remain unchanged without save. | Seed saved preferences. | Uncheck a saved country, navigate away/reload without saving or use reset. | Active saved preferences remain unchanged; draft restores saved values on reset/reload. | Assert persisted preferences from storage/API fixture unchanged. | Automated UI/integration |
| FLG-R-003 | Modified saved preferences persist after save. | Seed saved preferences. | Add Canada, remove Spain, click Save, reload. | Updated country selections render after reload; removed country no longer selected. | Assert saved payload and reloaded UI state. | Automated UI/integration |
| FLG-R-004 | Existing validation and save failure behavior preserved. | Mock save/reclassification failure. | Change selections and click Save. | Draft remains visible; active saved preferences remain unchanged; existing error handling appears. | Assert failed request does not commit active saved preference state. | Automated UI |
| FLG-R-005 | Location positives generation remains country-derived. | Intercept save payload. | Select a region and save. | Payload contains country IDs/derived `location_positives`; no region IDs persisted. | Inspect request body/local storage envelope. | Automated API-intercept/integration |
| FLG-R-006 | Setup completion still requires country selection. | Setup mode with no countries selected. | Clear all selections and click Continue/Save. | Completion blocked with `Select at least one country.` | Assert error message, focus behavior, and no save request. | Automated UI |
| FLG-R-007 | LocalStorage / existing wizard state still works. | Existing wizard draft in localStorage. | Open page and navigate Location step. | Draft country IDs normalize to grouped UI; no unrelated wizard fields reset. | Assert location and non-location draft values. | Automated UI |

### Data Integrity Test Cases

| Test ID | Purpose | Preconditions | Steps / Input | Expected Output | Validation Logic | Type |
|---|---|---|---|---|---|---|
| FLG-D-001 | Enforce one-country-one-region mapping. | Access frontend country data constants. | Iterate all country records. | Every country has exactly one non-empty primary region. | Unit test asserts no missing, array, or duplicate region assignments. | Automated unit |
| FLG-D-002 | Prevent duplicate checkbox values. | Location UI rendered. | Collect `input[name="selected_countries"]` values. | No duplicate values. | Assert unique set size equals input count. | Automated UI/unit |
| FLG-D-003 | Stable IDs preserved for existing countries. | Access country data. | Verify IDs for legacy countries. | `united_kingdom`, `south_korea`, `czech_republic`, `hong_kong`, `spain` remain present. | Static assertions against constants. | Automated unit |
| FLG-D-004 | No saved region values. | Select all countries by region and save. | Inspect payload/envelope. | Saved selections contain country IDs only; no region keys or `selected_regions`. | Request interception and schema assertion. | Automated integration |
| FLG-D-005 | Ambiguous geography is not duplicated. | Access country data. | Check examples: Turkey/Israel/UAE in Middle East; Cyprus in one region; Egypt in Africa; Russia in Europe if present; Armenia/Azerbaijan/Georgia in Asia unless product changed. | Each example appears once with documented primary region. | Static assertions; document product-approved deviations if any. | Automated unit/manual review |
| FLG-D-006 | Generated country keywords remain usable. | Access country data and mapping function. | Generate preferences for selected sample countries. | `location_positives` include expected lowercase country/search keywords and no region-only saved records. | Unit/integration assertion. | Automated unit |

### Negative and Edge Case Test Cases

| Test ID | Purpose | Preconditions | Steps / Input | Expected Output | Validation Logic | Type |
|---|---|---|---|---|---|---|
| FLG-E-001 | Empty selection blocks completion. | No countries selected. | Attempt Continue/Save. | Error shown; focus moves to error/Location; no payload sent. | Assert error, focus, and request count. | Automated UI/a11y |
| FLG-E-002 | Full group selection handles large groups. | Location section open. | Select Asia or Africa. | All countries in group selected; UI remains responsive; count accurate. | Assert selected count equals group total. | Automated UI |
| FLG-E-003 | Partial group count accuracy. | Select non-contiguous countries in same region. | Select first, middle, last country in Europe. | Count shows 3 of total; region mixed. | Assert selected count and mixed state. | Automated UI |
| FLG-E-004 | Search no-results does not clear draft. | One selected country. | Enter no-results query and then clear it. | Selection persists; no validation error from search. | Assert selected summary and checkbox after clear. | Automated UI |
| FLG-E-005 | Legacy unmatched country ID warning. | Seed saved preference with unknown legacy ID. | Open edit mode. | Non-blocking warning appears; unmatched active preference is not silently discarded until user saves valid changed draft. | Assert warning copy and persisted active preference. | Automated/manual depending implementation access |
| FLG-E-006 | Reset restores saved values and region states. | Saved preferences loaded; user modifies draft. | Click Reset/Cancel draft action. | Saved countries checked; modified unsaved selections removed; parent region states recalc. | Assert checkboxes and summaries. | Automated UI |
| FLG-E-007 | Save/reload persistence. | User has valid draft. | Select full North America plus one Europe country, save, reload. | Same country selections render; region states accurate after reload. | Assert persisted UI state and payload. | Automated integration |
| FLG-E-008 | No backend payload shape change. | Save request intercepted. | Perform save from setup and edit mode. | Request body/envelope conforms to existing contract; no backend errors due to regions. | Schema comparison with baseline configurable preferences contract. | Automated integration |

### Accessibility Checks

| Test ID | Purpose | Validation |
|---|---|---|
| FLG-A11Y-001 | Labeling | Search input has visible label; every region and country checkbox has visible accessible name. |
| FLG-A11Y-002 | Accordion semantics | Native `<details>/<summary>` works with keyboard, or custom accordion has `button`, `aria-expanded`, `aria-controls`, Enter/Space support. |
| FLG-A11Y-003 | Mixed state announcement | Region partial state uses native checkbox `indeterminate` consistently or exposes `aria-checked="mixed"` for custom controls. |
| FLG-A11Y-004 | Keyboard order | Tab order follows heading/search/actions/regions/countries/error/actions and does not trap focus during search. |
| FLG-A11Y-005 | Focus visibility | Search, summary/accordion, region checkbox, country checkbox, clear, save/continue all have visible focus indicators. |
| FLG-A11Y-006 | Live summary | Selected count updates through `aria-live="polite"` without announcing every child checkbox during select-all. |
| FLG-A11Y-007 | Validation accessibility | Empty selection error is associated through `aria-describedby="country-error"`; focus moves to error summary/Location error. |
| FLG-A11Y-008 | Contrast and disabled states | Text, borders, errors, focus outlines meet contrast expectations; disabled controls use native disabled where applicable. |

Recommended tooling: Playwright accessibility assertions, `axe-core` scan for critical/serious issues, and manual screen reader smoke test with VoiceOver on macOS for mixed checkbox and accordion announcements.

### Responsive Checks

| Test ID | Viewport | Expected Behavior |
|---|---|---|
| FLG-RESP-001 | Desktop >= 1024px | Toolbar uses two-column layout where applicable; country grid can use 2-3 readable columns; accordions remain scannable. |
| FLG-RESP-002 | Tablet 768px-1023px | Toolbar wraps with search full width/actions below; country grid uses up to 2 columns without truncation. |
| FLG-RESP-003 | Mobile <= 767px | Search, summary, actions, accordions, and country checkboxes stack in one column; no horizontal scrolling. |
| FLG-RESP-004 | Mobile tap targets | Summary rows and checkbox labels are at least 44px high or have equivalent touch area. |
| FLG-RESP-005 | Long labels | Long country names wrap without overlapping controls or counts. |
| FLG-RESP-006 | Page scrolling | No long fixed-height nested scroll container traps the country list on mobile. |

## 4. Edge Cases

- Empty selection: Continue/Save is blocked and `Select at least one country.` appears.
- Full group selection: selecting a region selects all countries in the group, including countries hidden by active search.
- Full group deselection: deselecting a checked or mixed region removes all countries in the group.
- Partial group selection: individual child selections produce mixed/indeterminate region state and accurate `selected/total` count.
- Search by region: matching a region label shows the full region expanded.
- Search by country/alias/ID: matching countries appear inside expanded groups; unmatched selected countries remain selected while hidden.
- Search no results: no-results copy appears and selected summary remains unchanged.
- Save/reload persistence: saved country IDs reload into correct grouped checked states.
- Existing saved preferences: known legacy IDs remain stable; unknown saved IDs produce non-blocking warning and are not silently discarded before user saves.
- Data duplication: duplicate country records or duplicate checkbox values fail validation.
- Ambiguous regions: countries with multiple perceived regions appear in exactly one primary region; aliases may help search only.
- Payload compatibility: no persisted region IDs, `selected_regions`, or changed backend envelope shape.
- Local storage unavailable/save failure: existing error behavior remains; active saved preferences are unchanged on failed save.

## 5. Test Types Covered

### Recommended Automated Validation

- **Unit/static data tests**
  - Validate country constants include required regions and ISO 3166-1 coverage.
  - Validate exactly one primary region per country.
  - Validate no duplicate country IDs or checkbox values.
  - Validate stable legacy IDs remain present.
  - Validate country-to-preference mapping emits country-derived keywords only.
- **Frontend UI/integration tests**
  - Use Playwright or existing UI test framework for `/job-preferences` setup and edit flows.
  - Intercept save requests to validate country-based payload shape and no region persistence.
  - Exercise region select/deselect, individual country selection, search, wizard navigation, reset, save/reload, validation failure.
- **Accessibility automation**
  - Run axe-core against Location section in default, partial-selected, validation-error, and mobile states.

### Recommended Manual Validation

- Screen reader smoke test for region accordion semantics and mixed state announcement.
- Keyboard-only walkthrough of search, accordion expansion, region select-all, country selection, validation error recovery, and save.
- Responsive visual review at desktop, tablet, and mobile breakpoints.
- Visual inspection for long country names, count alignment, focus outlines, disabled state, and error styling.

### Execution Evidence Required in Future Test Report

- Test command outputs for unit/UI/a11y suites.
- Browser/test runner logs for failed cases.
- Save request payload screenshots/log snippets proving no backend shape change.
- Responsive screenshots for desktop/tablet/mobile.
- Accessibility scan output and manual screen reader notes.

## 6. Coverage Justification

This plan covers the full acceptance criteria from the UI/UX design specification and separates frontend behavior from explicitly out-of-scope backend changes. Functional coverage validates the grouped checklist, region selection model, individual country control, summaries, validation, and persistence. Regression coverage protects existing saved country preferences, stable legacy IDs, wizard navigation, localStorage behavior, save failure handling, and country-based payload compatibility. Data integrity coverage directly targets the highest-risk implementation areas: global ISO coverage, one-country-one-region mapping, duplicate prevention, and stable country IDs. Accessibility and responsive checks ensure the new accordion/search pattern remains usable for keyboard, screen reader, desktop, tablet, and mobile users.

## Risks / Blockers / Open Questions

- **Risk:** ISO 3166-1 completeness may be difficult to verify if no canonical test fixture/source is committed. Mitigation: add or reference a deterministic expected country fixture for data tests.
- **Risk:** Native checkbox `indeterminate` is not reflected as an HTML attribute, so UI tests must inspect DOM property or accessible state rather than static markup.
- **Risk:** Legacy unmatched country ID preservation requires clear access to active saved preferences versus draft state; test setup may need fixtures/mocks for saved preference state.
- **Open question:** Exact implementation file/module names for country constants and existing UI test framework are not yet known; automation should align to repository conventions after implementation.
