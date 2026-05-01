# Design Specification

## 1. Feature Overview

Enhance the `/job-preferences` **Location** step/section from a flat country checkbox list into a grouped global country selector. Users can select a whole user-facing region/continent, expand regions to select individual countries, and search across ISO 3166-1 countries while the saved preference contract remains country-based.

### Problem Statement

The current Location UI only exposes a small flat list of countries, which makes global job searches incomplete and does not support broad geographic preferences such as “Europe” or “Asia.” Users need faster broad-region selection without losing the ability to tune individual countries.

### Goals

- Make ISO 3166-1 countries globally available in the Location section.
- Group countries by practical user-facing regions/continents.
- Allow one-click region selection that selects every country assigned to that group.
- Preserve individual country selection within each group.
- Preserve existing saved country preferences unless the user changes them and saves.
- Keep the underlying preference payload country-based; no backend/API/data model change.
- Maintain current `/job-preferences` wizard, save, validation, localStorage, and reclassification patterns.

### Non-Goals

- Do not save region IDs as backend preference values.
- Do not add backend country/region endpoints.
- Do not change classification scoring semantics beyond the existing country keyword mapping.
- Do not introduce city/state/province selection.
- Do not support custom free-text locations in this enhancement.

### Target Users / User Scenario

- Primary user: a job seeker configuring preferred job locations before running matching/classification.
- Scenario: the user is open to all of Europe and North America, but wants to exclude or add individual countries as needed. They select **Europe**, expand **North America** to verify United States, Canada, and Mexico are included, then save preferences. Matching continues to receive country-derived location keywords.

### Finalized Design Decisions

- Country source is the ISO 3166-1 country list.
- Country/region data is static frontend data for this enhancement.
- Each country appears in exactly one primary region to avoid duplicate country preference records.
- North America is a broad top-level group. United States / US, Canada, and Mexico are included under **North America** rather than rendered as separate top-level duplicate groups.
- Optional sub-labeling inside North America may be used for readability, but it must not create duplicate checkbox values or additional saved preference records.

## 2. User Goal

The user wants to quickly express broad geographic openness, such as “Europe” or “North America,” and refine it by country without manually scanning a long global flat list.

## 3. UX Rationale

Use a **searchable accordion grouped checklist** with region-level tri-state select-all controls.

- Accordions reduce cognitive load for a global ISO country list.
- Region-level checkboxes match the requirement that selecting a region selects all countries in that group.
- Tri-state region controls communicate partial selection when only some countries in a group are selected.
- Search supports fast access to a specific country while keeping grouped structure as the source of truth.
- This pattern is consistent with existing product controls: native checkboxes, fieldsets, `.surface`, `.option-grid`, selected summaries, alerts, and explicit Save behavior.

## 4. User Flow

1. User opens `/job-preferences`.
2. In setup mode, user reaches Step 2: **Location**. In edit mode, Location appears as one visible panel with saved selections loaded.
3. System renders a location search input, selected summary, and region accordions.
4. User may:
   - check a region checkbox to select every country in that group;
   - uncheck a region checkbox to deselect every country in that group;
   - expand a region and check/uncheck individual countries;
   - search for a country or region name.
5. The selected-country count updates immediately.
6. User continues/saves using existing wizard actions.
7. On Save, selected countries map to the existing `wizard.selected_countries` country IDs and generated `location_positives`; active saved preferences are updated only after existing backend validation/reclassification succeeds.

## 5. Information Hierarchy

Within the Location section:

1. Step/panel heading: **Location**
2. Short instruction: “Choose countries or select whole regions you are open to for your job search.”
3. Selected summary: “{n} countries selected.” plus optional compact selected-region summary.
4. Search input: “Search countries or regions”
5. Global helper/action row:
   - Optional secondary action: **Clear all locations**
   - Optional secondary action: **Expand all** / **Collapse all** if implementation adds many accordions
6. Region accordion list with region tri-state checkbox, count, and country checkboxes.
7. Field-level validation error.

## 6. Layout Structure

Use the existing `.surface` wizard step container and add grouped location-specific utilities only as needed.

```text
section.surface[data-wizard-step="1"]
├─ h2: Location
├─ p.muted instructions
├─ div.location-toolbar
│  ├─ div.field-group
│  │  ├─ label[for="location-search"] Search countries or regions
│  │  ├─ input#location-search
│  │  └─ p.field-help
│  └─ div.location-toolbar__actions
│     ├─ button Clear all locations
│     └─ optional button Expand/Collapse all
├─ p#country-summary.selected-summary
├─ div#region-summary.field-help aria-live="polite"
├─ div.location-region-list
│  └─ details.location-region[open]
│     ├─ summary
│     │  ├─ input[type="checkbox"].region-checkbox
│     │  ├─ span Region name
│     │  └─ span Count: selected / total
│     └─ fieldset.option-grid.option-grid--countries
│        ├─ legend.sr-only Countries in {Region}
│        └─ label > input[type="checkbox"][name="selected_countries"] Country
└─ p#country-error.field-error
```

