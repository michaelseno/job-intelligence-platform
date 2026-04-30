document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('[data-sidebar]');
  const toggle = document.querySelector('[data-sidebar-toggle]');
  const backdrop = document.querySelector('[data-sidebar-backdrop]');
  const focusableSelector = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
  let previousFocus = null;
  const closeSidebar = () => { if (!sidebar || !toggle) return; sidebar.classList.remove('is-open'); document.body.classList.remove('sidebar-open'); toggle.setAttribute('aria-expanded', 'false'); if (window.matchMedia('(max-width: 1023px)').matches && previousFocus instanceof HTMLElement) previousFocus.focus(); };
  const openSidebar = () => { if (!sidebar || !toggle) return; previousFocus = document.activeElement; sidebar.classList.add('is-open'); document.body.classList.add('sidebar-open'); toggle.setAttribute('aria-expanded', 'true'); const first = sidebar.querySelector(focusableSelector); if (first instanceof HTMLElement) first.focus(); else sidebar.focus(); };
  if (sidebar && toggle) {
    toggle.addEventListener('click', () => { if (sidebar.classList.contains('is-open')) closeSidebar(); else openSidebar(); });
    if (backdrop) backdrop.addEventListener('click', closeSidebar);
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && sidebar.classList.contains('is-open')) closeSidebar(); });
  }
  document.querySelectorAll('form[data-clean-empty-query="true"]').forEach((form) => form.addEventListener('submit', () => form.querySelectorAll('input[name], select[name], textarea[name]').forEach((field) => { if (!field.value) field.disabled = true; })));
  initPreferenceGuards();
  initJobPreferencesPage();
  initSourceBatchRuns();
});

