# Design Specification

## 1. Feature Overview

Create a configurable **Job Preferences** experience at `/job-preferences` that lets users complete a simple first-time setup before job filtering/classification runs. Preferences remain browser-local in `localStorage`; backend classification/reclassification receives the active preference payload per request and does not persist preferences.

**HITL correction:** the previous all-fields-first setup layout is superseded for first-time setup. First-time setup must be a four-step wizard. Advanced keyword/scoring fields remain available only after setup completion as a collapsed secondary section on the same page.

Route and placement:
- Route: `/job-preferences`.
- Primary navigation: after **Dashboard**, before **Jobs**.
- Active nav key: `job_preferences`.

## 2. User Goal

The user wants to quickly tell the app what jobs they want, where they are open to working, what work arrangements they accept, and whether they require visa sponsorship—without editing internal keyword/scoring rules during initial setup.

## 3. UX Rationale

The wizard reduces first-time setup complexity while preserving the underlying configurable criteria model.

- First-time users should answer plain-language questions, not edit classification constants.
- A step-by-step wizard supports completion gating and clearer validation.
- Advanced controls are still available after setup for power users, satisfying configurability without blocking onboarding.
- Browser-local persistence, explicit Save, immediate reclassification after Save, and per-request backend preference submission remain unchanged.

## 4. User Flow

### First-time setup / missing preferences

1. User opens a preference-dependent workflow such as `/dashboard`, `/jobs`, source ingestion, digest/reminder generation, or another classification-dependent surface.
2. System detects no usable active preferences in `localStorage`.
3. User is redirected/navigated to `/job-preferences?next=<encoded-relative-path>`.
4. Page shows setup wizard with status **Setup required** and four steps:
   1. Job categories
   2. Location
   3. Work arrangement
   4. Visa sponsorship
5. User completes each step using predefined controls.
6. On final step, user clicks **Save preferences**.
7. System maps wizard selections into the underlying preference object, validates/normalizes it, sends it to backend validation/reclassification, and writes the normalized response to `localStorage` only after backend success.
8. On success, existing active jobs are immediately reclassified and the user may continue to the original `next` workflow.

### Editing after setup completion

1. User selects **Job Preferences** from primary navigation.
2. Page loads active preferences from `localStorage`.
3. Page shows a compact editable summary of the four wizard sections plus a collapsed **Advanced settings** section.
4. User may edit wizard selections and/or expand Advanced settings.
5. User clicks **Save preferences**.
6. System validates, reclassifies existing active jobs, then updates active `localStorage` preferences only after backend success.

## 5. Information Hierarchy

### First-time setup hierarchy

1. Page header
   - Title: “Set up Job Preferences”
   - Description: “Answer a few questions so the app can filter and rank jobs for your search.”
   - Status badge: **Setup required**
2. Setup callout
   - “Job matching is paused until preferences are saved. Defaults are not active until you complete setup.”
3. Wizard progress indicator
   - Step 1 of 4: Job categories
   - Step 2 of 4: Location
   - Step 3 of 4: Work arrangement
   - Step 4 of 4: Visa sponsorship
4. Current step panel
5. Wizard action row
   - **Back** where applicable
   - **Continue** for steps 1–3
   - **Save preferences** on step 4

### Post-setup hierarchy

1. Page header
   - Title: “Job Preferences”
   - Description: “Configure the criteria used to filter, score, and rank jobs.”
   - Status badge: **Active** or **Unsaved changes**
   - Last saved timestamp
2. Success/error/storage alerts
3. Editable summary sections for job categories, locations, work arrangement, and visa sponsorship
4. Collapsed **Advanced settings** section
5. Save action row

Manual runtime job-list filters (`bucket`, `tracking_status`, `source`, free-text search, sort) remain separate and must not appear in preferences.

## 6. Layout Structure

Use existing UI conventions from `app/web/templates` and `app/web/static/styles.css`: `.page-header`, `.panel`, `.form-grid`, `.field-group`, `.button-row`, `.alert`, `.callout-warning`, `.callout-info`, `.badge`, `.field-help`, and `.field-error`.

### First-time wizard layout

```text
Primary nav
Main .container.page-shell
├─ Page header: Set up Job Preferences
├─ Setup/storage alert region
├─ Wizard progress indicator
├─ form#job-preferences-wizard
│  ├─ Step panel: one visible step at a time
│  └─ Action row: Back / Continue or Save preferences
```

