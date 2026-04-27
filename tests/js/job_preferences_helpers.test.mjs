import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const STATIC_FILES = ['app/static/js/app.js', 'app/web/static/app.js'];

function defaultPreferences(overrides = {}) {
  return {
    schema_version: 1,
    configured_at: '2026-04-26T12:00:00.000Z',
    role_positives: {
      'python backend': ['python backend', 'backend engineer'],
      sdet: ['sdet'],
    },
    role_negatives: ['sales'],
    remote_positives: ['remote'],
    location_positives: ['spain'],
    location_negatives: ['us only'],
    sponsorship_supported: ['will sponsor'],
    sponsorship_unsupported: ['unable to sponsor'],
    sponsorship_ambiguous: ['visa'],
    ...overrides,
  };
}

function loadHelpers(filePath) {
  const listeners = {};
  const storage = new Map();
  class FakeForm {
    constructor() {
      this.dataset = { requiresJobPreferencesSubmit: 'true' };
      this.appended = [];
    }

    querySelector(selector) {
      return this.appended.find((node) => selector === 'input[name="job_preferences_json"]' && node.name === 'job_preferences_json') || null;
    }

    appendChild(node) {
      this.appended.push(node);
    }
  }
  const document = {
    body: { dataset: {}, classList: { add() {}, remove() {} } },
    addEventListener(type, callback) {
      listeners[type] = listeners[type] || [];
      listeners[type].push(callback);
    },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    getElementById() { return null; },
    createElement(tagName) { return { tagName, type: '', name: '', value: '' }; },
  };
  const window = {
    document,
    localStorage: {
      setItem(key, value) { storage.set(key, String(value)); },
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      removeItem(key) { storage.delete(key); },
    },
    location: {
      origin: 'https://example.test',
      pathname: '/sources/1',
      search: '',
      assign(value) { this.assigned = value; },
    },
    matchMedia() { return { matches: false }; },
  };
  const context = vm.createContext({
    console,
    document,
    window,
    URL,
    Set,
    Map,
    JSON,
    Date,
    Number,
    Object,
    String,
    Array,
    HTMLElement: class HTMLElement {},
    HTMLFormElement: FakeForm,
  });
  vm.runInContext(readFileSync(filePath, 'utf8'), context, { filename: filePath });
  return { helpers: context.window.__JobPreferencesTestHelpers, listeners, FakeForm };
}

for (const filePath of STATIC_FILES) {
  test(`${filePath}: editable comparison ignores configured_at metadata`, () => {
    const { helpers } = loadHelpers(filePath);
    const saved = defaultPreferences({ configured_at: '2026-04-26T12:00:00.000Z' });
    const draftShape = { ...saved };
    delete draftShape.configured_at;

    assert.equal(helpers.preferencesEqual(draftShape, saved), true);
    assert.deepEqual(Object.keys(helpers.editablePreferenceSnapshot(saved)), [
      'schema_version',
      'role_positives',
      'role_negatives',
      'remote_positives',
      'location_positives',
      'location_negatives',
      'sponsorship_supported',
      'sponsorship_unsupported',
      'sponsorship_ambiguous',
    ]);
  });

  test(`${filePath}: editable comparison detects real draft changes`, () => {
    const { helpers } = loadHelpers(filePath);
    const saved = defaultPreferences();
    const changed = defaultPreferences({ remote_positives: ['hybrid'] });

    assert.equal(helpers.preferencesEqual(saved, changed), false);
  });

  test(`${filePath}: localStorage store rejects unusable positive-signal-free preferences`, () => {
    const { helpers } = loadHelpers(filePath);
    const invalid = defaultPreferences({ role_positives: { empty: [] }, remote_positives: [], location_positives: [] });

    helpers.JobPreferencesStore.write(invalid);

    assert.equal(helpers.JobPreferencesStore.read(), null);
  });

  test(`${filePath}: wizard maps predefined categories countries work and visa yes`, () => {
    const { helpers } = loadHelpers(filePath);
    const preferences = helpers.mapWizardToPreferences({
      schema_version: 1,
      selected_categories: ['python_backend', 'sdet', 'not_custom'],
      selected_countries: ['spain', 'united_kingdom'],
      work_arrangements: ['remote', 'hybrid'],
      requires_visa_sponsorship: true,
    });

    assert.deepEqual(Array.from(Object.keys(preferences.role_positives)), ['python backend', 'sdet']);
    assert.equal(JSON.stringify(preferences.location_positives), JSON.stringify(['spain', 'united kingdom', 'uk', 'britain', 'great britain']));
    assert.equal(JSON.stringify(preferences.remote_positives), JSON.stringify(['remote', 'work from anywhere', 'distributed', 'hybrid']));
    assert.equal(preferences.sponsorship_unsupported.includes('no visa sponsorship'), true);
  });

  test(`${filePath}: flexible any is exclusive and visa no is neutral`, () => {
    const { helpers } = loadHelpers(filePath);
    const wizard = helpers.normalizeWizard({
      selected_categories: ['backend_engineer'],
      selected_countries: ['germany'],
      work_arrangements: ['remote', 'any', 'onsite'],
      requires_visa_sponsorship: false,
    });
    const preferences = helpers.mapWizardToPreferences(wizard);

    assert.equal(JSON.stringify(wizard.work_arrangements), JSON.stringify(['any']));
    assert.equal(JSON.stringify(preferences.remote_positives), JSON.stringify([]));
    assert.equal(JSON.stringify(preferences.sponsorship_supported), JSON.stringify([]));
    assert.equal(JSON.stringify(preferences.sponsorship_unsupported), JSON.stringify([]));
    assert.equal(JSON.stringify(preferences.sponsorship_ambiguous), JSON.stringify([]));
  });

  test(`${filePath}: envelope stores wizard metadata while extraction returns backend DTO`, () => {
    const { helpers } = loadHelpers(filePath);
    const wizard = { selected_categories: ['sdet'], selected_countries: ['japan'], work_arrangements: ['onsite'], requires_visa_sponsorship: false };
    const preferences = helpers.mapWizardToPreferences(wizard);
    const envelope = helpers.createPreferenceEnvelope(wizard, preferences);

    assert.equal(envelope.wizard.selected_categories[0], 'sdet');
    assert.deepEqual(helpers.extractPreferences(envelope), preferences);
  });

  test(`${filePath}: source-run submit injects saved preferences at submit time`, () => {
    const { helpers, listeners, FakeForm } = loadHelpers(filePath);
    const saved = defaultPreferences();
    helpers.JobPreferencesStore.write(helpers.createPreferenceEnvelope({ selected_categories: ['sdet'], selected_countries: ['spain'], work_arrangements: ['remote'], requires_visa_sponsorship: true }, saved));
    const form = new FakeForm();
    const event = { target: form, preventDefault() { this.prevented = true; } };

    for (const listener of listeners.submit || []) {
      listener(event);
    }

    assert.equal(event.prevented, undefined);
    assert.equal(form.appended.length, 1);
    assert.equal(form.appended[0].name, 'job_preferences_json');
    assert.deepEqual(JSON.parse(form.appended[0].value), saved);
  });
}
