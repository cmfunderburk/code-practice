import { describe, expect, it } from 'bun:test';
import { renderToString } from 'react-dom/server';
import { bundle } from '../bundle';
import { READ_TABS } from '../route';
import { DEFAULT_SETTINGS, SettingsContext } from '../settings';
import { Library } from './Library';
import { ProgramView } from './ProgramView';
import { ReadView } from './ReadView';

// Rendering every screen for every program catches runtime errors in the
// views; layout itself is checked on the iPad.
describe('screens render', () => {
  it('library', () => {
    const html = renderToString(
      <SettingsContext.Provider value={[DEFAULT_SETTINGS, () => {}]}><Library /></SettingsContext.Provider>,
    );
    for (const program of bundle.programs) expect(html).toContain(program.title);
  });

  it('every program and read tab', () => {
    for (const program of bundle.programs) {
      for (const impl of program.impls) {
        const view = renderToString(
          <SettingsContext.Provider value={[DEFAULT_SETTINGS, () => {}]}><ProgramView program={program} impl={impl} /></SettingsContext.Provider>,
        );
        expect(view).toContain(impl.units[0]!.name);
        for (const tab of READ_TABS) {
          const lastUnit = impl.units[impl.units.length - 1]!;
          expect(renderToString(<ReadView program={program} impl={impl} tab={tab} unit={lastUnit.id} />)).toContain('read-body');
        }
      }
    }
  });

  it('folds answer callouts in the defense doc', () => {
    const program = bundle.programs.find((p) => p.id === 'Hangman')!;
    const html = renderToString(<ReadView program={program} impl={program.impls[0]!} tab="defense" />);
    expect(html).toContain('<details class="md-callout md-callout-answer">');
    expect(html).not.toContain('[!answer]');
  });
});