Only one wizard step is visible at a time. Do not render the Advanced settings section during first-time setup.

### Post-setup layout

```text
Primary nav
Main .container.page-shell
├─ Page header: Job Preferences
├─ Alert region
├─ form#job-preferences-form
│  ├─ Panel: Job categories
│  ├─ Panel: Location
│  ├─ Panel: Work arrangement
│  ├─ Panel: Visa sponsorship
│  ├─ details/section: Advanced settings (collapsed by default)
│  ├─ Panel/callout: How changes apply
│  └─ Action row
```

## 7. Components

### Wizard progress indicator

- Shows four steps with current step highlighted.
- Text format: “Step {n} of 4: {step name}”.
- Use visible text; do not rely on color alone.
- Current step should be announced to screen readers via heading text and/or `aria-current="step"` if using a list.

### Step 1: Job categories

Purpose: collect target job categories using predefined options only.

Controls:
- Search/typeahead input labeled “Search job categories”.
- Multi-select predefined category options rendered as checkboxes or selectable chips with checkbox semantics.
- Selected categories summary below the search field.

Initial predefined categories:
- Python Backend
- Backend Engineer
- SDET
- QA Automation
- Test Automation
- Test Infrastructure
- Developer Productivity / Developer Experience

Search/typeahead behavior:
- Trigger: user types in the search field.
- System response: filter predefined category options by case-insensitive substring match.
- UI feedback: show matching options below the search field.
- Empty search: show all predefined categories.
- No results: show “No matching predefined categories.” Do not offer “Add custom category”.
- Enter key behavior: if exactly one filtered option is highlighted/focused, select it; otherwise do not save arbitrary typed text.
- Custom/free-text saved categories are not allowed.

Validation:
- At least one predefined job category must be selected to continue.
- Error copy: “Select at least one job category.”

### Step 2: Location

Purpose: collect preferred countries as location-positive signals.

Control:
- Country checkbox list.
- Multi-select allowed.
- Include a search/filter input if the list becomes visually long; the checkbox list remains the source of truth.

Approved initial European and Asian tech-hub country list:
- Spain
- Portugal
- Germany
- Netherlands
- Ireland
- United Kingdom
- France
- Switzerland
- Sweden
- Denmark
- Finland
- Poland
- Estonia
- Czech Republic
- Lithuania
- Romania
- Singapore
- Japan
- South Korea
- India
- Taiwan
- Hong Kong
- Malaysia
- Thailand
- Vietnam
- Philippines
- Indonesia

Validation:
- At least one country must be selected to complete setup.
- Error copy: “Select at least one country.”

### Step 3: Work arrangement

Purpose: collect acceptable work arrangements.

Options:
- Remote
- Hybrid
- On-site
- Flexible / Any

Behavior:
- Remote, Hybrid, and On-site are multi-select and may be combined.
- **Flexible / Any is exclusive.**
  - Selecting Flexible / Any clears Remote, Hybrid, and On-site.
  - Selecting Remote, Hybrid, or On-site clears Flexible / Any.
  - Flexible / Any means no work-arrangement restriction and must not be mapped as a restrictive keyword.

Validation:
- One or more options must be selected.
- Error copy: “Choose at least one work arrangement.”

### Step 4: Visa sponsorship

Purpose: collect whether sponsorship is required.

Question:
- “I require visa sponsorship”

Control:
- Required yes/no radio group.
- Options:
  - Yes
  - No

Behavior:
- Yes: system should reject jobs explicitly stating no sponsorship and prefer/require sponsorship-positive signals.
- No: sponsorship is neutral; sponsorship text should not increase or decrease ranking solely because of sponsorship.

Validation:
- User must select Yes or No before saving.
- Error copy: “Choose whether you require visa sponsorship.”

### Wizard-to-preference mapping guidance

The wizard is the first-time user-facing input layer. Save should map wizard selections into the underlying preference object used by validation, `localStorage`, and backend classification.

Deterministic mapping for initial implementation must be based on the current role-family/default keyword groups from the existing preference DTO/classification defaults. Do not introduce new category aliases in the first implementation. If two selected categories map to the same underlying role family, merge the keyword lists and de-duplicate case-insensitively.