Recommended default expansion:
- Setup with no saved locations: expand the first two high-priority groups only: **Europe** and **Asia**.
- Edit mode with saved locations: expand groups containing selected countries.
- Search active: show matching groups expanded; hide non-matching countries inside matching groups.

## 7. Components

### Location search input

- Label: “Search countries or regions”
- Placeholder: “Type a country or region”
- Filters by case-insensitive match on country label, country aliases/keywords, and region label.
- Local-only; no loading spinner required.

### Region accordion

- Use native `<details>`/`<summary>` where possible for keyboard and screen reader support.
- Each region has one select-all checkbox inside or adjacent to the summary.
- Summary content: `{Region name}`, `{selectedCount} of {totalCount} selected`.
- Region order should prioritize broad user-facing groups: Europe, Asia, North America, Australia / New Zealand, Africa, South America, Middle East, then any additional groups if required by the ISO taxonomy.
- North America must include United States / US, Canada, and Mexico as individual country checkboxes. If frontend engineers add visual sub-labels within North America, those sub-labels are presentation-only and must not be selectable groups or saved values.

### Country checkbox

- Existing checkbox pattern remains: `name="selected_countries"`, `value="<country_id>"`.
- Labels use current common English country names.
- Country IDs remain stable slug IDs to preserve existing saved selections.

### Selected summary

- Existing `#country-summary` remains.
- Copy:
  - Empty: “No countries selected.”
  - One selected: “1 country selected.”
  - Multiple: “{n} countries selected.”
- Add live region behavior only to the summary text, not every checkbox label.

## 8. Interaction Behavior

### Region selection

- Trigger: user checks a region checkbox.
- System response: add all country IDs assigned to that region to the draft selection, de-duplicated.
- UI feedback:
  - Region checkbox becomes checked.
  - All visible and hidden country checkboxes in that region become checked.
  - Region count updates to `{total} of {total} selected`.
  - Country summary updates.
- Success behavior: selection persists while navigating wizard steps and is saved only on Save.
- Failure behavior: none for local selection; if saving later fails, draft remains but active saved preferences remain unchanged.

### Region deselection

- Trigger: user unchecks a checked or partially checked region checkbox.
- System response: remove all country IDs assigned to that region from the draft selection.
- UI feedback: region and all child country checkboxes become unchecked; count becomes `0 of {total} selected`.

### Partial region state

- Trigger: user checks or unchecks individual countries so the region has at least one but not all countries selected.
- System response: set the region checkbox DOM `indeterminate = true`, `checked = false`.
- UI feedback: summary shows `{selectedCount} of {totalCount} selected`.
- Accessibility: expose partial state with `aria-checked="mixed"` on the region control if using a custom control; native checkbox `indeterminate` is acceptable visually but must be updated consistently.

### Individual country selection

- Trigger: user checks a country.
- System response: add that country ID to `wizard.selected_countries` if not present.
- UI feedback: country checkbox checked; parent region state recalculated; summaries updated.
- Trigger: user unchecks a country.
- System response: remove that country ID from `wizard.selected_countries`.
- UI feedback: country checkbox unchecked; parent region may become partial or empty.

### Search/filter

- Trigger: user types in search input.
- System response: filter country rows and region accordions by case-insensitive substring against region label, country label, aliases, and stable ID.
- UI feedback:
  - If a region label matches, show the whole region expanded.
  - If countries match, show only matching countries and expand their groups.
  - Selected countries that do not match the query may be hidden in the list but remain counted in the summary.
  - No results copy: “No countries or regions match your search.”
- Clearing search restores default/previous expanded groups and full country lists.

### Existing saved preferences

- On page load, normalize saved wizard country IDs against the new global country list.
- Existing IDs from the current list (e.g., `spain`, `united_kingdom`, `south_korea`) must resolve to the same countries and show checked.
- Existing saved `preferences.location_positives` are preserved through current behavior unless the user changes wizard location selections and saves.
- If a legacy saved country ID is no longer present due to a naming mismatch, do not silently discard it from active saved preferences. Show a non-blocking warning in the Location section: “Some saved countries could not be matched to the updated country list. Review locations before saving.” The unmatched active preference must remain active until the user saves a changed valid draft.
- Reset draft to saved values restores the saved country selections and region partial/full states.

### Geographic taxonomy rule

Each country must appear in exactly one selectable group to avoid duplicate country preference records. Use a deterministic `primary_region` assignment in the frontend country data. If a country could be perceived as belonging to multiple regions, assign it to the group most useful for job-search filtering and document aliases only for search.

