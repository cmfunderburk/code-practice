import { describe, expect, it } from 'bun:test';
import type { Unit } from '../bundle';
import { givenSteps, hide, initialState, outcome, reveal, revealBlock, stepIndents, toggleFlag, withGiven } from './state';

// def total(xs):          step 0  (after a comment, step 0 too)
//     acc = 0             step 1
//     for x in xs:        step 2
//         acc += x        step 3
//         # note          step 4 (joins the next line)
//         n += 1          step 4
//     return acc          step 5
const lines: Array<[string, number]> = [
  ['# Sum them.', 0], ['def total(xs):', 0], ['    acc = 0', 1], ['    for x in xs:', 2],
  ['        acc += x', 3], ['        # note', 4], ['        n += 1', 4], ['    return acc', 5],
];
const unit: Unit = {
  id: 'total', name: 'total', kind: 'function', cue: '', signature: 0, hash: '', gap: 0,
  lines: lines.map(([text, step]) => ({ text, step, indent: text.length - text.trimStart().length })),
};

describe('drill state', () => {
  it('gives the signature steps only when asked', () => {
    expect(givenSteps(unit, false)).toBe(0);
    expect(givenSteps(unit, true)).toBe(1);
    expect(givenSteps({ ...unit, signature: null }, true)).toBe(0);
  });

  it('reveals and hides one step at a time, never below the given steps', () => {
    let state = initialState(1);
    state = reveal(reveal(state, unit), unit);
    expect(state.revealed).toBe(3);
    state = hide(hide(hide(state, 1), 1), 1);
    expect(state.revealed).toBe(1);
    for (let i = 0; i < 10; i += 1) state = reveal(state, unit);
    expect(state.revealed).toBe(6);
  });

  it('takes step indents from code lines, not comments', () => {
    expect(stepIndents(unit)).toEqual([0, 4, 4, 8, 8, 4]);
  });

  it('reveals the rest of a block', () => {
    // Next step is `acc += x` (depth 8): reveal it and `n += 1`, stop at `return`.
    expect(revealBlock({ revealed: 3, flagged: [] }, unit).revealed).toBe(5);
    // Next step is `acc = 0` (depth 4): the whole body.
    expect(revealBlock({ revealed: 1, flagged: [] }, unit).revealed).toBe(6);
    // Next step is the header: everything.
    expect(revealBlock(initialState(0), unit).revealed).toBe(6);
  });

  it('flags revealed, non-given steps; hiding a flagged step drops its flag', () => {
    let state: ReturnType<typeof initialState> = { revealed: 4, flagged: [] };
    state = toggleFlag(state, 0, 1); // given
    state = toggleFlag(state, 5, 1); // hidden
    expect(state.flagged).toEqual([]);
    state = toggleFlag(toggleFlag(state, 3, 1), 2, 1);
    expect(state.flagged).toEqual([2, 3]);
    expect(toggleFlag(state, 3, 1).flagged).toEqual([2]);
    expect(hide(state, 1).flagged).toEqual([2]);
  });

  it('adjusts to a changed signature toggle', () => {
    expect(withGiven(initialState(0), 1)).toEqual({ revealed: 1, flagged: [] });
    expect(withGiven({ revealed: 3, flagged: [0, 2] }, 1)).toEqual({ revealed: 3, flagged: [2] });
    expect(withGiven({ revealed: 3, flagged: [2] }, 0)).toEqual({ revealed: 3, flagged: [2] });
  });

  it('has an outcome only when every step is revealed', () => {
    expect(outcome({ revealed: 5, flagged: [] }, unit, 1)).toBeNull();
    expect(outcome({ revealed: 6, flagged: [3] }, unit, 1)).toEqual({ steps: 5, missed: [3] });
  });
});
