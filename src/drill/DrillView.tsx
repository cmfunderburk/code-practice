import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { stepCount, type Impl, type Program, type Unit } from '../bundle';
import { CodeLine } from '../code/CodeLine';
import { highlight, type Token } from '../code/highlight';
import { flaggedUnits, latestPasses, outlineUnits } from '../progress';
import { isLaunchRoute, navigate, type DrillScope } from '../route';
import { useSettings } from '../settings';
import { listPasses, savePass } from '../store/db';
import { loadSession, saveSession, sessionSource, type DrillSession, type SavedPass } from './session';
import {
  givenSteps, hide, initialState, outcome, reveal, revealBlock, toggleFlag, withGiven,
  type DrillState, type Outcome,
} from './state';
import { useDrillGestures } from './useDrillGestures';

/** The units a drill pages through: a run's top-level units, or the whole outline
 * (narrowed to the flagged units by the run's ids). */
function sequenceFor(impl: Impl, scope: DrillScope): Unit[] {
  return scope === 'all' ? impl.units : outlineUnits(impl);
}

function unitTokens(unit: Unit, lang: string): Token[][] {
  return highlight(unit.lines.map((line) => line.text).join('\n'), lang);
}

function resultLabel(result: Outcome | null): string {
  if (!result) return 'not finished';
  return result.missed.length === 0 ? 'clean' : `missed ${result.missed.length}/${result.steps}`;
}

/** An earlier unit of a run, dimmed above the current one: its first line, or all of it. */
function ContextUnit({ unit, lang }: { unit: Unit; lang: string }) {
  const [open, setOpen] = useState(false);
  const tokens = useMemo(() => unitTokens(unit, lang), [unit, lang]);
  const first = Math.max(0, unit.lines.findIndex((line) => line.text.trim() && !line.text.trimStart().startsWith('#')));
  const shown = open ? unit.lines.map((_, i) => i) : [first];
  return (
    <button className={`context-unit${open ? ' open' : ''}`} onClick={() => setOpen(!open)} aria-expanded={open}>
      {shown.map((i) => <CodeLine key={i} tokens={tokens[i]!} indent={unit.lines[i]!.indent} />)}
      {!open && unit.lines.length > 1 && <span className="context-more">…</span>}
    </button>
  );
}