const CATEGORY_OPTIONS = [
  { id: 'python_backend', label: 'Python Backend', family: 'python backend', keywords: ['python backend', 'python engineer'] },
  { id: 'backend_engineer', label: 'Backend Engineer', family: 'backend engineer', keywords: ['backend engineer', 'backend developer'] },
  { id: 'sdet', label: 'SDET', family: 'sdet', keywords: ['sdet', 'software development engineer in test'] },
  { id: 'qa_automation', label: 'QA Automation', family: 'qa automation', keywords: ['qa automation', 'quality assurance automation'] },
  { id: 'test_automation', label: 'Test Automation', family: 'test automation', keywords: ['test automation'] },
  { id: 'test_infrastructure', label: 'Test Infrastructure', family: 'test infrastructure', keywords: ['test infrastructure', 'testing platform', 'quality platform'] },
  { id: 'developer_productivity', label: 'Developer Productivity / Developer Experience', family: 'developer productivity', keywords: ['developer productivity', 'developer experience', 'engineering productivity'] },
];
const REGION_GROUPS = [
  { id: 'europe', label: 'Europe' }, { id: 'asia', label: 'Asia' }, { id: 'north_america', label: 'North America' }, { id: 'australia_new_zealand', label: 'Australia / New Zealand' }, { id: 'africa', label: 'Africa' }, { id: 'south_america', label: 'South America' }, { id: 'middle_east', label: 'Middle East' }, { id: 'central_america', label: 'Central America' }, { id: 'caribbean', label: 'Caribbean' }, { id: 'oceania', label: 'Oceania' }, { id: 'antarctica', label: 'Antarctica' },
];
const COUNTRY_OPTIONS = [
  ['aland_islands', 'Åland Islands', 'Europe'], ['albania', 'Albania', 'Europe'], ['andorra', 'Andorra', 'Europe'], ['austria', 'Austria', 'Europe'], ['belarus', 'Belarus', 'Europe'], ['belgium', 'Belgium', 'Europe'], ['bosnia_and_herzegovina', 'Bosnia and Herzegovina', 'Europe'], ['bulgaria', 'Bulgaria', 'Europe'], ['croatia', 'Croatia', 'Europe'], ['cyprus', 'Cyprus', 'Europe'], ['czech_republic', 'Czech Republic', 'Europe', ['czechia']], ['denmark', 'Denmark', 'Europe'], ['estonia', 'Estonia', 'Europe'], ['faroe_islands', 'Faroe Islands', 'Europe'], ['finland', 'Finland', 'Europe'], ['france', 'France', 'Europe'], ['germany', 'Germany', 'Europe'], ['gibraltar', 'Gibraltar', 'Europe'], ['greece', 'Greece', 'Europe'], ['guernsey', 'Guernsey', 'Europe'], ['holy_see', 'Holy See', 'Europe', ['vatican', 'vatican city']], ['hungary', 'Hungary', 'Europe'], ['iceland', 'Iceland', 'Europe'], ['ireland', 'Ireland', 'Europe'], ['isle_of_man', 'Isle of Man', 'Europe'], ['italy', 'Italy', 'Europe'], ['jersey', 'Jersey', 'Europe'], ['latvia', 'Latvia', 'Europe'], ['liechtenstein', 'Liechtenstein', 'Europe'], ['lithuania', 'Lithuania', 'Europe'], ['luxembourg', 'Luxembourg', 'Europe'], ['malta', 'Malta', 'Europe'], ['moldova', 'Moldova', 'Europe'], ['monaco', 'Monaco', 'Europe'], ['montenegro', 'Montenegro', 'Europe'], ['netherlands', 'Netherlands', 'Europe', ['holland']], ['north_macedonia', 'North Macedonia', 'Europe'], ['norway', 'Norway', 'Europe'], ['poland', 'Poland', 'Europe'], ['portugal', 'Portugal', 'Europe'], ['romania', 'Romania', 'Europe'], ['russia', 'Russia', 'Europe', ['russian federation']], ['san_marino', 'San Marino', 'Europe'], ['serbia', 'Serbia', 'Europe'], ['slovakia', 'Slovakia', 'Europe'], ['slovenia', 'Slovenia', 'Europe'], ['spain', 'Spain', 'Europe'], ['svalbard_and_jan_mayen', 'Svalbard and Jan Mayen', 'Europe'], ['sweden', 'Sweden', 'Europe'], ['switzerland', 'Switzerland', 'Europe'], ['ukraine', 'Ukraine', 'Europe'], ['united_kingdom', 'United Kingdom', 'Europe', ['uk', 'britain', 'great britain']],
  ['afghanistan', 'Afghanistan', 'Asia'], ['armenia', 'Armenia', 'Asia'], ['azerbaijan', 'Azerbaijan', 'Asia'], ['bangladesh', 'Bangladesh', 'Asia'], ['bhutan', 'Bhutan', 'Asia'], ['brunei_darussalam', 'Brunei Darussalam', 'Asia', ['brunei']], ['cambodia', 'Cambodia', 'Asia'], ['china', 'China', 'Asia'], ['georgia', 'Georgia', 'Asia'], ['hong_kong', 'Hong Kong', 'Asia', ['hk']], ['india', 'India', 'Asia'], ['indonesia', 'Indonesia', 'Asia'], ['japan', 'Japan', 'Asia'], ['kazakhstan', 'Kazakhstan', 'Asia'], ['kyrgyzstan', 'Kyrgyzstan', 'Asia'], ['lao_peoples_democratic_republic', "Lao People's Democratic Republic", 'Asia', ['laos']], ['macao', 'Macao', 'Asia', ['macau']], ['malaysia', 'Malaysia', 'Asia'], ['maldives', 'Maldives', 'Asia'], ['mongolia', 'Mongolia', 'Asia'], ['myanmar', 'Myanmar', 'Asia', ['burma']], ['nepal', 'Nepal', 'Asia'], ['north_korea', 'North Korea', 'Asia', ['korea democratic people republic']], ['pakistan', 'Pakistan', 'Asia'], ['philippines', 'Philippines', 'Asia'], ['singapore', 'Singapore', 'Asia'], ['south_korea', 'South Korea', 'Asia', ['korea', 'republic of korea']], ['sri_lanka', 'Sri Lanka', 'Asia'], ['taiwan', 'Taiwan', 'Asia'], ['tajikistan', 'Tajikistan', 'Asia'], ['thailand', 'Thailand', 'Asia'], ['timor_leste', 'Timor-Leste', 'Asia', ['east timor']], ['turkmenistan', 'Turkmenistan', 'Asia'], ['uzbekistan', 'Uzbekistan', 'Asia'], ['vietnam', 'Vietnam', 'Asia'],
  ['canada', 'Canada', 'North America'], ['greenland', 'Greenland', 'North America'], ['mexico', 'Mexico', 'North America'], ['saint_pierre_and_miquelon', 'Saint Pierre and Miquelon', 'North America'], ['united_states', 'United States', 'North America', ['us', 'usa', 'united states of america']],
  ['australia', 'Australia', 'Australia / New Zealand'], ['new_zealand', 'New Zealand', 'Australia / New Zealand'],
  ['algeria', 'Algeria', 'Africa'], ['angola', 'Angola', 'Africa'], ['benin', 'Benin', 'Africa'], ['botswana', 'Botswana', 'Africa'], ['bouvet_island', 'Bouvet Island', 'Africa'], ['british_indian_ocean_territory', 'British Indian Ocean Territory', 'Africa'], ['burkina_faso', 'Burkina Faso', 'Africa'], ['burundi', 'Burundi', 'Africa'], ['cabo_verde', 'Cabo Verde', 'Africa', ['cape verde']], ['cameroon', 'Cameroon', 'Africa'], ['central_african_republic', 'Central African Republic', 'Africa'], ['chad', 'Chad', 'Africa'], ['comoros', 'Comoros', 'Africa'], ['congo', 'Congo', 'Africa'], ['democratic_republic_of_the_congo', 'Democratic Republic of the Congo', 'Africa', ['congo drc']], ['cote_d_ivoire', "Côte d'Ivoire", 'Africa', ['ivory coast', 'cote d ivoire']], ['djibouti', 'Djibouti', 'Africa'], ['egypt', 'Egypt', 'Africa'], ['equatorial_guinea', 'Equatorial Guinea', 'Africa'], ['eritrea', 'Eritrea', 'Africa'], ['eswatini', 'Eswatini', 'Africa', ['swaziland']], ['ethiopia', 'Ethiopia', 'Africa'], ['french_southern_territories', 'French Southern Territories', 'Africa'], ['gabon', 'Gabon', 'Africa'], ['gambia', 'Gambia', 'Africa'], ['ghana', 'Ghana', 'Africa'], ['guinea', 'Guinea', 'Africa'], ['guinea_bissau', 'Guinea-Bissau', 'Africa'], ['kenya', 'Kenya', 'Africa'], ['lesotho', 'Lesotho', 'Africa'], ['liberia', 'Liberia', 'Africa'], ['libya', 'Libya', 'Africa'], ['madagascar', 'Madagascar', 'Africa'], ['malawi', 'Malawi', 'Africa'], ['mali', 'Mali', 'Africa'], ['mauritania', 'Mauritania', 'Africa'], ['mauritius', 'Mauritius', 'Africa'], ['mayotte', 'Mayotte', 'Africa'], ['morocco', 'Morocco', 'Africa'], ['mozambique', 'Mozambique', 'Africa'], ['namibia', 'Namibia', 'Africa'], ['niger', 'Niger', 'Africa'], ['nigeria', 'Nigeria', 'Africa'], ['reunion', 'Réunion', 'Africa', ['reunion']], ['rwanda', 'Rwanda', 'Africa'], ['saint_helena_ascension_and_tristan_da_cunha', 'Saint Helena, Ascension and Tristan da Cunha', 'Africa'], ['sao_tome_and_principe', 'Sao Tome and Principe', 'Africa'], ['senegal', 'Senegal', 'Africa'], ['seychelles', 'Seychelles', 'Africa'], ['sierra_leone', 'Sierra Leone', 'Africa'], ['somalia', 'Somalia', 'Africa'], ['south_africa', 'South Africa', 'Africa'], ['south_sudan', 'South Sudan', 'Africa'], ['sudan', 'Sudan', 'Africa'], ['tanzania', 'Tanzania', 'Africa'], ['togo', 'Togo', 'Africa'], ['tunisia', 'Tunisia', 'Africa'], ['uganda', 'Uganda', 'Africa'], ['western_sahara', 'Western Sahara', 'Africa'], ['zambia', 'Zambia', 'Africa'], ['zimbabwe', 'Zimbabwe', 'Africa'],
  ['argentina', 'Argentina', 'South America'], ['bolivia', 'Bolivia', 'South America'], ['brazil', 'Brazil', 'South America'], ['chile', 'Chile', 'South America'], ['colombia', 'Colombia', 'South America'], ['ecuador', 'Ecuador', 'South America'], ['falkland_islands', 'Falkland Islands', 'South America', ['malvinas']], ['french_guiana', 'French Guiana', 'South America'], ['guyana', 'Guyana', 'South America'], ['paraguay', 'Paraguay', 'South America'], ['peru', 'Peru', 'South America'], ['suriname', 'Suriname', 'South America'], ['uruguay', 'Uruguay', 'South America'], ['venezuela', 'Venezuela', 'South America'],
  ['bahrain', 'Bahrain', 'Middle East'], ['iran', 'Iran', 'Middle East'], ['iraq', 'Iraq', 'Middle East'], ['israel', 'Israel', 'Middle East'], ['jordan', 'Jordan', 'Middle East'], ['kuwait', 'Kuwait', 'Middle East'], ['lebanon', 'Lebanon', 'Middle East'], ['oman', 'Oman', 'Middle East'], ['palestine', 'Palestine', 'Middle East', ['palestinian territories']], ['qatar', 'Qatar', 'Middle East'], ['saudi_arabia', 'Saudi Arabia', 'Middle East'], ['syrian_arab_republic', 'Syrian Arab Republic', 'Middle East', ['syria']], ['turkey', 'Turkey', 'Middle East', ['turkiye', 'türkiye']], ['united_arab_emirates', 'United Arab Emirates', 'Middle East', ['uae']], ['yemen', 'Yemen', 'Middle East'],
  ['belize', 'Belize', 'Central America'], ['costa_rica', 'Costa Rica', 'Central America'], ['el_salvador', 'El Salvador', 'Central America'], ['guatemala', 'Guatemala', 'Central America'], ['honduras', 'Honduras', 'Central America'], ['nicaragua', 'Nicaragua', 'Central America'], ['panama', 'Panama', 'Central America'],
  ['anguilla', 'Anguilla', 'Caribbean'], ['antigua_and_barbuda', 'Antigua and Barbuda', 'Caribbean'], ['aruba', 'Aruba', 'Caribbean'], ['bahamas', 'Bahamas', 'Caribbean'], ['barbados', 'Barbados', 'Caribbean'], ['bermuda', 'Bermuda', 'Caribbean'], ['bonaire_sint_eustatius_and_saba', 'Bonaire, Sint Eustatius and Saba', 'Caribbean'], ['cayman_islands', 'Cayman Islands', 'Caribbean'], ['cuba', 'Cuba', 'Caribbean'], ['curacao', 'Curaçao', 'Caribbean', ['curacao']], ['dominica', 'Dominica', 'Caribbean'], ['dominican_republic', 'Dominican Republic', 'Caribbean'], ['grenada', 'Grenada', 'Caribbean'], ['guadeloupe', 'Guadeloupe', 'Caribbean'], ['haiti', 'Haiti', 'Caribbean'], ['jamaica', 'Jamaica', 'Caribbean'], ['martinique', 'Martinique', 'Caribbean'], ['montserrat', 'Montserrat', 'Caribbean'], ['puerto_rico', 'Puerto Rico', 'Caribbean'], ['saint_barthelemy', 'Saint Barthélemy', 'Caribbean', ['st barthelemy']], ['saint_kitts_and_nevis', 'Saint Kitts and Nevis', 'Caribbean'], ['saint_lucia', 'Saint Lucia', 'Caribbean'], ['saint_martin', 'Saint Martin', 'Caribbean'], ['saint_vincent_and_the_grenadines', 'Saint Vincent and the Grenadines', 'Caribbean'], ['sint_maarten', 'Sint Maarten', 'Caribbean'], ['trinidad_and_tobago', 'Trinidad and Tobago', 'Caribbean'], ['turks_and_caicos_islands', 'Turks and Caicos Islands', 'Caribbean'], ['virgin_islands_british', 'Virgin Islands (British)', 'Caribbean'], ['virgin_islands_us', 'Virgin Islands (U.S.)', 'Caribbean'],
  ['american_samoa', 'American Samoa', 'Oceania'], ['christmas_island', 'Christmas Island', 'Oceania'], ['cocos_keeling_islands', 'Cocos (Keeling) Islands', 'Oceania'], ['cook_islands', 'Cook Islands', 'Oceania'], ['fiji', 'Fiji', 'Oceania'], ['french_polynesia', 'French Polynesia', 'Oceania'], ['guam', 'Guam', 'Oceania'], ['heard_island_and_mcdonald_islands', 'Heard Island and McDonald Islands', 'Oceania'], ['kiribati', 'Kiribati', 'Oceania'], ['marshall_islands', 'Marshall Islands', 'Oceania'], ['micronesia', 'Micronesia', 'Oceania'], ['nauru', 'Nauru', 'Oceania'], ['new_caledonia', 'New Caledonia', 'Oceania'], ['niue', 'Niue', 'Oceania'], ['norfolk_island', 'Norfolk Island', 'Oceania'], ['northern_mariana_islands', 'Northern Mariana Islands', 'Oceania'], ['palau', 'Palau', 'Oceania'], ['papua_new_guinea', 'Papua New Guinea', 'Oceania'], ['pitcairn', 'Pitcairn', 'Oceania'], ['samoa', 'Samoa', 'Oceania'], ['solomon_islands', 'Solomon Islands', 'Oceania'], ['tokelau', 'Tokelau', 'Oceania'], ['tonga', 'Tonga', 'Oceania'], ['tuvalu', 'Tuvalu', 'Oceania'], ['united_states_minor_outlying_islands', 'United States Minor Outlying Islands', 'Oceania'], ['vanuatu', 'Vanuatu', 'Oceania'], ['wallis_and_futuna', 'Wallis and Futuna', 'Oceania'],
  ['antarctica', 'Antarctica', 'Antarctica'], ['south_georgia_and_the_south_sandwich_islands', 'South Georgia and the South Sandwich Islands', 'Antarctica'],
].map(([id, label, region, aliases = []]) => ({ id, label, region, search_aliases: aliases, location_keywords: dedupe([label.toLocaleLowerCase(), ...aliases]) }));
const DEFAULT_ROLE_NEGATIVES = ['sales', 'account executive', 'marketing', 'recruiter', 'designer', 'hr', 'finance'];
const DEFAULT_SPONSORSHIP_SUPPORTED = ['visa sponsorship available', 'sponsorship available', 'will sponsor'];
const DEFAULT_SPONSORSHIP_UNSUPPORTED = ['no visa sponsorship', 'unable to sponsor', 'must be authorized to work'];
const DEFAULT_SPONSORSHIP_AMBIGUOUS = ['visa', 'work authorization', 'sponsorship'];
const COUNTRY_IDS = new Set(COUNTRY_OPTIONS.map((option) => option.id));
const COUNTRIES_BY_REGION = REGION_GROUPS.map((region) => ({ ...region, countries: COUNTRY_OPTIONS.filter((country) => country.region === region.label) }));