Examples:
- Turkey, Israel, United Arab Emirates, Saudi Arabia, Qatar, Jordan, Lebanon, Bahrain, Kuwait, Oman, Iraq, Iran, Yemen, Palestinian Territories: **Middle East**.
- Cyprus: **Europe** unless product chooses to align it with Middle East; do not duplicate.
- Russia: **Europe** for user-facing job-search grouping unless excluded by ISO source/availability policy.
- Egypt: **Africa**; searchable by “Middle East” only if product explicitly approves aliases, but not duplicated.
- Armenia, Azerbaijan, Georgia: **Asia** unless product approves a Caucasus-specific group.
- United States / US, Canada, and Mexico: **North America**. Do not create separate top-level selectable groups for these countries.

## 9. Component States

### Location search input

- Default: empty; full grouped list visible according to default expansion rules.
- Hover: standard input hover/no special behavior.
- Focus: visible focus outline using existing `input:focus-visible`.
- Active/input: filters list on each input event.
- Disabled: disabled while saving/reclassifying or when form disabled.
- Loading: not applicable; country data is local static frontend data.
- Success: search result count shown via visible filtered list; no success alert.
- Error: no validation error from search itself.
- Empty: empty query shows all groups; no-results state appears when query has no matches.

### Region accordion

- Default: collapsed unless default expansion rules apply; summary visible.
- Hover: summary background may use `--bg-surface-subtle`; cursor pointer on summary.
- Focus: summary and region checkbox have visible focus outlines.
- Active: expanded when user toggles summary; checkbox toggles all countries without requiring expansion.
- Disabled: summary may remain expandable, but checkboxes disabled while saving; preferred implementation disables all controls during save.
- Loading: not applicable beyond form-level `aria-busy`.
- Success: selected/full/partial counts update immediately.
- Error: if no countries selected on Continue/Save, Location error appears below list.
- Empty: `0 of {total} selected`; checkbox unchecked.
- Partial: some selected; checkbox indeterminate/mixed.
- Selected: all selected; checkbox checked.

### Country checkbox

- Default: unchecked unless saved/draft selected.
- Hover: label uses existing bordered option hover pattern if added; pointer cursor.
- Focus: visible checkbox focus outline.
- Active: checked/unchecked state updates immediately.
- Disabled: disabled while saving/reclassifying.
- Loading: not applicable beyond form-level loading.
- Success: parent region and selected summary update.
- Error: group-level error only when zero countries selected and user continues/saves.
- Empty: no countries selected is allowed during draft editing but blocks setup completion/save validation.

### Clear all locations button

- Default: enabled when one or more countries are selected.
- Hover: existing secondary button hover behavior.
- Focus: visible focus outline.
- Active: clears draft location selection.
- Disabled: disabled when no countries are selected or while saving.
- Loading: disabled while saving.
- Success: all region/country states become empty; summary says “No countries selected.”
- Error: if user attempts Continue/Save after clearing, existing Location validation error appears.
- Empty: disabled.

### Save/Continue behavior affected by Location

- Default: existing wizard buttons unchanged.
- Disabled/loading/success/error states remain as specified in `docs/uiux/configurable_job_preferences_uiux.md`.
- Location-specific validation remains: at least one selected country is required.

## 10. Responsive Design Rules

### Desktop ≥ 1024px

- Toolbar uses two columns: search input grows; secondary actions align right.
- Region list may display as a single vertical stack of accordions for scanability.
- Country checkboxes inside expanded groups may use 2–3 columns when labels remain readable.

### Tablet 768px–1023px

- Toolbar wraps: search full width, actions below.
- Country checkbox grid uses 2 columns where space permits.
- Accordions remain full width.

### Mobile ≤ 767px

- Single-column layout.
- Search, summary, buttons, accordions, and country checkboxes stack vertically.
- Tap targets must be at least 44px high for summary rows and checkbox labels.
- Avoid long fixed-height scroll containers inside the page; allow normal page scrolling.

## 11. Visual Design Tokens

Use existing tokens from `app/static/css/app.css`:

- Background/surfaces: `--bg-surface`, `--bg-surface-subtle`, `--bg-canvas`
- Text: `--text-primary`, `--text-secondary`, `--text-tertiary`
- Borders: `--border-default`, `--border-strong`
- Primary/focus: `--brand-600`, `--brand-700`, `--brand-50`
- Error: `--danger-600`, `--danger-50`
- Radius: `--radius-md`, `--radius-lg`
- Shadow: `--shadow-sm`

Suggested lightweight classes:
- `.location-toolbar`
- `.location-region-list`
- `.location-region`
- `.location-region__summary`
- `.location-region__count`
- `.location-no-results`

