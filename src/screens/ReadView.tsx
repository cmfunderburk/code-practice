import { useEffect, useMemo, useRef } from 'react';
import type { Impl, Program } from '../bundle';
import { CodeLine } from '../code/CodeLine';
import { highlight } from '../code/highlight';
import { Markdown } from '../markdown/Markdown';
import { navigate, type ReadTab } from '../route';

const TAB_LABELS: Record<ReadTab, string> = { code: 'Code', spec: 'Spec', problem: 'Problem', notes: 'Notes', defense: 'Defense' };

function docFor(tab: ReadTab, program: Program, impl: Impl): string {
  switch (tab) {
    case 'code': return impl.readSource;
    case 'spec': return program.docs.spec;
    case 'problem': return impl.docs.problem;
    case 'notes': return impl.docs.notes;
    case 'defense': return program.docs.defense;
  }
}

function SourceView({ impl, unit }: { impl: Impl; unit?: string }) {
  const lines = useMemo(() => highlight(impl.readSource, impl.lang), [impl]);
  // Top-level unit names label the lines they start on.
  const labels = useMemo(() => new Map(impl.units.map((u) => [impl.readStarts[u.id]!, u.name])), [impl]);
  const target = unit === undefined ? undefined : impl.readStarts[unit];
  const targetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    targetRef.current?.scrollIntoView({ block: 'start' });
  }, [target]);

  return (
    <div className="source">
      {lines.map((tokens, i) => {
        const text = tokens.map((t) => t.text).join('');
        const label = labels.get(i);
        return (
          <div key={i} ref={i === target ? targetRef : undefined} className={i === target ? 'scroll-target' : undefined}>
            {label !== undefined && <div className="unit-label">{label}</div>}
            <CodeLine tokens={tokens} indent={text.length - text.trimStart().length} />
          </div>
        );
      })}
    </div>
  );
}

export function ReadView({ program, impl, tab, unit }: { program: Program; impl: Impl; tab: ReadTab; unit?: string }) {
  const tabs = (Object.keys(TAB_LABELS) as ReadTab[]).filter((t) => docFor(t, program, impl));
  const bodyRef = useRef<HTMLDivElement>(null);
  const base = { program: program.id, lang: impl.lang };

  useEffect(() => {
    if (unit === undefined) bodyRef.current?.scrollTo(0, 0);
  }, [tab, unit]);

  return (
    <div className="read">
      <header className="read-bar">
        <button className="button subtle back" onClick={() => navigate({ screen: 'program', ...base })}>‹ {program.title}</button>
        <nav className="tabs">
          {tabs.map((t) => (
            <button
              key={t}
              className={t === tab ? 'selected' : ''}
              onClick={() => navigate({ screen: 'read', ...base, tab: t }, { replace: true })}
            >
              {TAB_LABELS[t]}
            </button>
          ))}
        </nav>
      </header>
      <div className="read-body" ref={bodyRef}>
        {tab === 'code' ? <SourceView impl={impl} unit={unit} /> : <Markdown source={docFor(tab, program, impl)} />}
      </div>
    </div>
  );
}