function dedupe(values) { const seen = new Set(); const out = []; values.forEach((value) => { const trimmed = String(value || '').trim(); const key = trimmed.toLocaleLowerCase(); if (trimmed && !seen.has(key)) { seen.add(key); out.push(trimmed); } }); return out; }
function normalizeKeywordLines(text) { return dedupe(String(text || '').split(/\r?\n/)); }
function listFromIds(ids, options, field) { return dedupe(ids.flatMap((id) => (options.find((option) => option.id === id) || {})[field] || [])); }
function validWizard(wizard) { return Boolean(wizard && Array.isArray(wizard.selected_categories) && wizard.selected_categories.length && Array.isArray(wizard.selected_countries) && wizard.selected_countries.length && Array.isArray(wizard.work_arrangements) && wizard.work_arrangements.length && typeof wizard.requires_visa_sponsorship === 'boolean'); }
function defaultWizard() { return { schema_version: 1, selected_categories: [], selected_countries: [], work_arrangements: [], requires_visa_sponsorship: null }; }
function normalizeWizard(wizard) {
  const source = { ...defaultWizard(), ...(wizard || {}) };
  const categoryIds = new Set(CATEGORY_OPTIONS.map((option) => option.id));
  const countryIds = new Set(COUNTRY_OPTIONS.map((option) => option.id));
  let work = (source.work_arrangements || []).filter((value) => ['remote', 'hybrid', 'onsite', 'any'].includes(value));
  if (work.includes('any')) work = ['any'];
  return { schema_version: 1, selected_categories: dedupe(source.selected_categories || []).filter((id) => categoryIds.has(id)), selected_countries: dedupe(source.selected_countries || []).filter((id) => countryIds.has(id)), work_arrangements: dedupe(work), requires_visa_sponsorship: typeof source.requires_visa_sponsorship === 'boolean' ? source.requires_visa_sponsorship : null };
}
function mapWizardToPreferences(wizard, basePreferences = {}) {
  const normalized = normalizeWizard(wizard);
  const role_positives = {};
  normalized.selected_categories.forEach((id) => { const option = CATEGORY_OPTIONS.find((item) => item.id === id); if (!option) return; role_positives[option.family] = dedupe([...(role_positives[option.family] || []), ...option.keywords]); });
  const remote = [];
  if (normalized.work_arrangements.includes('remote')) remote.push('remote', 'work from anywhere', 'distributed');
  if (normalized.work_arrangements.includes('hybrid')) remote.push('hybrid');
  if (normalized.work_arrangements.includes('onsite')) remote.push('on-site', 'onsite');
  return { schema_version: 1, role_positives, role_negatives: dedupe(basePreferences.role_negatives || DEFAULT_ROLE_NEGATIVES), remote_positives: dedupe(remote), location_positives: listFromIds(normalized.selected_countries, COUNTRY_OPTIONS, 'location_keywords'), location_negatives: dedupe(basePreferences.location_negatives || []), sponsorship_supported: normalized.requires_visa_sponsorship ? DEFAULT_SPONSORSHIP_SUPPORTED : [], sponsorship_unsupported: normalized.requires_visa_sponsorship ? DEFAULT_SPONSORSHIP_UNSUPPORTED : [], sponsorship_ambiguous: normalized.requires_visa_sponsorship ? DEFAULT_SPONSORSHIP_AMBIGUOUS : [] };
}
function isPreferencePayload(value) { return Boolean(value && value.schema_version === 1 && value.role_positives && Array.isArray(value.role_negatives)); }
function extractPreferences(value) { if (!value) return null; if (isPreferencePayload(value.preferences)) return value.preferences; if (isPreferencePayload(value)) return value; return null; }
function createPreferenceEnvelope(wizard, preferences, advancedCustomized = false) { return { schema_version: 1, configured_at: preferences.configured_at || new Date().toISOString(), setup_mode: 'wizard', wizard: normalizeWizard(wizard), preferences, advanced_customized: Boolean(advancedCustomized) }; }
function editablePreferenceSnapshot(preferences) { const source = extractPreferences(preferences) || {}; const roleSource = source.role_positives && typeof source.role_positives === 'object' ? source.role_positives : {}; const role_positives = {}; Object.keys(roleSource).sort((a, b) => a.localeCompare(b)).forEach((family) => { role_positives[family] = Array.isArray(roleSource[family]) ? [...roleSource[family]] : []; }); const list = (field) => (Array.isArray(source[field]) ? [...source[field]] : []); return { schema_version: source.schema_version, role_positives, role_negatives: list('role_negatives'), remote_positives: list('remote_positives'), location_positives: list('location_positives'), location_negatives: list('location_negatives'), sponsorship_supported: list('sponsorship_supported'), sponsorship_unsupported: list('sponsorship_unsupported'), sponsorship_ambiguous: list('sponsorship_ambiguous') }; }
function preferencesEqual(left, right) { return JSON.stringify(editablePreferenceSnapshot(left)) === JSON.stringify(editablePreferenceSnapshot(right)); }
function safeNextPath(value) { if (!value || !value.startsWith('/') || value.startsWith('//')) return ''; try { const parsed = new URL(value, window.location.origin); return parsed.origin === window.location.origin ? `${parsed.pathname}${parsed.search}${parsed.hash}` : ''; } catch (_e) { return ''; } }
function hasPositiveSignal(preferences) { const p = extractPreferences(preferences); return Boolean(p && (Object.values(p.role_positives || {}).some((values) => values.length) || (p.remote_positives || []).length || (p.location_positives || []).length)); }