## 12. Accessibility Requirements

- Keep Location controls inside a labelled region/fieldset context with visible heading.
- Every checkbox must have a visible label.
- Region select-all controls must communicate checked, unchecked, and mixed state.
- Native `<details>/<summary>` is preferred for accordion semantics. If custom accordions are used, implement button semantics with `aria-expanded`, `aria-controls`, and keyboard support for Enter/Space.
- Keyboard order: heading → search → actions → each region summary/select-all → country checkboxes in expanded regions → validation error/actions.
- Search must not trap focus and must not remove selected values from the draft when results are hidden.
- On validation failure, focus moves to the error summary/Location error and the country group is associated with `aria-describedby="country-error"`.
- Use `aria-live="polite"` for selected count updates only; avoid announcing every child checkbox update during region select-all.
- Maintain contrast of text, borders, focus outlines, and error messages against existing tokens.
- Disabled controls must use native `disabled` attributes where applicable.

## 13. Edge Cases

- No countries selected: block Continue/Save and show “Select at least one country.”
- Search no results: show no-results message; keep selected summary unchanged.
- Region selected while search is active: selects all countries in that region, not only visible filtered countries. Add helper text if needed: “Selecting a region includes all countries in that region.”
- Country belongs to multiple perceived regions: show it once according to `primary_region`; include alternate terms only as search aliases.
- Very large country groups: keep accordions collapsed by default and use multi-column country grid on wider screens.
- Saved legacy countries: preserve unchanged active preferences until user saves; warn if a saved ID cannot be matched.
- Duplicate countries in data: frontend data build/test should fail or de-duplicate by ID before render; no duplicate checkbox values should appear.
- Local storage unavailable: existing storage error and disabled save behavior apply.

## 14. Developer Handoff Notes

- This is frontend-only. Do not change backend APIs or preference DTO shape.
- Replace/extend `COUNTRY_OPTIONS` with a global ISO 3166-1 country list. Each option should include:
  - `id`: stable slug used in `wizard.selected_countries`
  - `label`: visible country name
  - `location_keywords`: lowercase country/search keywords used for `location_positives`
  - `region`: one primary region key
  - optional `search_aliases`: alternate common names/abbreviations
- Add a `REGION_GROUPS` frontend constant with ordered user-facing groups. Required top-level groups: Europe, Asia, North America, Australia / New Zealand, Africa, South America, Middle East, plus any additional groups needed to place every ISO 3166-1 country exactly once.
- North America must contain United States / US, Canada, and Mexico country entries. Any labels such as “US,” “Canada,” or “Mexico” inside the North America accordion are country labels or presentation-only sub-labels, not separate saved region selections.
- Countries must be assigned to exactly one `region` to prevent duplicate saved country IDs.
- Keep existing input name/value contract: `input[name="selected_countries"]` values are country IDs.
- Preserve `normalizeWizard`, `mapWizardToPreferences`, `createPreferenceEnvelope`, dirty-state, reset, and save behavior. Update only country option source and rendering/sync logic as needed.
- Existing selected country IDs must remain stable for current countries. Do not rename IDs such as `united_kingdom`, `south_korea`, `czech_republic`, `hong_kong` without a migration strategy.
- Region selection should update the same `wizard.selected_countries` array; do not add `selected_regions` to the saved preference contract unless it is UI-only and safely ignored by existing validators.
- Use local static data; no loading state is required unless implementation asynchronously imports country data. If async import is introduced, show form-level loading and disable Location controls until data is available.
- QA should verify both setup mode and post-setup edit mode.

### QA-Facing Acceptance Criteria

1. The Location section displays ISO 3166-1 countries globally, not only the previous Europe/Asia subset.
2. Countries are grouped under user-facing regions including at minimum Europe, Asia, North America, Australia / New Zealand, Africa, South America, and Middle East.
3. North America contains United States / US, Canada, and Mexico as individual country selections without duplicate top-level country groups.
4. Selecting a region selects every country in that group and updates the selected count.
5. Deselecting a region removes every country in that group and updates the selected count.
6. Selecting only some countries in a region displays a partial/mixed region state.
7. Individual country checkboxes remain selectable and persist through wizard navigation.
8. Search filters countries/regions without clearing hidden selections.
9. Previously saved country preferences display as checked after the global grouped list is introduced.
10. Existing saved preferences remain active and unchanged until the user saves a modified draft.
11. Save payload remains country-based; no backend/API/data model change is required.
12. Location validation still blocks completion when zero countries are selected.
13. The grouped selector is keyboard-operable and screen-reader understandable.
14. Mobile layout stacks controls with readable labels and usable tap targets.

### Open Questions / Assumptions

- None. Prior assumptions have been confirmed and incorporated as finalized design decisions.