| Wizard selection | Underlying preference mapping |
| --- | --- |
| Python Backend | `role_positives["python backend"] = ["python backend", "backend engineer", "backend developer", "python engineer"]` |
| Backend Engineer | Add `backend engineer`, `backend developer` to the `python backend` role-positive family. |
| SDET | `role_positives["sdet"] = ["sdet", "software development engineer in test"]` |
| QA Automation | `role_positives["qa automation"] = ["qa automation", "quality assurance automation", "test automation"]` |
| Test Automation | Add `test automation` to the `qa automation` role-positive family. |
| Test Infrastructure | `role_positives["test infrastructure"] = ["test infrastructure", "testing platform", "quality platform"]` |
| Developer Productivity / Developer Experience | `role_positives["developer productivity"] = ["developer productivity", "developer experience", "engineering productivity"]` |
| Selected countries | Lowercase country names populate `location_positives`; implementation may add common city aliases later only if product-approved. |
| Remote | Populate `remote_positives` with current defaults: `remote`, `work from anywhere`, `distributed`. |
| Hybrid | No current default positive keyword group exists for Hybrid; preserve the selected wizard value in high-level metadata and do not add generated scoring keywords unless later edited in Advanced settings. |
| On-site | Treat on-site as acceptable; preserve the selected wizard value in high-level metadata and remove `on-site`/`onsite` from generated incompatible location keywords. |
| Flexible / Any | Exclusive and unrestricted: do not add generated work-arrangement positive keywords and do not add generated work-arrangement negative keywords. |
| Visa sponsorship: Yes | Keep sponsorship supported/unsupported/ambiguous keyword groups active so explicit no-sponsorship jobs are rejected and support signals are preferred. |
| Visa sponsorship: No | Make sponsorship neutral by clearing generated sponsorship-supported, unsupported, and ambiguous keyword lists unless the user later explicitly edits them in Advanced settings. |

Default negative role keywords may remain seeded in the underlying object unless changed in Advanced settings: `sales`, `account executive`, `marketing`, `recruiter`, `designer`, `hr`, `finance`.

High-level wizard metadata should be stored alongside the underlying criteria in `localStorage` so the post-setup summary can be reconstructed:

```json
{
  "wizard": {
    "categories": ["Python Backend", "SDET"],
    "countries": ["Spain", "Germany"],
    "work_arrangements": ["Remote"],
    "requires_visa_sponsorship": true
  }
}
```

This metadata is browser-local only and must be submitted only as part of the preference payload when needed for classification/reclassification workflows.

### Advanced settings section

Availability:
- Hidden during first-time setup.
- Visible only after setup completion.
- Render on `/job-preferences` as a collapsed secondary section, e.g. `<details>` with summary “Advanced settings”.

Purpose:
- Contains lower-level keyword/scoring fields from the current implementation for power users.
- Must not dominate the page visually.
- Must not be required to complete setup.
- Saved Advanced settings values are active after Save.
- If the user later changes wizard answers and saves, the wizard is the source of truth for simple generated fields and overwrites corresponding generated criteria: role positives, location positives, work arrangement positives, and sponsorship keyword lists.
- Advanced-only fields not represented by the wizard remain preserved where technically possible.

Advanced fields include:
- Role-positive family names and keywords, preserving role-family grouping.
- Negative role keywords.
- Work arrangement positive keywords.
- Preferred location keywords.
- Incompatible location keywords.
- Sponsorship supported, unsupported, and ambiguous keyword groups.

Collapsed state copy:
- Summary: “Advanced settings”
- Help: “Optional keyword controls for matching behavior. Most users do not need to edit these.”
- Warning helper: “Changing the simple wizard answers above can update generated advanced criteria for roles, locations, work arrangement, and sponsorship.”

Expanded behavior:
- Show the advanced fields as textareas/list inputs using the previous advanced pattern.
- One item per line.
- Trim whitespace, ignore blank lines, and de-duplicate case-insensitively on save.
- Preserve role-family grouping; do not merge all role keywords into one flat list.

### Apply behavior notice

- Component: `.callout.callout-info`.
- Copy before save: “Changes apply only after you save. Until then, filtering and matching continue to use your last saved preferences.”
- Copy while saving: “Saving preferences and reclassifying existing active jobs…”
- Copy after save: “Saved preferences are active. Existing active jobs were reclassified with the updated criteria.”
- Include count when backend returns it: “{count} active job(s) reclassified.”

## 8. Interaction Behavior