const JobPreferencesStore = (() => {
  const KEY = 'job_intelligence.job_filter_preferences.v1';
  function isStorageAvailable() { try { const probe = `${KEY}.probe`; window.localStorage.setItem(probe, '1'); window.localStorage.removeItem(probe); return true; } catch (_e) { return false; } }
  function readEnvelope() { if (!isStorageAvailable()) return null; try { const parsed = JSON.parse(window.localStorage.getItem(KEY) || 'null'); const preferences = extractPreferences(parsed); return preferences && hasPositiveSignal(preferences) ? (parsed.preferences ? parsed : createPreferenceEnvelope(null, preferences, true)) : null; } catch (_e) { return null; } }
  function read() { const envelope = readEnvelope(); return envelope ? envelope.preferences : null; }
  function write(value) { window.localStorage.setItem(KEY, JSON.stringify(value && value.preferences ? value : createPreferenceEnvelope(null, value, true))); }
  function writeEnvelope(envelope) { window.localStorage.setItem(KEY, JSON.stringify(envelope)); }
  function redirectToSetup() { const current = `${window.location.pathname}${window.location.search}`; const target = new URL('/job-preferences', window.location.origin); target.searchParams.set('next', current || '/dashboard'); window.location.assign(target.toString()); }
  return { KEY, isStorageAvailable, readEnvelope, read, write, writeEnvelope, redirectToSetup };
})();

function initPreferenceGuards() { const shell = document.querySelector('.app-shell'); if (!shell || shell.dataset.requiresJobPreferences !== 'true') return; if (JobPreferencesStore.read()) return; JobPreferencesStore.redirectToSetup(); }

