import { describe, expect, it } from 'bun:test';
import { findProgram } from './bundle';
import { cleanCount, dayLabel, flaggedUnits, latestFor, latestPasses, outlineUnits, unitMark } from './progress';
import type { PassRecord } from './store/db';

const impl = findProgram('Hangman')!.impls[0]!;
const unit = (id: string) => impl.units.find((u) => u.id === id)!;
const pass = (unitId: string, at: number, missed: number[] = [], sourceHash = unit(unitId).hash): PassRecord => ({
  implId: impl.id, unitId, at, steps: 5, missed, signatureShown: false, sourceHash,
});

describe('progress', () => {
  it('keeps the latest pass per unit', () => {
    const latest = latestPasses([pass('masked', 2, [1]), pass('masked', 5), pass('masked', 3, [2])]);
    expect(latestFor(latest, impl, unit('masked'))?.at).toBe(5);
  });

  it('marks units new, clean, missed or stale', () => {
    expect(unitMark(unit('masked'), undefined)).toEqual({ kind: 'new' });
    expect(unitMark(unit('masked'), pass('masked', 1))).toEqual({ kind: 'clean', at: 1 });
    expect(unitMark(unit('masked'), pass('masked', 1, [0, 3]))).toEqual({ kind: 'missed', at: 1, missed: 2, steps: 5 });
    expect(unitMark(unit('masked'), pass('masked', 1, [], 'old'))).toEqual({ kind: 'stale', at: 1 });
  });

  it('counts clean units and lists flagged ones, ignoring stale passes', () => {
    const latest = latestPasses([
      pass('masked', 1), pass('status', 1, [2]), pass('guess', 1, [1], 'old'), pass('wrong_count', 1, [1]),
    ]);
    expect(cleanCount(impl, latest)).toEqual({ clean: 1, total: outlineUnits(impl).length });
    expect(flaggedUnits(impl, latest).map((u) => u.id)).toEqual(['wrong_count', 'status']);
  });

  it('labels days', () => {
    const now = new Date(2026, 9, 27, 9).getTime();
    expect(dayLabel(new Date(2026, 9, 27, 1).getTime(), now)).toBe('today');
    expect(dayLabel(new Date(2026, 9, 26, 23).getTime(), now)).toBe('yesterday');
  });
});
