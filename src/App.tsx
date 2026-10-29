import { useState } from 'react';
import { findProgram } from './bundle';
import { DrillView } from './drill/DrillView';
import { useRoute } from './route';
import { Library } from './screens/Library';
import { ProgramView } from './screens/ProgramView';
import { ReadView } from './screens/ReadView';
import { SettingsProvider } from './settings';
import { useUpdateReady } from './sw/register';

function UpdateBanner() {
  const ready = useUpdateReady();
  const [dismissed, setDismissed] = useState(false);
  if (!ready || dismissed) return null;
  return (
    <div className="update-banner" role="status">
      <span>A new version is ready</span>
      <button className="button primary" onClick={() => location.reload()}>
        Reload
      </button>
      <button className="button subtle" onClick={() => setDismissed(true)} aria-label="Not now">
        ×
      </button>
    </div>
  );
}

function Screen() {
  const route = useRoute();
  if (route.screen === 'library') return <Library />;
  // A program that left the bundle (renamed in the corpus) falls back to the library.
  const program = findProgram(route.program);
  const impl = program?.impls.find((i) => i.lang === route.lang);
  if (!program || !impl) return <Library />;
  if (route.screen === 'program') return <ProgramView program={program} impl={impl} />;
  if (route.screen === 'drill') {
    return <DrillView key={`${program.id}/${impl.lang}/${route.scope}`} program={program} impl={impl} scope={route.scope} unitId={route.unit} />;
  }
  return <ReadView key={`${program.id}/${impl.lang}`} program={program} impl={impl} tab={route.tab} unit={route.unit} />;
}

export function App() {
  return (
    <SettingsProvider>
      <Screen />
      <UpdateBanner />
    </SettingsProvider>
  );
}