### Page load

- Trigger: user opens `/job-preferences`.
- System response:
  - Check `localStorage` for a usable active preference set.
  - If missing, show first-time wizard at Step 1 and hide Advanced settings.
  - If present, show post-setup edit view with Advanced settings collapsed.
- UI feedback:
  - Missing: badge **Setup required** and setup callout.
  - Saved: badge **Active** and last saved timestamp.
  - `localStorage` unavailable: blocking error and disabled Save.
- Failure behavior:
  - Malformed or unsupported saved schema: treat as setup required; show wizard and require Save before continuing.

### Wizard navigation

- Trigger: user clicks **Continue**.
- System response: validate current step only.
- Success: move to next step; focus moves to the new step heading.
- Failure: stay on current step, show step error, set invalid controls with `aria-invalid="true"`, and focus the error summary.
- Trigger: user clicks **Back**.
- System response: return to previous step without discarding selections.
- Failure: none.

### Category typeahead selection

- Trigger: user types in “Search job categories”.
- System response: filter predefined options.
- UI feedback:
  - Matching options remain selectable.
  - Selected options remain visible in a selected summary even when filtered out.
  - No-results text appears when no predefined option matches.
- Success: selecting an option toggles its selected state.
- Failure: typed text that is not a predefined option is not saved.

### Country checkbox selection

- Trigger: user checks/unchecks a country.
- System response: update draft selection.
- UI feedback: selected count may be shown, e.g. “3 countries selected.”
- Success: selections persist when navigating between wizard steps.
- Failure: attempting to continue with none selected shows the location validation error.

### Work arrangement exclusive behavior

- Trigger: user selects Flexible / Any.
- System response: clear Remote, Hybrid, and On-site selections.
- UI feedback: only Flexible / Any remains selected; helper text says “No work-arrangement restriction will be applied.”
- Trigger: user selects Remote, Hybrid, or On-site while Flexible / Any is selected.
- System response: clear Flexible / Any and select the chosen arrangement.
- Failure: none unless no option is selected on Continue/Save.

### Visa sponsorship yes/no

- Trigger: user selects Yes or No.
- System response: update draft sponsorship requirement.
- UI feedback:
  - Yes helper: “Jobs that explicitly state no sponsorship will be rejected; sponsorship-positive signals are preferred.”
  - No helper: “Sponsorship will be treated as neutral.”
- Failure: no selection on Save shows validation error.

### Save preferences

- Trigger: user clicks **Save preferences** from Step 4 or the post-setup edit view.
- System response:
  1. Preflight `localStorage` availability.
  2. Validate wizard selections or edited post-setup values.
  3. Map simplified selections into the underlying preference object. In post-setup edit mode, wizard answers overwrite corresponding generated criteria for role positives, location positives, work arrangement positives, and sponsorship lists.
  4. Trim, remove blanks, and de-duplicate case-insensitively.
  5. Preserve Advanced-only fields not represented by the wizard where technically possible.
  6. Send preferences to backend validation/reclassification.
  7. Backend validates again, reclassifies existing active jobs, and returns normalized preferences plus reclassification count.
  8. Write normalized preferences to `localStorage` only after backend success.
- Loading feedback:
  - Disable Back/Continue/Save actions that would mutate state.
  - Button text: “Saving and reclassifying…”.
  - Set `aria-busy="true"` on the form region.
- Success:
  - Alert: “Job Preferences saved. {count} active job(s) reclassified.”
  - Badge changes to **Active**.
  - Advanced settings become available collapsed on the same page.
  - Focus moves to the success alert.
  - If safe `next` is present, continue to original workflow when technically supported.
- Failure:
  - Do not update active `localStorage` preferences.
  - Preserve draft selections.
  - Validation error alert: “Fix the highlighted fields before saving.”
  - Reclassification error alert: “Preferences were not saved because existing jobs could not be reclassified. Your last saved preferences are still active.”
  - `localStorage` write error alert: “Preferences were reclassified but could not be saved in this browser. Try again after enabling browser storage.”
  - Focus moves to the error summary.

### Classification-triggering requests after setup

- Trigger: user runs source ingestion or another workflow requiring backend classification.
- System response: read active preferences from `localStorage` at submit time and include them in the request payload/form field.
- Missing/invalid preferences: redirect to `/job-preferences?next=<relative-path>` or show setup-required messaging before workflow runs.

