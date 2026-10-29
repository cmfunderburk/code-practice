// A unit's drill state as pure functions: how many steps are revealed, and
// which revealed steps are flagged as missed (the README's Drilling section).
// Steps before `given` are shown before recall starts (the signature toggle)
// and can't be hidden or flagged.

import { stepCount, type Unit } from '../bundle';

export interface DrillState {
  revealed: number;
  /** Flagged steps, ascending. */
  flagged: number[];
}

/** Steps shown as given: through the def/class header when signatures are on. */
export function givenSteps(unit: Unit, showSignature: boolean): number {
  return showSignature && unit.signature !== null ? unit.signature + 1 : 0;
}

export function initialState(given: number): DrillState {
  return { revealed: given, flagged: [] };
}

/** Apply a changed `given` (the signature toggle) without losing progress. */
export function withGiven(state: DrillState, given: number): DrillState {
  if (state.revealed >= given) return { ...state, flagged: state.flagged.filter((step) => step >= given) };
  return { revealed: given, flagged: state.flagged.filter((step) => step >= given) };
}

export function reveal(state: DrillState, unit: Unit): DrillState {
  return { ...state, revealed: Math.min(stepCount(unit), state.revealed + 1) };
}

export function hide(state: DrillState, given: number): DrillState {
  const revealed = Math.max(given, state.revealed - 1);
  return { revealed, flagged: state.flagged.filter((step) => step < revealed) };
}

/** Each step's indent: that of its first code line (not blank, not a comment). */
export function stepIndents(unit: Unit): number[] {
  const indents: number[] = [];
  for (const line of unit.lines) {
    const trimmed = line.text.trimStart();
    // `//` too, for the Rust and C ports; no Python line starts with it.
    const code = trimmed !== '' && !trimmed.startsWith('#') && !trimmed.startsWith('//');
    if (indents[line.step] === undefined || (code && indents[line.step]! < 0)) {
      indents[line.step] = code ? line.indent : -1;
    }
  }
  return indents.map((indent) => Math.max(indent, 0));
}

/** Reveal the rest of the block the next step is in: every following step indented at
 * least as deep, stopping at the first one that dedents. */
export function revealBlock(state: DrillState, unit: Unit): DrillState {
  const total = stepCount(unit);
  if (state.revealed >= total) return state;
  const indents = stepIndents(unit);
  const depth = indents[state.revealed]!;
  let end = state.revealed + 1;
  while (end < total && indents[end]! >= depth) end += 1;
  return { ...state, revealed: end };
}

export function toggleFlag(state: DrillState, step: number, given: number): DrillState {
  if (step < given || step >= state.revealed) return state;
  const flagged = state.flagged.includes(step)
    ? state.flagged.filter((s) => s !== step)
    : [...state.flagged, step].sort((a, b) => a - b);
  return { ...state, flagged };
}

export interface Outcome {
  /** Steps recalled: all but the given ones. */
  steps: number;
  missed: number[];
}

/** The pass's outcome once every step is revealed, else null. */
export function outcome(state: DrillState, unit: Unit, given: number): Outcome | null {
  if (state.revealed < stepCount(unit)) return null;
  return { steps: stepCount(unit) - given, missed: state.flagged };
}