function initJobPreferencesPage() {
  const root = document.getElementById('job-preferences-root'); if (!root) return;
  const form = document.getElementById('job-preferences-form'); const defaults = JSON.parse(root.dataset.defaultPreferences || '{}'); const nextUrl = safeNextPath(root.dataset.next || '');
  const elements = { title: document.getElementById('job-preferences-page-title'), desc: document.getElementById('job-preferences-page-description'), badge: document.getElementById('job-preferences-status-badge'), lastSaved: document.getElementById('job-preferences-last-saved'), setup: document.getElementById('job-preferences-setup-callout'), storage: document.getElementById('job-preferences-storage-error'), message: document.getElementById('job-preferences-message'), progress: document.getElementById('job-preferences-progress'), back: document.getElementById('wizard-back'), next: document.getElementById('wizard-next'), save: document.getElementById('job-preferences-save'), reset: document.getElementById('job-preferences-reset'), cont: document.getElementById('job-preferences-continue'), unsaved: document.getElementById('job-preferences-unsaved-note'), advanced: document.getElementById('advanced-settings'), apply: document.getElementById('job-preferences-apply-copy') };
  let envelope = JobPreferencesStore.readEnvelope(); let activePreferences = envelope ? envelope.preferences : null; let unmatchedSavedCountryIds = envelope && envelope.wizard && Array.isArray(envelope.wizard.selected_countries) ? dedupe(envelope.wizard.selected_countries).filter((id) => !COUNTRY_IDS.has(id)) : []; let wizard = normalizeWizard(envelope && envelope.wizard ? envelope.wizard : defaultWizard()); let currentStep = 0; let baselineWizard = JSON.stringify(wizard); let baselinePreferences = editablePreferenceSnapshot(activePreferences || mapWizardToPreferences(wizard, defaults));
  const isSetup = () => !activePreferences;
  const field = (name) => form.querySelector(`[data-pref-field="${name}"]`);
  const selected = (name) => Array.from(form.querySelectorAll(`input[name="${name}"]:checked`)).map((input) => input.value);
  function setAlert(type, text, focus = false) { const t = type === 'error' ? 'danger' : type; elements.message.className = `alert alert--${t}`; elements.message.textContent = text; elements.message.setAttribute('role', type === 'error' ? 'alert' : 'status'); elements.message.classList.remove('hidden'); if (focus) elements.message.focus(); }
  function clearAlert() { elements.message.className = 'alert hidden'; elements.message.textContent = ''; elements.message.removeAttribute('role'); }
  function setStatus(state) { elements.badge.className = `badge badge--${state === 'active' ? 'success' : 'warning'}`; elements.badge.textContent = state === 'active' ? 'Active' : state === 'unsaved' ? 'Unsaved changes' : 'Setup required'; elements.setup.classList.toggle('hidden', state !== 'setup'); }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char])); }
  function countryMatches(option, query, regionLabel) { if (!query) return true; const haystack = [option.id, option.label, ...(option.search_aliases || []), ...(option.location_keywords || []), regionLabel].join(' ').toLocaleLowerCase(); return haystack.includes(query); }
  function shouldOpenRegion(region, query) { if (query) return true; if (wizard.selected_countries.some((id) => region.countries.some((country) => country.id === id))) return true; return ['Europe', 'Asia'].includes(region.label) && !wizard.selected_countries.length; }
  function renderOptions() { const group = document.getElementById('category-group'); const q = (document.getElementById('category-search').value || '').toLocaleLowerCase(); group.innerHTML = ''; const matches = CATEGORY_OPTIONS.filter((o) => o.label.toLocaleLowerCase().includes(q)); matches.forEach((option) => { const label = document.createElement('label'); label.innerHTML = `<input type="checkbox" name="selected_categories" value="${option.id}"> ${option.label}`; group.appendChild(label); label.querySelector('input').checked = wizard.selected_categories.includes(option.id); }); document.getElementById('category-empty').classList.toggle('hidden', matches.length > 0); renderCountryGroups(); syncInputs(); }
  function renderCountryGroups() { const container = document.getElementById('country-group'); if (!container) return; const query = (document.getElementById('location-search')?.value || '').trim().toLocaleLowerCase(); container.innerHTML = ''; let visibleRegions = 0; COUNTRIES_BY_REGION.forEach((region) => { const regionMatches = query && region.label.toLocaleLowerCase().includes(query); const visibleCountries = regionMatches ? region.countries : region.countries.filter((country) => countryMatches(country, query, region.label)); if (query && !regionMatches && !visibleCountries.length) return; visibleRegions += 1; const details = document.createElement('details'); details.className = 'location-region'; details.dataset.region = region.id; if (shouldOpenRegion(region, query)) details.open = true; const countriesHtml = visibleCountries.map((option) => `<label><input type="checkbox" name="selected_countries" value="${escapeHtml(option.id)}"> ${escapeHtml(option.label)}</label>`).join(''); details.innerHTML = `<summary class="location-region__summary"><input class="region-checkbox" type="checkbox" value="${escapeHtml(region.id)}" aria-label="Select all countries in ${escapeHtml(region.label)}" data-region-checkbox="${escapeHtml(region.id)}"><span class="location-region__name">${escapeHtml(region.label)}</span><span class="location-region__count" data-region-count="${escapeHtml(region.id)}">0 of ${region.countries.length} selected</span></summary><fieldset class="option-grid option-grid--countries" aria-describedby="country-error"><legend class="sr-only">Countries in ${escapeHtml(region.label)}</legend>${countriesHtml}</fieldset>`; container.appendChild(details); }); document.getElementById('country-empty')?.classList.toggle('hidden', visibleRegions > 0); }
  function syncRegionStates() { COUNTRIES_BY_REGION.forEach((region) => { const selectedCount = region.countries.filter((country) => wizard.selected_countries.includes(country.id)).length; const checkbox = form.querySelector(`input[data-region-checkbox="${region.id}"]`); if (checkbox) { checkbox.checked = Boolean(selectedCount && selectedCount === region.countries.length); checkbox.indeterminate = selectedCount > 0 && selectedCount < region.countries.length; checkbox.setAttribute('aria-checked', checkbox.indeterminate ? 'mixed' : String(checkbox.checked)); } const count = form.querySelector(`[data-region-count="${region.id}"]`); if (count) count.textContent = `${selectedCount} of ${region.countries.length} selected`; }); }
  function syncInputs() { form.querySelectorAll('input[name="selected_categories"]').forEach((input) => { input.checked = wizard.selected_categories.includes(input.value); }); form.querySelectorAll('input[name="selected_countries"]').forEach((input) => { input.checked = wizard.selected_countries.includes(input.value); }); form.querySelectorAll('input[name="work_arrangements"]').forEach((input) => { input.checked = wizard.work_arrangements.includes(input.value); }); form.querySelectorAll('input[name="requires_visa_sponsorship"]').forEach((input) => { input.checked = String(wizard.requires_visa_sponsorship) === input.value; }); document.getElementById('category-summary').textContent = wizard.selected_categories.length ? `${wizard.selected_categories.length} selected: ${wizard.selected_categories.map((id) => CATEGORY_OPTIONS.find((o) => o.id === id).label).join(', ')}` : 'No categories selected.'; const count = wizard.selected_countries.filter((id) => COUNTRY_IDS.has(id)).length; document.getElementById('country-summary').textContent = count === 1 ? '1 country selected.' : count ? `${count} countries selected.` : 'No countries selected.'; document.getElementById('location-clear')?.toggleAttribute('disabled', count === 0 || elements.save.disabled); document.getElementById('country-legacy-warning')?.classList.toggle('hidden', unmatchedSavedCountryIds.length === 0); syncRegionStates(); }
  function setStep(step) { currentStep = step; document.querySelectorAll('[data-wizard-step]').forEach((panel) => panel.classList.toggle('hidden', Number(panel.dataset.wizardStep) !== step && isSetup())); document.querySelectorAll('[data-step-indicator]').forEach((item) => { const active = Number(item.dataset.stepIndicator) === step; if (active) item.setAttribute('aria-current', 'step'); else item.removeAttribute('aria-current'); }); elements.back.classList.toggle('hidden', !isSetup() || step === 0); elements.next.classList.toggle('hidden', !isSetup() || step === 3); elements.save.classList.toggle('hidden', isSetup() && step !== 3); const heading = document.querySelector(`[data-wizard-step="${step}"] h2`); if (heading && document.activeElement !== document.body) heading.focus(); }
  function collectWizardFromInputs() { wizard.selected_categories = selected('selected_categories'); const renderedCountryIds = Array.from(form.querySelectorAll('input[name="selected_countries"]')).map((input) => input.value); const renderedSelectedCountryIds = selected('selected_countries'); wizard.selected_countries = dedupe([...wizard.selected_countries.filter((id) => !renderedCountryIds.includes(id)), ...renderedSelectedCountryIds]); const work = selected('work_arrangements'); wizard.work_arrangements = work.includes('any') ? ['any'] : work; const visa = form.querySelector('input[name="requires_visa_sponsorship"]:checked'); wizard.requires_visa_sponsorship = visa ? visa.value === 'true' : null; wizard = normalizeWizard(wizard); syncInputs(); }
  function validateStep(step) { collectWizardFromInputs(); document.querySelectorAll('[data-step-error]').forEach((node) => { node.textContent = ''; }); const errors = { 0: ['categories', 'Select at least one job category.', wizard.selected_categories.length], 1: ['countries', 'Select at least one country.', wizard.selected_countries.length], 2: ['work_arrangements', 'Choose at least one work arrangement.', wizard.work_arrangements.length], 3: ['requires_visa_sponsorship', 'Choose whether you require visa sponsorship.', typeof wizard.requires_visa_sponsorship === 'boolean'] }[step]; if (!errors[2]) { const node = document.querySelector(`[data-step-error="${errors[0]}"]`); node.textContent = errors[1]; node.focus?.(); return false; } return true; }
  function textFromList(values) { return Array.isArray(values) ? values.join('\n') : ''; }
  function populateAdvanced(preferences) { const p = preferences || mapWizardToPreferences(wizard, defaults); const entries = Object.entries(p.role_positives || {}); document.querySelectorAll('[data-role-family-index]').forEach((group, index) => { const [family, keywords] = entries[index] || ['', []]; group.querySelector('[data-pref-field="role-family-name"]').value = family; group.querySelector('[data-pref-field="role-family-keywords"]').value = textFromList(keywords); }); ['role_negatives', 'remote_positives', 'location_positives', 'location_negatives', 'sponsorship_supported', 'sponsorship_unsupported', 'sponsorship_ambiguous'].forEach((name) => { field(name).value = textFromList(p[name]); }); }
  function collectAdvanced() { const role_positives = {}; document.querySelectorAll('[data-role-family-index]').forEach((group) => { const family = group.querySelector('[data-pref-field="role-family-name"]').value.trim(); const keywords = normalizeKeywordLines(group.querySelector('[data-pref-field="role-family-keywords"]').value); if (family) role_positives[family] = keywords; }); return { schema_version: 1, role_positives, role_negatives: normalizeKeywordLines(field('role_negatives').value), remote_positives: normalizeKeywordLines(field('remote_positives').value), location_positives: normalizeKeywordLines(field('location_positives').value), location_negatives: normalizeKeywordLines(field('location_negatives').value), sponsorship_supported: normalizeKeywordLines(field('sponsorship_supported').value), sponsorship_unsupported: normalizeKeywordLines(field('sponsorship_unsupported').value), sponsorship_ambiguous: normalizeKeywordLines(field('sponsorship_ambiguous').value) }; }
  function currentDraftPreferences() { collectWizardFromInputs(); const generated = mapWizardToPreferences(wizard, activePreferences || defaults); return !isSetup() && elements.advanced.open ? collectAdvanced() : generated; }
  function updateDirty() { const dirty = JSON.stringify(normalizeWizard(wizard)) !== baselineWizard || !preferencesEqual(currentDraftPreferences(), baselinePreferences); if (dirty) setStatus('unsaved'); else setStatus(activePreferences ? 'active' : 'setup'); elements.unsaved.classList.toggle('hidden', !dirty); }
  function setLocationControlsDisabled(disabled) { form.querySelectorAll('#location-search, #location-clear, input[name="selected_countries"], [data-region-checkbox]').forEach((control) => { control.disabled = disabled || (control.id === 'location-clear' && !wizard.selected_countries.length); }); }
  async function save() { clearAlert(); if (!JobPreferencesStore.isStorageAvailable()) { elements.storage.classList.remove('hidden'); elements.storage.focus(); return; } if (!validWizard(wizard)) { for (let i = 0; i < 4; i += 1) if (!validateStep(i)) { setStep(i); setAlert('error', 'Fix the highlighted fields before saving.', true); return; } } const preferences = currentDraftPreferences(); elements.save.disabled = true; elements.save.textContent = 'Saving and reclassifying…'; form.setAttribute('aria-busy', 'true'); setLocationControlsDisabled(true); try { const response = await fetch('/job-preferences/validate-and-reclassify', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ ...preferences, next: nextUrl || undefined }) }); const payload = await response.json().catch(() => ({})); if (!response.ok) { setAlert('error', response.status === 500 ? 'Preferences were not saved because existing jobs could not be reclassified. Your last saved preferences are still active.' : 'Fix the highlighted fields before saving.', true); return; } const normalized = payload.preferences; const newEnvelope = createPreferenceEnvelope(wizard, normalized, elements.advanced.open); JobPreferencesStore.writeEnvelope(newEnvelope); envelope = newEnvelope; activePreferences = normalized; baselineWizard = JSON.stringify(normalizeWizard(wizard)); baselinePreferences = editablePreferenceSnapshot(normalized); populateAdvanced(normalized); renderMode(); const count = payload.reclassification && payload.reclassification.jobs_reclassified; setAlert('success', Number.isInteger(count) ? `Job Preferences saved. ${count} active job(s) reclassified.` : 'Job Preferences saved. Existing active jobs were reclassified.', true); const continuation = safeNextPath(payload.next || nextUrl); if (continuation) { elements.cont.href = continuation; elements.cont.textContent = continuation.startsWith('/dashboard') ? 'Continue to Dashboard' : 'Continue to Jobs'; elements.cont.classList.remove('hidden'); } } catch (_e) { setAlert('error', 'Preferences were not saved because existing jobs could not be reclassified. Your last saved preferences are still active.', true); } finally { elements.save.disabled = false; elements.save.textContent = 'Save preferences'; form.setAttribute('aria-busy', 'false'); setLocationControlsDisabled(false); updateDirty(); } }
  function renderMode() { const setup = isSetup(); elements.title.textContent = setup ? 'Set up Job Preferences' : 'Job Preferences'; elements.desc.textContent = setup ? 'Answer a few questions so the app can filter and rank jobs for your search.' : 'Configure the criteria used to filter, score, and rank jobs.'; elements.progress.classList.toggle('hidden', !setup); elements.advanced.classList.toggle('hidden', setup); elements.reset.classList.toggle('hidden', setup); document.querySelectorAll('[data-wizard-step]').forEach((panel) => panel.classList.toggle('hidden', setup ? Number(panel.dataset.wizardStep) !== currentStep : false)); setStep(setup ? currentStep : 0); setStatus(activePreferences ? 'active' : 'setup'); if (activePreferences && activePreferences.configured_at) elements.lastSaved.textContent = `Last saved ${new Date(activePreferences.configured_at).toLocaleString()}`; }
  renderOptions(); populateAdvanced(activePreferences || mapWizardToPreferences(wizard, defaults)); renderMode(); if (!JobPreferencesStore.isStorageAvailable()) { elements.storage.classList.remove('hidden'); elements.save.disabled = true; }
  document.getElementById('category-search').addEventListener('input', () => { renderOptions(); }); document.getElementById('location-search')?.addEventListener('input', () => { renderCountryGroups(); syncInputs(); }); document.getElementById('location-clear')?.addEventListener('click', () => { wizard.selected_countries = []; renderCountryGroups(); syncInputs(); updateDirty(); }); form.addEventListener('click', (event) => { if (event.target instanceof HTMLInputElement && event.target.matches('[data-region-checkbox]')) event.stopPropagation(); }); form.addEventListener('change', (event) => { if (event.target instanceof HTMLInputElement && event.target.matches('[data-region-checkbox]')) { const region = COUNTRIES_BY_REGION.find((item) => item.id === event.target.value); if (region) { const ids = region.countries.map((country) => country.id); wizard.selected_countries = event.target.checked ? dedupe([...wizard.selected_countries, ...ids]) : wizard.selected_countries.filter((id) => !ids.includes(id)); } syncInputs(); updateDirty(); return; } if (event.target.name === 'work_arrangements') { let work = selected('work_arrangements'); if (event.target.value === 'any' && event.target.checked) work = ['any']; else work = work.filter((v) => v !== 'any'); wizard.work_arrangements = work; } collectWizardFromInputs(); syncInputs(); updateDirty(); }); form.addEventListener('input', (event) => { if (event.target.id === 'location-search') return; collectWizardFromInputs(); updateDirty(); }); elements.next.addEventListener('click', () => { if (validateStep(currentStep)) setStep(Math.min(3, currentStep + 1)); }); elements.back.addEventListener('click', () => setStep(Math.max(0, currentStep - 1))); elements.reset.addEventListener('click', () => { envelope = JobPreferencesStore.readEnvelope(); if (!envelope) return; unmatchedSavedCountryIds = envelope && envelope.wizard && Array.isArray(envelope.wizard.selected_countries) ? dedupe(envelope.wizard.selected_countries).filter((id) => !COUNTRY_IDS.has(id)) : []; wizard = normalizeWizard(envelope.wizard); activePreferences = envelope.preferences; baselineWizard = JSON.stringify(wizard); baselinePreferences = editablePreferenceSnapshot(activePreferences); renderOptions(); populateAdvanced(activePreferences); updateDirty(); }); form.addEventListener('submit', (event) => { event.preventDefault(); save(); }); updateDirty();
}