## 9. Component States

### Wizard step panel

- Default: current step visible with heading, instructions, controls, and action row.
- Hover: not applicable at panel level.
- Focus: step heading receives focus after navigation.
- Active: current step indicated in progress component.
- Disabled: controls disabled while saving/reclassifying.
- Loading: `aria-busy="true"`; Save text “Saving and reclassifying…”.
- Success: advances to next step or shows save success.
- Error: error summary and field-level errors shown; user remains on step.
- Empty: setup starts at Step 1 with no selections.

### Category search/typeahead

- Default: empty input and all predefined options visible.
- Hover: pointer/hover style on selectable options.
- Focus: visible focus on input and options.
- Active/input: filters options as user types.
- Disabled: disabled while saving.
- Loading: not applicable for local predefined options.
- Success: selected categories appear in selected summary.
- Error: no selected categories on Continue sets `aria-invalid="true"` on group and shows error.
- Empty: no search text shows all options; no results state says no predefined categories match.

### Country checkbox list

- Default: all countries unchecked.
- Hover: pointer/hover on labels.
- Focus: visible focus on each checkbox.
- Active: checked/unchecked state updates immediately.
- Disabled: disabled while saving.
- Loading: not applicable.
- Success: selected count/summary updates.
- Error: no country selected on Continue/Save shows group error.
- Empty: allowed while editing draft, not allowed for setup completion.

### Work arrangement options

- Default: none selected in setup; saved values selected in edit mode.
- Hover/focus/active: same checkbox behavior as existing controls.
- Disabled: disabled while saving.
- Loading: not applicable beyond form loading.
- Success: selected summary updates.
- Error: no option selected on Continue/Save shows group error.
- Empty: not allowed for setup completion.
- Exclusive state: Flexible / Any selected alone; Remote/Hybrid/On-site cleared.

### Visa sponsorship radio group

- Default: no selection in setup; saved Yes/No selected in edit mode.
- Hover/focus/active: standard radio behavior.
- Disabled: disabled while saving.
- Loading: not applicable beyond form loading.
- Success: helper text reflects selected meaning.
- Error: no selection on Save shows group error.
- Empty: not allowed for setup completion.

### Advanced settings disclosure

- Default: hidden during first-time setup; collapsed after setup.
- Hover: summary uses existing link/button hover behavior if styled.
- Focus: summary is keyboard focusable with visible outline.
- Active: expanded/collapsed state toggles on click/Enter/Space.
- Disabled: not shown during first-time setup; fields disabled while saving.
- Loading: form-level loading only.
- Success: remains collapsed unless user expanded it; saved values normalized.
- Error: if an advanced field has a validation error, expand Advanced settings and focus error summary.
- Empty: advanced optional fields may be empty except where underlying positive-signal validation applies.

### Save preferences button

- Default: enabled when current step/view is valid enough to attempt save and `localStorage` is available.
- Hover: existing `.button-primary:hover` behavior.
- Focus: existing `.button:focus-visible` outline.
- Active: standard pressed state.
- Disabled: disabled while saving or when `localStorage` is unavailable.
- Loading: disabled; text “Saving and reclassifying…”.
- Success: returns to “Save preferences”; success alert shown.
- Error: returns to “Save preferences”; error alert shown.
- Empty: validation errors shown for missing required wizard selections.

## 10. Responsive Design Rules

### Desktop ≥ 981px

- Wizard panel width should remain readable; do not spread one step across too many columns.
- Category chips/checkboxes and country lists may use two or three columns if labels remain readable.
- Action row aligns consistently with existing forms.

### Tablet 721px–980px

- Wizard panel remains full width.
- Category/country lists use two columns where space permits.
- Progress indicator may wrap but must keep step order clear.

### Mobile ≤ 720px

- Single-column wizard layout.
- Country/category options stack vertically with large tap targets.
- Progress indicator uses compact text: “Step 2 of 4”.
- Back/Continue/Save buttons stack or wrap; primary action appears first visually if consistent with existing mobile patterns, otherwise remains first in source order.
- Advanced settings fields stack in one column after setup.

## 11. Visual Design Tokens

Use existing tokens in `app/web/static/styles.css`:

