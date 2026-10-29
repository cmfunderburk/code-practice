import 'fake-indexeddb/auto';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'bun:test';
import { Window } from 'happy-dom';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { bundle, findProgram, stepCount } from '../bundle';
import { markLaunch, parseRoute } from '../route';
import { listPasses } from '../store/db';
import { DEFAULT_SETTINGS, SettingsContext, type Settings } from '../settings';
import { DrillView } from './DrillView';

// Drive the real view from the keyboard in happy-dom. Touch zones need layout,
// which happy-dom doesn't do, so gestures are checked on the iPad.
const window = new Window({ url: 'http://localhost/' });
const globals = { window, document: window.document, location: window.location, history: window.history,
  HashChangeEvent: window.HashChangeEvent, KeyboardEvent: window.KeyboardEvent, HTMLElement: window.HTMLElement,
  Element: window.Element, IS_REACT_ACT_ENVIRONMENT: true };
const saved: Record<string, unknown> = {};

beforeAll(() => {
  for (const [key, value] of Object.entries(globals)) {
    saved[key] = (globalThis as Record<string, unknown>)[key];
    (globalThis as Record<string, unknown>)[key] = value;
  }
  window.HTMLElement.prototype.scrollIntoView = () => {};
});
afterAll(() => {
  Object.assign(globalThis, saved);
  void window.happyDOM.close();
});

const settle = () => act(async () => {
  await new Promise((resolve) => setTimeout(resolve, 20));
});

/** Every pass and the session start empty: clear the stores between tests. */
beforeEach(async () => {
  await listPasses(); // the app opens (and creates) the database first
  const db = await new Promise<IDBDatabase>((resolve) => {
    const request = indexedDB.open('code-practice', 2);
    request.onsuccess = () => resolve(request.result);
  });
  const tx = db.transaction(['passes', 'settings'], 'readwrite');
  tx.objectStore('passes').clear();
  tx.objectStore('settings').clear();
  await new Promise((resolve) => { tx.oncomplete = resolve; });
});

async function mount(programId: string, scope: 'all' | 'one' | 'flagged', unitId: string,
  { launch = false, ...settings }: Partial<Settings> & { launch?: boolean } = {}) {
  const program = findProgram(programId)!;
  const impl = program.impls[0]!;
  const container = document.createElement('div');
  document.body.appendChild(container);
  let root!: Root;
  // The view navigates by replacing the hash; re-render with the routed unit, as App does.
  const render = () => {
    const route = parseRoute(location.hash);
    const unit = route.screen === 'drill' ? route.unit : unitId;
    root.render(
      <SettingsContext.Provider value={[{ ...DEFAULT_SETTINGS, ...settings }, () => {}]}>
        <DrillView program={program} impl={impl} scope={scope} unitId={unit} />
      </SettingsContext.Provider>,
    );
  };
  history.replaceState(null, '', `#/p/${programId}/python/drill/${scope}/${encodeURIComponent(unitId)}`);
  if (launch) markLaunch();
  const onHash = () => act(render);
  window.addEventListener('hashchange', onHash);
  act(() => {
    root = createRoot(container as unknown as HTMLElement);
    render();
  });
  await settle();
  const press = (key: string) => act(() => {
    window.dispatchEvent(new window.KeyboardEvent('keydown', { key }));
  });
  const q = (selector: string) => container.querySelectorAll(selector);
  const unmount = () => {
    window.removeEventListener('hashchange', onHash);
    act(() => root.unmount());
  };
  return { press, q, container, impl, unmount };
}

