# GitHub Issue

## 1. Feature Name

Job Preference Location Groups

## 2. Problem Summary

The Job Preference page Location section currently uses a flat, limited country checklist. This does not support broad global job-search preferences efficiently and makes it difficult for users to select countries by continent or practical region.

Users need a searchable grouped country selector that supports region-level select-all behavior while preserving individual country control and existing saved country preferences unless the user explicitly changes and saves them.

## 3. Linked Planning Documents

- UI/UX Spec: `docs/uiux/job_preference_location_groups_design_spec.md`
- QA Test Plan: `docs/qa/job_preference_location_groups_test_plan.md`
- Product Spec: Not applicable. Requirements were clear for this focused frontend UI enhancement and are captured in the UI/UX spec and QA plan.
- Technical Design: Not applicable. No backend, API, DTO, database, or data model changes are expected; implementation can be derived from frontend UI/UX and QA guidance.

## 4. Scope Summary

In scope:

- Replace the flat Location country list with a searchable accordion grouped checklist.
- Use ISO 3166-1 countries globally through frontend static data.
- Group countries by broad user-facing primary regions/continents.
- Include North America as a region containing United States / US, Canada, and Mexico.
- Ensure each country maps to exactly one primary region to avoid duplicate preference records.
- Support region-level select-all and deselect-all behavior.
- Preserve individual country checkbox selection.
- Preserve existing saved country preferences unless the user changes and saves the draft.
- Preserve the existing country-based preference payload contract.
- Maintain setup mode, edit mode, validation, wizard navigation, localStorage, save, and reclassification behavior.
- Validate responsive and accessibility behavior for the new grouped selector.

Out of scope:

- Backend endpoints or backend country/region taxonomy.
- API, DTO, database, or data model changes.
- Persisting region IDs as preferences.
- City, state, province, or custom free-text location selection.
- Classification scoring semantic changes beyond existing country keyword mapping.

## 5. Implementation Notes

- Treat this as frontend-only.
- Add or extend static frontend country data to represent ISO 3166-1 countries.
- Country records should include stable country IDs, visible labels, country-derived location keywords, one primary region key, and optional aliases for search.
- Existing selected country IDs must remain stable for current saved preferences, including examples such as `spain`, `united_kingdom`, `south_korea`, `czech_republic`, and `hong_kong`.
- Add ordered region groups including at minimum Europe, Asia, North America, Australia / New Zealand, Africa, South America, and Middle East.
- North America must include United States / US, Canada, and Mexico as country entries, not duplicate top-level selectable country groups.
- Region selection should update the existing `wizard.selected_countries` country array. Do not persist `selected_regions` or region IDs.
- Region controls should support checked, unchecked, and mixed/indeterminate states.
- Search should filter by country label, stable ID, aliases/keywords, and region label without clearing hidden selections.
- When a region is selected while search is active, all countries in that region should be selected, not only visible matches.
- Legacy unmatched saved country IDs must not be silently discarded from active saved preferences before the user saves a changed valid draft.

## 6. QA Section

QA planning is documented in `docs/qa/job_preference_location_groups_test_plan.md`.

Required validation areas:

- Global ISO 3166-1 country coverage.
- Required region rendering and ordering.
- North America membership for United States / US, Canada, and Mexico.
- Region select-all, deselect-all, and mixed/partial states.
- Individual country selection and wizard navigation persistence.
- Search by country, region, stable ID, and alias without clearing hidden selections.
- Existing saved preference loading, reset, save, save failure, and reload behavior.
- Country-based save payload with no persisted region values.
- Empty Location validation.
- Data integrity: one country, one primary region; no duplicate checkbox values; stable legacy IDs.
- Accessibility checks for labels, keyboard operation, accordion semantics, mixed state, live summaries, focus, and validation association.
- Responsive checks for desktop, tablet, and mobile layouts.

## 7. Risks / Open Questions

Risks:

- ISO 3166-1 completeness needs deterministic verification through implementation constants or test fixtures.
- Checkbox `indeterminate` state is a DOM property, so automated tests must inspect the property or accessible mixed state rather than static HTML attributes.
- Legacy unmatched country preservation may require careful distinction between active saved preferences and draft UI state.
- Large country groups may create usability or performance concerns if rendering is not organized clearly.

Open questions:

- None currently blocking planning. Implementation file/module names and test framework alignment should be confirmed during development.

## 8. Definition of Done

- Location section renders as a searchable grouped country checklist.
- ISO 3166-1 countries are globally available from frontend static data.
- Required primary regions are present and every country maps to exactly one primary region.
- North America contains United States / US, Canada, and Mexico without duplicate selectable top-level groups.
- Region select-all/deselect-all works and updates child countries, mixed state, and counts correctly.
- Individual country selection remains available and persists through wizard navigation.
- Existing saved country preferences load correctly and remain preserved unless changed and saved.
- Save payload remains country-based with no backend/API/data model change.
- Empty Location validation remains enforced.
- Automated and/or manual QA validates functional, regression, data integrity, accessibility, and responsive scenarios from the QA test plan.
- No source code release occurs until QA and HITL gates are satisfied in later phases.