document.addEventListener('submit', (event) => { const form = event.target; if (!(form instanceof HTMLFormElement) || form.dataset.requiresJobPreferencesSubmit !== 'true') return; const preferences = JobPreferencesStore.read(); if (!preferences) { event.preventDefault(); JobPreferencesStore.redirectToSetup(); return; } let input = form.querySelector('input[name="job_preferences_json"]'); if (!input) { input = document.createElement('input'); input.type = 'hidden'; input.name = 'job_preferences_json'; form.appendChild(input); } input.value = JSON.stringify(preferences); });

function initSourceBatchRuns() {
  const root = document.querySelector('[data-source-batch-root]'); if (!root) return;
  const runAllButton = root.querySelector('[data-batch-run-all]');
  const runSelectedButton = root.querySelector('[data-batch-run-selected]');
  const selectionStatus = root.querySelector('[data-batch-selection-status]');
  const region = root.querySelector('[data-batch-region]');
  const selectAll = root.querySelector('[data-source-select-all]');
  const rows = Array.from(root.querySelectorAll('[data-source-row]'));
  const checkboxes = Array.from(root.querySelectorAll('[data-source-row-checkbox]'));
  const dialog = root.querySelector('[data-batch-dialog]');
  const dialogBackdrop = root.querySelector('[data-batch-dialog-backdrop]');
  const dialogTitle = root.querySelector('#source-batch-dialog-title');
  const dialogDescription = root.querySelector('[data-batch-dialog-description]');
  const dialogError = root.querySelector('[data-batch-dialog-error]');
  const dialogCancel = root.querySelector('[data-batch-dialog-cancel]');
  const dialogConfirm = root.querySelector('[data-batch-dialog-confirm]');
  const focusableSelector = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
  let selectedIds = new Set();
  let active = false;
  let previewLoading = false;
  let pendingPreview = null;
  let initiatingButton = null;
  let pollTimer = null;
  let lastStatus = null;

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const terminal = (status) => ['completed', 'completed_with_failures', 'failed'].includes(status);
  const modeLabel = (mode) => (mode === 'all' ? 'Run All' : 'Run Selected');
  const resultLabel = (status) => ({ success: 'Succeeded', failed: 'Failed after retries', skipped: 'Skipped', running: 'Running', pending: 'Queued', queued: 'Queued' }[status] || String(status || 'Unknown').replace(/_/g, ' '));
  const resultTone = (status) => (status === 'success' ? 'success' : status === 'failed' ? 'danger' : status === 'running' ? 'info' : status === 'skipped' ? 'warning' : 'neutral');

  function getSelectedRows() { return rows.filter((row) => selectedIds.has(Number(row.dataset.sourceId))); }
  function hasHealthySelection() { return getSelectedRows().some((row) => (row.dataset.healthState || '').toLowerCase() === 'healthy'); }
  function setButtonLoading(button, loading) { if (!button) return; button.textContent = loading ? 'Preparing…' : (button === runAllButton ? 'Run All' : 'Run Selected'); button.setAttribute('aria-busy', loading ? 'true' : 'false'); }
  function syncToolbar() {
    const count = selectedIds.size;
    if (selectionStatus) selectionStatus.textContent = `${count} selected`;
    if (runAllButton) runAllButton.disabled = active || previewLoading;
    if (runSelectedButton) {
      const enabled = !active && !previewLoading && hasHealthySelection();
      runSelectedButton.disabled = !enabled;
      runSelectedButton.title = enabled ? 'Run selected Healthy sources.' : 'Select at least one Healthy source to run selected sources.';
    }
    if (selectAll) {
      const visibleIds = rows.map((row) => Number(row.dataset.sourceId));
      const selectedVisible = visibleIds.filter((id) => selectedIds.has(id)).length;
      selectAll.checked = Boolean(visibleIds.length && selectedVisible === visibleIds.length);
      selectAll.indeterminate = selectedVisible > 0 && selectedVisible < visibleIds.length;
      selectAll.disabled = visibleIds.length === 0;
    }
    rows.forEach((row) => row.classList.toggle('is-selected', selectedIds.has(Number(row.dataset.sourceId))));
  }
  function setRegion(html, options = {}) { if (!region) return; region.innerHTML = html; region.classList.toggle('hidden', !html); region.setAttribute('role', options.alert ? 'alert' : 'status'); if (options.testid) region.dataset.testid = options.testid; }
  function showError(message) { setRegion(`<div class="alert alert--danger" role="alert"><strong>${escapeHtml(message)}</strong></div>`, { alert: true }); }
  function closeDialog() {
    if (!dialog || !dialogBackdrop) return;
    dialog.classList.add('hidden'); dialogBackdrop.classList.add('hidden');
    dialogError?.classList.add('hidden');
    pendingPreview = null;
    if (initiatingButton instanceof HTMLElement) initiatingButton.focus();
    initiatingButton = null;
    syncToolbar();
  }
  function trapDialogFocus(event) {
    if (!dialog || dialog.classList.contains('hidden') || event.key !== 'Tab') return;
    const focusable = Array.from(dialog.querySelectorAll(focusableSelector));
    if (!focusable.length) return;
    const first = focusable[0]; const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  function openDialog(preview, mode, selectedCount) {
    pendingPreview = preview;
    const isAll = mode === 'all';
    if (dialogTitle) dialogTitle.textContent = isAll ? 'Run all healthy sources?' : 'Run selected healthy sources?';
    const skippedItems = (preview.skipped_sources || []).map((item) => `<li><strong>${escapeHtml(item.source_name || `Source ${item.source_id}`)}</strong>: ${escapeHtml(item.reason || item.health_state || 'Skipped')}</li>`).join('');
    const zero = Number(preview.eligible_count || 0) === 0;
    if (dialogDescription) dialogDescription.innerHTML = `
      <p>${isAll ? 'This will run all Healthy sources in the system. Current filters, search, sorting, and pagination will not limit this run.' : 'Only selected sources that are Healthy will run. Selected sources that are not eligible will be skipped.'}</p>
      ${isAll ? '' : `<p><strong>Selected:</strong> ${Number(selectedCount || 0)}</p>`}
      <p><strong>Eligible to run:</strong> ${Number(preview.eligible_count || 0)}</p>
      <p><strong>Skipped:</strong> ${Number(preview.skipped_count || 0)}</p>
      ${zero ? '<p><strong>No sources are eligible to run.</strong></p>' : ''}
      ${(preview.skipped_sources || []).length ? `<details><summary>View skipped sources</summary><ul>${skippedItems}</ul></details>` : ''}`;
    if (dialogConfirm) dialogConfirm.classList.toggle('hidden', zero);
    if (dialogCancel) dialogCancel.textContent = zero ? 'Close' : 'Cancel';
    dialogError?.classList.add('hidden');
    dialog?.classList.remove('hidden'); dialogBackdrop?.classList.remove('hidden');
    setTimeout(() => (dialogTitle instanceof HTMLElement ? dialogTitle.focus() : dialog?.querySelector(focusableSelector)?.focus()), 0);
  }
  async function requestJson(url, options = {}) {
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...(options.headers || {}) }, ...options });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(payload.detail || payload.message || `Request failed with status ${response.status}`);
      error.status = response.status; throw error;
    }
    return payload;
  }
  async function preview(mode) {
    const preferences = JobPreferencesStore.read(); if (!preferences) { JobPreferencesStore.redirectToSetup(); return; }
    initiatingButton = mode === 'all' ? runAllButton : runSelectedButton;
    previewLoading = true; setButtonLoading(initiatingButton, true); syncToolbar();
    try {
      const sourceIds = mode === 'selected' ? Array.from(selectedIds) : null;
      const payload = await requestJson('/sources/batch-runs/preview', { method: 'POST', body: JSON.stringify({ mode, source_ids: sourceIds }) });
      openDialog(payload, mode, sourceIds ? sourceIds.length : 0);
    } catch (_error) { showError('Could not prepare batch run. Try again.'); }
    finally { previewLoading = false; setButtonLoading(initiatingButton, false); syncToolbar(); }
  }
  function renderProgress(status, statusError = '') {
    lastStatus = status;
    const eligible = Number(status.eligible_count || 0); const completed = Number(status.completed_count || 0);
    const progress = eligible > 0 ? `<progress class="source-batch-progress" max="${eligible}" value="${Math.min(completed, eligible)}">${completed} of ${eligible}</progress>` : '';
    const rowsHtml = (status.source_results || []).map((item) => `<tr><td>${escapeHtml(item.source_name || `Source ${item.source_id}`)}</td><td><span class="badge badge--${resultTone(item.status)}">${escapeHtml(resultLabel(item.status))}</span></td><td>${Number(item.attempts_used || 0)} of 3</td><td>${escapeHtml(item.last_error || '')}</td></tr>`).join('');
    const skippedHtml = (status.skipped_sources || []).map((item) => `<tr><td>${escapeHtml(item.source_name || `Source ${item.source_id}`)}</td><td><span class="badge badge--warning">Skipped</span></td><td>—</td><td>${escapeHtml(item.reason || item.health_state || '')}</td></tr>`).join('');
    setRegion(`<section class="source-batch-panel" data-testid="batch-progress-panel" aria-labelledby="source-batch-progress-title">
      <h3 id="source-batch-progress-title" tabindex="-1">${status.status === 'starting' ? 'Starting batch run…' : 'Batch run in progress'}</h3>
      <p>${escapeHtml(modeLabel(status.mode))}: ${completed} of ${eligible} completed, ${Number(status.running_count || 0)} running, ${Number(status.pending_count || 0)} queued, ${Number(status.success_count || 0)} succeeded, ${Number(status.failure_count || 0)} failed, ${Number(status.skipped_count || 0)} skipped.</p>
      ${progress}<p class="helper-text">Up to 5 sources run at the same time. Failed sources may retry up to 3 attempts.</p>
      ${statusError ? `<div class="alert alert--warning" role="status">${escapeHtml(statusError)}</div>` : ''}
      ${(rowsHtml || skippedHtml) ? `<div class="table-wrap source-batch-details"><table><thead><tr><th>Source</th><th>Result</th><th>Attempts used</th><th>Reason or error</th></tr></thead><tbody>${rowsHtml}${skippedHtml}</tbody></table></div>` : ''}
    </section>`);
  }
  function renderSummary(status) {
    active = false; syncToolbar();
    const title = status.status === 'failed' ? 'Batch run failed' : Number(status.failure_count || 0) > 0 || status.status === 'completed_with_failures' ? 'Batch run completed with failures' : 'Batch run completed';
    const rowsHtml = (status.source_results || []).map((item) => `<tr><td>${escapeHtml(item.source_name || `Source ${item.source_id}`)}</td><td><span class="badge badge--${resultTone(item.status)}">${escapeHtml(resultLabel(item.status))}</span></td><td>${Number(item.attempts_used || 0)} of 3</td><td>${escapeHtml(item.last_error || '')}</td></tr>`).join('');
    const skippedHtml = (status.skipped_sources || []).map((item) => `<tr><td>${escapeHtml(item.source_name || `Source ${item.source_id}`)}</td><td><span class="badge badge--warning">Skipped</span></td><td>—</td><td>${escapeHtml(item.reason || item.health_state || '')}</td></tr>`).join('');
    setRegion(`<section class="source-batch-panel source-batch-summary" data-testid="batch-completion-summary" aria-labelledby="source-batch-summary-title">
      <div class="section-heading"><h3 id="source-batch-summary-title" tabindex="-1">${escapeHtml(title)}</h3><button class="btn btn--ghost btn--sm" type="button" data-batch-dismiss-summary>Dismiss summary</button></div>
      ${status.error_message ? `<div class="alert alert--danger" role="alert">${escapeHtml(status.error_message)}</div>` : ''}
      <div class="source-batch-counts" aria-label="Batch run summary counts"><span>Succeeded: <strong>${Number(status.success_count || 0)}</strong></span><span>Failed: <strong>${Number(status.failure_count || 0)}</strong></span><span>Skipped: <strong>${Number(status.skipped_count || 0)}</strong></span><span>Eligible: <strong>${Number(status.eligible_count || 0)}</strong></span></div>
      <div class="table-wrap source-batch-details"><table><thead><tr><th>Source</th><th>Result</th><th>Attempts used</th><th>Reason or error</th></tr></thead><tbody>${rowsHtml}${skippedHtml || '<tr><td colspan="4">No skipped sources.</td></tr>'}</tbody></table></div>
    </section>`);
  }
  function poll(url) {
    clearTimeout(pollTimer);
    pollTimer = setTimeout(async () => {
      try {
        const status = await requestJson(url);
        if (terminal(status.status)) { renderSummary(status); return; }
        renderProgress(status); poll(url);
      } catch (error) {
        if (error.status === 404) { active = false; syncToolbar(); showError('Batch status is no longer available. Completed source attempts may still appear in source run history.'); return; }
        if (lastStatus) renderProgress(lastStatus, 'Unable to refresh batch status. Retrying…');
        poll(url);
      }
    }, 1000);
  }
  async function startBatch() {
    if (!pendingPreview || !dialogConfirm) return;
    const preferences = JobPreferencesStore.read(); if (!preferences) { JobPreferencesStore.redirectToSetup(); return; }
    dialogConfirm.disabled = true; dialogConfirm.textContent = 'Starting…';
    try {
      const skippedSources = pendingPreview.skipped_sources || [];
      const started = await requestJson('/sources/batch-runs', { method: 'POST', body: JSON.stringify({ preview_id: pendingPreview.preview_id, job_preferences: preferences }) });
      active = ['starting', 'running'].includes(started.status); closeDialog(); syncToolbar();
      const initial = { ...started, success_count: 0, failure_count: 0, pending_count: started.eligible_count || 0, running_count: 0, completed_count: 0, source_results: [], skipped_sources: skippedSources };
      if (terminal(started.status)) { renderSummary(initial); return; }
      renderProgress(initial); document.getElementById('source-batch-progress-title')?.focus(); poll(started.poll_url || `/sources/batch-runs/${started.batch_id}`);
    } catch (error) {
      const message = error.status === 409 ? 'Another batch run is already active. Wait for it to finish before starting another.' : error.status === 410 ? 'This confirmation expired. Prepare the batch run again.' : 'Could not start batch run. Try again.';
      if (dialogError) { dialogError.textContent = message; dialogError.classList.remove('hidden'); }
    } finally { dialogConfirm.disabled = false; dialogConfirm.textContent = 'Run eligible sources'; syncToolbar(); }
  }

  checkboxes.forEach((checkbox) => checkbox.addEventListener('change', () => { const row = checkbox.closest('[data-source-row]'); const id = Number(row?.dataset.sourceId); if (!id) return; if (checkbox.checked) selectedIds.add(id); else selectedIds.delete(id); syncToolbar(); }));
  selectAll?.addEventListener('change', () => { rows.forEach((row) => { const id = Number(row.dataset.sourceId); const checkbox = row.querySelector('[data-source-row-checkbox]'); if (selectAll.checked) selectedIds.add(id); else selectedIds.delete(id); if (checkbox) checkbox.checked = selectAll.checked; }); syncToolbar(); });
  runAllButton?.addEventListener('click', () => preview('all'));
  runSelectedButton?.addEventListener('click', () => { if (!runSelectedButton.disabled) preview('selected'); });
  dialogCancel?.addEventListener('click', closeDialog);
  dialogBackdrop?.addEventListener('click', closeDialog);
  dialogConfirm?.addEventListener('click', startBatch);
  region?.addEventListener('click', (event) => { if (event.target instanceof HTMLElement && event.target.matches('[data-batch-dismiss-summary]')) setRegion(''); });
  document.addEventListener('keydown', (event) => { if (!dialog || dialog.classList.contains('hidden')) return; if (event.key === 'Escape') closeDialog(); else trapDialogFocus(event); });
  syncToolbar();
}

if (typeof window !== 'undefined') window.__JobPreferencesTestHelpers = { CATEGORY_OPTIONS, COUNTRY_OPTIONS, normalizeWizard, mapWizardToPreferences, createPreferenceEnvelope, extractPreferences, editablePreferenceSnapshot, preferencesEqual, normalizeKeywordLines, safeNextPath, JobPreferencesStore };