describe('DrillView', () => {
  it('starts with every line hidden and reveals one step per key', async () => {
    const { press, q, impl, unmount } = await mount('Hangman', 'one', 'wrong_count');
    const unit = impl.units.find((u) => u.id === 'wrong_count')!;
    expect(q('.drill-line.hidden').length).toBe(unit.lines.length);
    expect(q('.drill-cue')[0]?.textContent).toBe(unit.cue);
    press(' ');
    expect(q('.drill-line:not(.hidden)').length).toBe(unit.lines.filter((l) => l.step === 0).length);
    press('Backspace');
    expect(q('.drill-line:not(.hidden)').length).toBe(0);
    unmount();
  });

  it('flags the last revealed step, finishes with a score, and resets', async () => {
    const { press, q, container, impl, unmount } = await mount('Hangman', 'one', 'masked');
    const unit = impl.units.find((u) => u.id === 'masked')!;
    press(' ');
    press(' ');
    press('m');
    expect(q('.drill-line.flagged').length).toBeGreaterThan(0);
    for (let i = 0; i < stepCount(unit); i += 1) press(' ');
    expect(container.querySelector('.drill-footer .result')?.textContent).toBe(`missed 1/${stepCount(unit)}`);
    press('r');
    expect(q('.drill-line.hidden').length).toBe(unit.lines.length);
    expect(q('.drill-footer').length).toBe(0);
    unmount();
  });

  it('gives the signature when the toggle is on', async () => {
    const { press, q, unmount } = await mount('Hangman', 'one', 'masked', { showSignature: true });
    expect(q('.drill-line.given:not(.hidden)').length).toBe(1);
    press('Backspace'); // can't hide a given step
    expect(q('.drill-line.given:not(.hidden)').length).toBe(1);
    press('s');
    expect(q('.drill-line.given').length).toBe(0);
    unmount();
  });

  it('pages through a whole-program run to its summary, with earlier units as context', async () => {
    const { press, q, container, impl, unmount } = await mount('Hangman', 'all', 'imports');
    impl.units.forEach((unit, i) => {
      expect(container.querySelector('.drill-name')?.textContent).toBe(unit.name);
      expect(q('.context-unit').length).toBe(i);
      for (let s = 0; s < stepCount(unit); s += 1) press(' ');
      if (i === 1) press('m'); // miss one step of the second unit
      press('Enter');
    });
    expect(container.querySelector('.run-summary h2')?.textContent).toBe(`Run finished: ${impl.units.length - 1}/${impl.units.length} clean`);
    const redo = [...container.querySelectorAll('.run-summary button')].find((b) => b.textContent === 'Redo flagged')!;
    act(() => (redo as unknown as HTMLElement).click());
    expect(container.querySelector('.drill-name')?.textContent).toBe(impl.units[1]!.name);
    expect(container.querySelector('.drill-position')?.textContent).toBe('1 / 1');
    unmount();
  });

  it('pages a single-unit drill through the outline, methods included', async () => {
    const { press, container, unmount } = await mount('Editor-Buffer', 'one', 'EditorBuffer');
    press('ArrowRight');
    expect(container.querySelector('.drill-name')?.textContent).toBe('EditorBuffer.__init__');
    unmount();
  });

  it('renders the first unit of every program', async () => {
    for (const program of bundle.programs) {
      const { q, unmount } = await mount(program.id, 'all', program.impls[0]!.units[0]!.id);
      expect(q('.drill-line').length).toBe(program.impls[0]!.units[0]!.lines.length);
      unmount();
    }
  });

  it('saves one pass per finish, updated by flag changes afterwards', async () => {
    const { press, impl, unmount } = await mount('Hangman', 'one', 'masked');
    const unit = impl.units.find((u) => u.id === 'masked')!;
    for (let i = 0; i < stepCount(unit); i += 1) press(' ');
    await settle();
    expect((await listPasses(impl.id)).map((p) => p.missed)).toEqual([[]]);
    press('m'); // flag the last step after finishing
    await settle();
    const [pass] = await listPasses(impl.id);
    expect(pass).toMatchObject({ unitId: 'masked', missed: [stepCount(unit) - 1], steps: stepCount(unit), sourceHash: unit.hash });
    press('r');
    for (let i = 0; i < stepCount(unit); i += 1) press(' ');
    await settle();
    expect((await listPasses(impl.id)).map((p) => p.missed)).toEqual([[stepCount(unit) - 1], []]);
    unmount();
  });

  it('runs the flagged units from the outline', async () => {
    const first = await mount('Hangman', 'one', 'wrong_count');
    const units = first.impl.units;
    for (const id of ['wrong_count', 'masked']) {
      const unit = units.find((u) => u.id === id)!;
      for (let i = 0; i < stepCount(unit); i += 1) first.press(' ');
      if (id === 'masked') first.press('m');
      first.press('ArrowRight');
    }
    await settle();
    first.unmount();

    const run = await mount('Hangman', 'flagged', 'masked');
    expect(run.container.querySelector('.drill-name')?.textContent).toBe('masked');
    expect(run.container.querySelector('.drill-position')?.textContent).toBe('1 / 1');
    run.unmount();
  });

  it('resumes the drill it relaunched into, but not one opened again', async () => {
    const first = await mount('Hangman', 'all', 'imports');
    first.press(' ');
    first.press(' ');
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 350)); }); // the session save is debounced
    first.unmount();

    const reopened = await mount('Hangman', 'all', 'imports');
    expect(reopened.q('.drill-line:not(.hidden)').length).toBe(0);
    reopened.unmount();

    const relaunched = await mount('Hangman', 'all', 'imports', { launch: true });
    expect(relaunched.q('.drill-line:not(.hidden)').length).toBeGreaterThan(0);
    relaunched.unmount();
  });
});