- Background: `--bg`.
- Surface: `--surface`.
- Muted surface: `--surface-muted`.
- Text: `--text`, `--text-muted`.
- Border: `--border`.
- Primary action: `--primary`.
- Success/active: `--matched`.
- Warning/setup required: `--review`.
- Error: `--rejected`.
- Radius: `--radius`.
- Shadow: `--shadow`.

Add only minimal wizard-specific utilities if needed, such as `.wizard-progress`, `.option-grid`, `.selected-summary`, and `.advanced-settings`.

## 12. Accessibility Requirements

- Use one `<h1>` and one visible `<h2>` for the current wizard step.
- Wizard progress must expose current step text; use `aria-current="step"` when implemented as a list.
- On step change, move focus to the new step heading.
- Every input/group must have a visible label or `<legend>`.
- Checkbox and radio groups must use `<fieldset>` and `<legend>`.
- Typeahead must not require mouse use; keyboard users can type, tab to options, and toggle predefined categories.
- Do not save arbitrary typed text from the category search field.
- Help text and errors must be connected via `aria-describedby`.
- Invalid groups must set `aria-invalid="true"` on the relevant group/control where supported.
- Error summaries must use `role="alert"` and receive focus after failed Continue/Save.
- Success confirmation should receive focus after Save.
- Loading/reclassification state must be announced through button text and/or an `aria-live="polite"` region.
- `localStorage` blocking errors must use `role="alert"`.
- Flexible / Any exclusivity must be announced through helper text and reflected in checkbox state changes.
- Advanced settings disclosure must be keyboard operable and expose expanded/collapsed state. Native `<details>/<summary>` is preferred for accessibility.

## 13. Edge Cases

- First-time user reaches `/jobs` directly: redirect/navigate to wizard at `/job-preferences?next=/jobs`; do not run filtering with hidden defaults.
- User types a non-predefined job category and presses Continue: do not save the typed text; show “Select at least one job category” if no predefined category is selected.
- Category search has no results: show no-results text and no add-custom action.
- User selects Flexible / Any after selecting Remote/Hybrid/On-site: clear other work arrangements.
- User selects Remote/Hybrid/On-site after Flexible / Any: clear Flexible / Any.
- User attempts Save without sponsorship Yes/No: show radio-group error.
- User refreshes mid-wizard before Save: setup remains incomplete because draft values are not active preferences.
- `localStorage` is unavailable/full/cleared: show blocking error; do not mark setup complete.
- Backend reclassification fails during Save: do not write draft preferences to `localStorage`; keep last saved preferences active.
- Existing saved preferences are malformed or schema-incompatible: show wizard repair flow and require Save.
- Advanced settings contain invalid edits after setup: expand Advanced settings and show field-specific errors.
- Existing advanced values cannot be represented cleanly in simplified summary: show the four summary sections from saved high-level wizard metadata; if metadata is absent, show “Advanced custom preferences active” and keep Advanced settings available for review.
- User saves Advanced settings, then later changes wizard answers: wizard-generated criteria overwrite role positives, location positives, work arrangement positives, and sponsorship lists; Advanced-only fields not represented by the wizard remain preserved where technically possible.

## 14. Developer Handoff Notes

- Update `/job-preferences` to render wizard-first setup when no usable active preferences exist in `localStorage`.
- Hide Advanced settings during first-time setup.
- After setup completion, render Advanced settings on the same page as collapsed secondary content.
- Preserve browser-local `localStorage` persistence only; do not add auth, DynamoDB, backend DB, backend session, or cloud preference persistence.
- Preserve Save-gated behavior: draft wizard changes do not affect filtering until Save succeeds.
- Preserve immediate reclassification after successful Save and include reclassified count in success copy when available.
- Preserve role-family grouping in the underlying preference object and in Advanced settings.
- Do not allow custom/free-text saved job categories in Step 1.
- Store high-level wizard metadata in `localStorage` alongside underlying criteria so post-setup summaries remain reconstructable.
- When wizard answers are saved after Advanced edits, treat wizard answers as source of truth for generated simple criteria and show helper warning copy before Save.
- Ensure source-run/classification-triggering forms read active preferences from `localStorage` at submit time and submit preferences per request.
- Prior all-fields-first layout is superseded only for first-time setup; its lower-level controls move to post-setup Advanced settings.

Remaining risks:
- Server-rendered pages cannot read `localStorage`; client guard plus optional non-sensitive marker cookie may cause a brief render before redirect if only client guard is used. This is a known non-blocking technical limitation.
