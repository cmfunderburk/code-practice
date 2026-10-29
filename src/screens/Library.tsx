import { useEffect, useRef, useState } from 'react';
import { exportState, restoreBackup, saveFile, BackupError } from '../backup';
import { bundle, findImpl, LANGS, type Lang, type Program } from '../bundle';
import { cleanCount, type Latest } from '../progress';
import { navigate } from '../route';
import { useSettings, type Settings } from '../settings';
import { Segmented, SettingsSheet } from '../Sheets';
import { formatBytes, storageStatus, type StorageStatus } from '../store/persistence';
import { useLatestPasses } from '../usePasses';

const TIERS: Array<[Program['tier'], string]> = [['easy', 'Easy'], ['medium', 'Medium'], ['hard', 'Hard']];

function progressLabel(program: Program, lang: Lang, latest: Latest | null): string {
  const impl = findImpl(program, lang);
  if (!impl) return '';
  const { clean, total } = cleanCount(impl, latest ?? new Map());
  return latest && clean > 0 ? `${clean}/${total} clean` : `${total} units`;
}

/** Export and restore the drill history, and how the device keeps it. */
function BackupSection({ onRestored }: { onRestored: () => void }) {
  const [settings, update] = useSettings();
  const [storage, setStorage] = useState<StorageStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void storageStatus().then(setStorage);
  }, []);

  const run = async (label: string, work: () => Promise<string | null>) => {
    setBusy(true);
    setMessage(null);
    try {
      setMessage(await work());
    } catch (err) {
      setMessage(`${label} failed: ${err instanceof BackupError ? err.message : String(err)}`);
    } finally {
      setBusy(false);
    }
  };

  const onExport = () => run('Export', async () => ((await saveFile(await exportState(settings))) ? 'Exported.' : null));

  const onRestore = (file: File | undefined) => {
    if (input.current) input.current.value = '';
    if (!file) return;
    void run('Restore', async () => {
      const result = await restoreBackup(file);
      if (result.settings && typeof result.settings === 'object') update(result.settings as Partial<Settings>);
      onRestored();
      return `Restored ${result.added} of ${result.total} passes${result.added < result.total ? ' (the rest were already here)' : ''}.`;
    });
  };

  const kept = storage?.persisted === true ? 'kept by the system' : storage?.persisted === false ? 'may be cleared if the device runs low on space' : null;
  return (
    <section className="backup">
      <h2 className="group-label">Backup</h2>
      <p className="backup-note">
        Drill history lives on this device{kept && `, ${kept}`}
        {storage?.usageBytes !== undefined && ` (${formatBytes(storage.usageBytes)})`}. Export it to keep a copy.
      </p>
      <div className="actions">
        <button className="button" disabled={busy} onClick={onExport}>Export</button>
        <button className="button" disabled={busy} onClick={() => input.current?.click()}>Restore</button>
      </div>
      <input ref={input} type="file" accept="application/json,.json" hidden onChange={(e) => onRestore(e.target.files?.[0])} />
      {message && <p className="backup-note" role="status">{message}</p>}
    </section>
  );
}

export function Library() {
  const [settings, update] = useSettings();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [generation, setGeneration] = useState(0);
  return (
    <main className="page">
      <header className="page-header">
        <h1>Code Practice</h1>
        <button className="button subtle" onClick={() => setSettingsOpen(true)}>Settings</button>
      </header>
      <div className="lang-switch">
        <Segmented options={LANGS} value={settings.lang} onChange={(lang) => update({ lang })} />
      </div>
      <ProgramList key={generation} lang={settings.lang} />
      <BackupSection onRestored={() => setGeneration((n) => n + 1)} />
      <p className="page-footnote">Bundle {bundle.version}</p>
      {settingsOpen && <SettingsSheet onClose={() => setSettingsOpen(false)} />}
    </main>
  );
}

function ProgramList({ lang }: { lang: Lang }) {
  const latest = useLatestPasses();
  return (
    <>
      {TIERS.map(([tier, label]) => {
        const programs = bundle.programs.filter((program) => program.tier === tier);
        if (programs.length === 0) return null;
        return (
          <section key={tier} className="tier">
            <h2 className="group-label">{label}</h2>
            <ul className="rows">
              {programs.map((program) => {
                // A program without this language opens in Python.
                const impl = findImpl(program, lang) ?? program.impls[0]!;
                return (
                  <li key={program.id}>
                    <button className="row" onClick={() => navigate({ screen: 'program', program: program.id, lang: impl.lang })}>
                      <span className="row-title">
                        <span>{program.title}</span>
                        <span className="row-meta">{progressLabel(program, impl.lang, latest)}</span>
                      </span>
                      <span className="row-detail">
                        {impl.variant} · {LANGS.filter(([l]) => findImpl(program, l)).map(([, label]) => label).join(', ')}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>
        );
      })}
    </>
  );
}
