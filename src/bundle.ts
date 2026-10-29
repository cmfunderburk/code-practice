// The content bundle: the corpus's programs, split into drill units by
// scripts/build_bundle.py (see corpus/README.md). It is imported, so it ships
// inside the content-hashed script and the service worker caches it with the app.

import raw from './generated/bundle.json';

export interface Line {
  text: string;
  /** Leading spaces. */
  indent: number;
  /** The reveal step that shows this line. */
  step: number;
}

export interface Unit {
  id: string;
  name: string;
  kind: 'imports' | 'assignment' | 'class' | 'function' | 'main-guard' | 'method' | 'type' | 'impl' | 'module';
  cue: string;
  /** The step holding the unit's header (def, class, fn, struct, ...), or null. */
  signature: number | null;
  /** Of the unit's text: a changed hash marks old passes stale. */
  hash: string;
  /** Blank lines dropped after the unit. */
  gap: number;
  lines: Line[];
  children?: Unit[];
}

export type Lang = 'python' | 'rust' | 'c';

export interface Impl {
  id: string;
  variant: string;
  lang: Lang;
  docs: { problem: string; notes: string };
  /** What the read view shows: the drill source, or for a port its annotated solution. */
  readSource: string;
  /** 0-based line in readSource where each unit starts, children included. */
  readStarts: Record<string, number>;
  units: Unit[];
}

export interface Program {
  id: string;
  title: string;
  tier: 'easy' | 'medium' | 'hard';
  tags: string[];
  docs: { spec: string; defense: string };
  impls: Impl[];
}

export interface Bundle {
  version: string;
  programs: Program[];
}

export const bundle = raw as unknown as Bundle;

export function findProgram(id: string): Program | undefined {
  return bundle.programs.find((program) => program.id === id);
}

export const LANGS: Array<[Lang, string]> = [['python', 'Python'], ['rust', 'Rust'], ['c', 'C']];

export function findImpl(program: Program, lang: Lang): Impl | undefined {
  return program.impls.find((impl) => impl.lang === lang);
}

/** Number of reveal steps in a unit. */
export function stepCount(unit: Unit): number {
  const last = unit.lines[unit.lines.length - 1];
  return last ? last.step + 1 : 0;
}