function DrillLines({ unit, lang, state, given }: { unit: Unit; lang: string; state: DrillState; given: number }) {
  const tokens = useMemo(() => unitTokens(unit, lang), [unit, lang]);
  return (
    <>
      {unit.lines.map((line, i) => {
        const shown = line.step < state.revealed;
        const classes = ['drill-line'];
        if (!shown) classes.push('hidden');
        if (!shown && line.step === state.revealed) classes.push('next');
        if (line.step < given) classes.push('given');
        if (state.flagged.includes(line.step)) classes.push('flagged');
        return (
          <div key={i} className={classes.join(' ')} data-step={line.step}>
            <span className="gutter" data-gutter aria-hidden />
            {shown ? (
              <CodeLine tokens={tokens[i]!} indent={line.indent} />
            ) : (
              <div className="code-line" style={{ '--indent': `${line.indent}ch` } as React.CSSProperties}>
                {line.text.trim() ? <span className="bar" style={{ width: `${line.text.length - line.indent}ch` }} /> : ' '}
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}

function RunSummary({ units, results, onAgain, onRedo, onBack }: {
  units: Unit[];
  results: Map<string, Outcome | null>;
  onAgain: () => void;
  onRedo: (() => void) | null;
  onBack: () => void;
}) {
  const clean = units.filter((unit) => results.get(unit.id)?.missed.length === 0).length;
  return (
    <div className="run-summary">
      <h2>Run finished: {clean}/{units.length} clean</h2>
      <ul className="rows">
        {units.map((unit) => {
          const result = results.get(unit.id) ?? null;
          return (
            <li key={unit.id} className="row summary-row">
              <span className="row-title">
                <span className="unit-name">{unit.name}</span>
                <span className={`result ${result?.missed.length === 0 ? 'clean' : 'missed'}`}>{resultLabel(result)}</span>
              </span>
            </li>
          );
        })}
      </ul>
      <div className="actions">
        <button className="button primary" onClick={onAgain}>Again</button>
        {onRedo && <button className="button" onClick={onRedo}>Redo flagged</button>}
        <button className="button" onClick={onBack}>Back</button>
      </div>
    </div>
  );
}

interface DrillProps {
  program: Program;
  impl: Impl;
  scope: DrillScope;
  unitId: string;
}

/** Load what the drill starts from: the session, when the app relaunched into this drill,
 * and for a flagged run, the passes that say which units to redo. */
export function DrillView(props: DrillProps) {
  const { impl, scope } = props;
  const [settings] = useSettings();
  const [initial, setInitial] = useState<DrillSession | null>(null);
  const key = `${props.program.id}/${impl.lang}/${scope}`;

  useEffect(() => {
    let live = true;
    const launch = isLaunchRoute();
    void (async () => {
      const session = launch ? await loadSession() : undefined;
      let start: DrillSession;
      if (session?.key === key && session.source === sessionSource(impl)) {
        start = session;
      } else {
        const runIds = scope === 'flagged'
          ? flaggedUnits(impl, latestPasses(await listPasses(impl.id).catch(() => []))).map((u) => u.id)
          : null;
        start = { key, source: sessionSource(impl), states: {}, runIds, finished: false, showSignature: settings.showSignature, passes: {} };
      }
      if (live) setInitial(start);
    })();
    return () => { live = false; };
  }, []);

  if (!initial) return null;
  if (initial.runIds?.length === 0) {
    return (
      <div className="drill">
        <div className="drill-scroll">
          <div className="run-summary">
            <h2>Nothing flagged</h2>
            <p className="page-subtitle">Every unit's latest pass was clean.</p>
            <button className="button" onClick={() => navigate({ screen: 'program', program: props.program.id, lang: impl.lang })}>Back</button>
          </div>
        </div>
      </div>
    );
  }
  return <DrillScreen {...props} initial={initial} />;
}

function DrillScreen({ program, impl, scope, unitId, initial }: DrillProps & { initial: DrillSession }) {
  const [settings] = useSettings();
  const [showSignature, setShowSignature] = useState(initial.showSignature);
  const [states, setStates] = useState<Record<string, DrillState>>(initial.states);
  // A "redo flagged" run covers only some units; null is every unit in the sequence.
  const [runIds, setRunIds] = useState<string[] | null>(initial.runIds);
  const [finished, setFinished] = useState(initial.finished);
  const scrollRef = useRef<HTMLDivElement>(null);
  // Each finished unit's saved pass, so flag changes after finishing update it.
  const passes = useRef(new Map<string, Promise<SavedPass | null>>(
    Object.entries(initial.passes).map(([id, saved]) => [id, Promise.resolve(saved)]),
  ));
  const savedPasses = useRef<Record<string, SavedPass>>({ ...initial.passes });

  const sequence = useMemo(() => {
    const all = sequenceFor(impl, scope);
    return runIds ? all.filter((unit) => runIds.includes(unit.id)) : all;
  }, [impl, scope, runIds]);
  const index = Math.max(0, sequence.findIndex((unit) => unit.id === unitId));
  const unit = sequence[index]!;
  const given = givenSteps(unit, showSignature);
  const state = withGiven(states[unit.id] ?? initialState(given), given);
  const result = outcome(state, unit, given);
  const base = { program: program.id, lang: impl.lang };

  const results = useMemo(() => new Map(sequence.map((u) => {
    const g = givenSteps(u, showSignature);
    return [u.id, outcome(withGiven(states[u.id] ?? initialState(g), g), u, g)];
  })), [sequence, states, showSignature]);

  const update = useCallback((change: (state: DrillState) => DrillState) => {
    setStates((prev) => ({ ...prev, [unit.id]: change(withGiven(prev[unit.id] ?? initialState(given), given)) }));
  }, [unit.id, given]);

  const goTo = useCallback((target: Unit) => {
    setFinished(false);
    navigate({ screen: 'drill', ...base, scope, unit: target.id }, { replace: true });
  }, [base.program, base.lang, scope]);

  const step = useCallback((by: 1 | -1) => {
    const target = sequence[index + by];
    if (target) goTo(target);
  }, [sequence, index, goTo]);

  const forgetPass = (id: string) => {
    passes.current.delete(id);
    delete savedPasses.current[id];
  };
  const resetUnit = () => {
    forgetPass(unit.id);
    update(() => initialState(given));
  };
  const next = () => {
    if (index < sequence.length - 1) step(1);
    else if (scope !== 'one') setFinished(true);
  };
  const restartRun = (ids: string[] | null) => {
    const all = sequenceFor(impl, scope);
    const units = ids ? all.filter((u) => ids.includes(u.id)) : all;
    setStates((prev) => {
      const copy = { ...prev };
      for (const u of units) delete copy[u.id];
      return copy;
    });
    for (const u of units) forgetPass(u.id);
    setRunIds(ids);
    if (units[0]) goTo(units[0]);
  };

  const gestures = useDrillGestures({
    onTap(zone, target) {
      const gutter = target.closest('[data-gutter]');
      const line = target.closest<HTMLElement>('[data-step]');
      if (gutter && line && Number(line.dataset.step) < state.revealed) {
        update((s) => toggleFlag(s, Number(line.dataset.step), given));
        return;
      }
      update((s) => (zone === 'reveal' ? reveal(s, unit) : hide(s, given)));
    },
    onSwipe: (direction) => step(direction === 'next' ? 1 : -1),
    onLongPress: () => update((s) => revealBlock(s, unit)),
  }, settings.swapZones);

  // Save the pass once the unit is finished; later flag changes update the same record.
  const missedKey = result ? result.missed.join(',') : null;
  useEffect(() => {
    if (!result) return;
    const id = unit.id;
    const record = {
      implId: impl.id, unitId: id, at: Date.now(), steps: result.steps, missed: result.missed,
      signatureShown: given > 0, sourceHash: unit.hash,
    };
    const saving = (passes.current.get(id) ?? Promise.resolve(null))
      .catch(() => null)
      .then(async (saved) => {
        const at = saved?.at ?? record.at;
        return { id: await savePass({ ...record, at, ...(saved ? { id: saved.id } : {}) }), at };
      });
    passes.current.set(id, saving);
    saving.then((saved) => {
      if (passes.current.get(id) === saving) savedPasses.current[id] = saved;
    }).catch(() => undefined);
  }, [missedKey, unit.id, given]);

  // Keep the session for a relaunch.
  useEffect(() => {
    saveSession({
      key: `${program.id}/${impl.lang}/${scope}`, source: sessionSource(impl), states, runIds, finished, showSignature, passes: savedPasses.current,
    });
  }, [states, runIds, finished, showSignature, unit.id]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (finished) {
        if (event.key === 'Escape') navigate({ screen: 'program', ...base });
        return;
      }
      const keys: Record<string, () => void> = {
        ' ': () => update((s) => reveal(s, unit)),
        Backspace: () => update((s) => hide(s, given)),
        m: () => update((s) => toggleFlag(s, s.revealed - 1, given)),
        r: resetUnit,
        s: () => setShowSignature((on) => !on),
        ArrowRight: () => step(1),
        ArrowLeft: () => step(-1),
        Enter: () => result && next(),
        Escape: () => navigate({ screen: 'program', ...base }),
      };
      const action = keys[event.key];
      if (!action) return;
      event.preventDefault();
      action();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  // Keep the next hidden line (or, once done, the footer) in view.
  useEffect(() => {
    const target = scrollRef.current?.querySelector('.drill-line.next') ?? scrollRef.current?.querySelector('.drill-footer');
    target?.scrollIntoView({ block: 'nearest' });
  }, [state.revealed, unit.id]);

  // A new unit starts at the top of its context.
  useEffect(() => {
    scrollRef.current?.querySelector('.drill-head')?.scrollIntoView({ block: 'start' });
  }, [unit.id]);

  return (
    <div className="drill">
      <header className="read-bar">
        <button className="button subtle back" onClick={() => navigate({ screen: 'program', ...base })}>‹ {program.title}</button>
        <span className="drill-position">{index + 1} / {sequence.length}</span>
        <div className="drill-tools">
          <button
            className={`button subtle${showSignature ? ' pressed' : ''}`}
            aria-pressed={showSignature}
            onClick={() => setShowSignature(!showSignature)}
          >
            Signature
          </button>
          <button className="button subtle" onClick={() => navigate({ screen: 'read', ...base, tab: 'code', unit: unit.id })}>Read</button>
          <button className="button subtle" onClick={resetUnit} disabled={state.revealed === given}>Reset</button>
        </div>
      </header>
      <div className="drill-scroll" ref={scrollRef}>
        {finished ? (
          <RunSummary
            units={sequence}
            results={results}
            onAgain={() => restartRun(null)}
            onRedo={sequence.some((u) => results.get(u.id)?.missed.length) ?
              () => restartRun(sequence.filter((u) => results.get(u.id)?.missed.length).map((u) => u.id)) : null}
            onBack={() => navigate({ screen: 'program', ...base })}
          />
        ) : (
          <>
            {scope === 'all' && index > 0 && (
              <div className="drill-context">
                {sequence.slice(0, index).map((u) => <ContextUnit key={u.id} unit={u} lang={impl.lang} />)}
              </div>
            )}
            <div className="drill-head">
              <div className="drill-name">{unit.name}</div>
              {unit.cue && <p className="drill-cue">{unit.cue}</p>}
            </div>
            <div className="drill-lines" {...gestures}>
              <DrillLines unit={unit} lang={impl.lang} state={state} given={given} />
              {result ? (
                <footer className="drill-footer" onPointerDown={(e) => e.stopPropagation()} onPointerUp={(e) => e.stopPropagation()}>
                  <span className={`result ${result.missed.length === 0 ? 'clean' : 'missed'}`}>{resultLabel(result)}</span>
                  <div className="actions">
                    <button className="button" onClick={resetUnit}>Again</button>
                    {index < sequence.length - 1 && <button className="button primary" onClick={next}>Next</button>}
                    {index === sequence.length - 1 && scope !== 'one' && <button className="button primary" onClick={next}>Done</button>}
                  </div>
                </footer>
              ) : (
                <div className="drill-progress">{state.revealed - given} / {stepCount(unit) - given}</div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
