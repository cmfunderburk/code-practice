// What the passes say about each unit: its latest pass, and from that the mark
// the outline shows, a program's clean count, and which units to redo.

import type { Impl, Unit } from './bundle';
import type { PassRecord } from './store/db';

export type Latest = Map<string, PassRecord>;

const key = (implId: string, unitId: string) => `${implId}\u0000${unitId}`;

export function latestPasses(passes: PassRecord[]): Latest {
  const latest: Latest = new Map();
  for (const pass of passes) {
    const k = key(pass.implId, pass.unitId);
    const current = latest.get(k);
    if (!current || pass.at > current.at) latest.set(k, pass);
  }
  return latest;
}

export function latestFor(latest: Latest, impl: Impl, unit: Unit): PassRecord | undefined {
  return latest.get(key(impl.id, unit.id));
}

export type Mark =
  | { kind: 'new' }
  | { kind: 'clean' | 'stale'; at: number }
  | { kind: 'missed'; at: number; missed: number; steps: number };

export function unitMark(unit: Unit, pass: PassRecord | undefined): Mark {
  if (!pass) return { kind: 'new' };
  if (pass.sourceHash !== unit.hash) return { kind: 'stale', at: pass.at };
  if (pass.missed.length === 0) return { kind: 'clean', at: pass.at };
  return { kind: 'missed', at: pass.at, missed: pass.missed.length, steps: pass.steps };
}

/** Every unit in outline order: top-level units, each followed by its children. */
export function outlineUnits(impl: Impl): Unit[] {
  return impl.units.flatMap((unit) => [unit, ...(unit.children ?? [])]);
}

export function cleanCount(impl: Impl, latest: Latest): { clean: number; total: number } {
  const units = outlineUnits(impl);
  const clean = units.filter((unit) => unitMark(unit, latestFor(latest, impl, unit)).kind === 'clean').length;
  return { clean, total: units.length };
}

/** Units whose latest pass, on their current code, had misses, in outline order. */
export function flaggedUnits(impl: Impl, latest: Latest): Unit[] {
  return outlineUnits(impl).filter((unit) => unitMark(unit, latestFor(latest, impl, unit)).kind === 'missed');
}

/** "today", "yesterday", or a short date. */
export function dayLabel(at: number, now = Date.now()): string {
  const day = (t: number) => {
    const d = new Date(t);
    return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  };
  const days = Math.round((day(now) - day(at)) / 86_400_000);
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  return new Date(at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
