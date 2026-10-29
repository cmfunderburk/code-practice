import { findImpl, LANGS, stepCount, type Impl, type Lang, type Program, type Unit } from '../bundle';
import { cleanCount, dayLabel, flaggedUnits, latestFor, unitMark, type Latest, type Mark } from '../progress';
import { navigate, type DrillScope, type ReadTab } from '../route';
import { useSettings } from '../settings';
import { Segmented } from '../Sheets';
import { useLatestPasses } from '../usePasses';

function MarkLabel({ mark }: { mark: Mark }) {
  switch (mark.kind) {
    case 'new': return <span className="mark new">·</span>;
    case 'clean': return <span className="mark clean">✓ {dayLabel(mark.at)}</span>;
    case 'missed': return <span className="mark missed">{mark.missed}/{mark.steps} · {dayLabel(mark.at)}</span>;
    case 'stale': return <span className="mark stale">changed · {dayLabel(mark.at)}</span>;
  }
}

/** A child unit's name without its parent's: `State.bump` → `bump`, `Game::new` → `new`. */
export function childName(name: string): string {
  return name.replace(/^.*?(\.|::)/, '');
}

function UnitRow({ unit, mark, child = false, onOpen }: { unit: Unit; mark: Mark | null; child?: boolean; onOpen: (unit: Unit) => void }) {
  return (
    <li>
      <button className={`row unit-row${child ? ' child' : ''}`} onClick={() => onOpen(unit)}>
        <span className="row-title">
          <span className="unit-name">{child ? childName(unit.name) : unit.name}</span>
          <span className="row-meta">
            {mark && <MarkLabel mark={mark} />}
            <span className="steps">{stepCount(unit)} steps</span>
          </span>
        </span>
        {unit.cue && <span className="row-detail cue">{unit.cue}</span>}
      </button>
    </li>
  );
}

export function ProgramView({ program, impl }: { program: Program; impl: Impl }) {
  const latest = useLatestPasses(impl.id);
  const [, update] = useSettings();
  const langs = LANGS.filter(([lang]) => findImpl(program, lang));
  const switchLang = (lang: Lang) => {
    update({ lang });
    navigate({ screen: 'program', program: program.id, lang }, { replace: true });
  };
  const base = { program: program.id, lang: impl.lang };
  const read = (tab: ReadTab) => navigate({ screen: 'read', ...base, tab });
  const drill = (scope: DrillScope, unit: string) => navigate({ screen: 'drill', ...base, scope, unit });
  const flagged = latest ? flaggedUnits(impl, latest) : [];
  const counts = latest ? cleanCount(impl, latest) : null;
  const markFor = (unit: Unit, ready: Latest | null) => (ready ? unitMark(unit, latestFor(ready, impl, unit)) : null);
  const docs: Array<[ReadTab, string, string]> = [
    ['spec', 'Spec', program.docs.spec],
    ['problem', 'Problem', impl.docs.problem],
    ['notes', 'Notes', impl.docs.notes],
    ['defense', 'Defense', program.docs.defense],
  ];

  return (
    <main className="page">
      <header className="page-header">
        <button className="button subtle back" onClick={() => navigate({ screen: 'library' })}>‹ Library</button>
        {langs.length > 1 && <Segmented options={langs} value={impl.lang} onChange={switchLang} />}
      </header>
      <h1 className="page-title">{program.title}</h1>
      <p className="page-subtitle">
        {impl.variant} · {program.tier}{program.tags.length > 0 && ` · ${program.tags.join(', ')}`}
        {counts && ` · ${counts.clean}/${counts.total} clean`}
      </p>
      <div className="actions">
        <button className="button primary" onClick={() => drill('all', impl.units[0]!.id)}>Drill whole program</button>
        {flagged.length > 0 && (
          <button className="button" onClick={() => drill('flagged', flagged[0]!.id)}>Redo flagged ({flagged.length})</button>
        )}
        <button className="button" onClick={() => read('code')}>Read code</button>
        {docs.filter(([, , text]) => text).map(([tab, label]) => (
          <button key={tab} className="button" onClick={() => read(tab)}>{label}</button>
        ))}
      </div>
      <h2 className="group-label">Units</h2>
      <ul className="rows">
        {impl.units.map((unit) => (
          <UnitGroup key={unit.id} unit={unit} markFor={(u) => markFor(u, latest)} onOpen={(u) => drill('one', u.id)} />
        ))}
      </ul>
    </main>
  );
}

function UnitGroup({ unit, markFor, onOpen }: { unit: Unit; markFor: (unit: Unit) => Mark | null; onOpen: (unit: Unit) => void }) {
  return (
    <>
      <UnitRow unit={unit} mark={markFor(unit)} onOpen={onOpen} />
      {unit.children?.map((child) => <UnitRow key={child.id} unit={child} mark={markFor(child)} child onOpen={onOpen} />)}
    </>
  );
}
