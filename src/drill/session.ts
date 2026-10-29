// The drill in progress, kept so a relaunch (or iPadOS discarding the app in
// the background) reopens it as it was: revealed steps, flags, the run, and
// which saved pass each finished unit's later flag changes update.

import type { Impl } from '../bundle';
import { outlineUnits } from '../progress';
import { getSetting, putSetting } from '../store/db';
import type { DrillState } from './state';

const SESSION_KEY = 'drillSession';

export interface SavedPass {
  id: number;
  at: number;
}

export interface DrillSession {
  /** program/lang/scope: a session only resumes the same drill. */
  key: string;
  /** The impl's units when saved: a session whose code changed since is dropped. */
  source?: string;
  states: Record<string, DrillState>;
  runIds: string[] | null;
  finished: boolean;
  showSignature: boolean;
  passes: Record<string, SavedPass>;
}

export function sessionSource(impl: Impl): string {
  return outlineUnits(impl).map((unit) => `${unit.id}:${unit.hash}`).join('\n');
}

export function loadSession(): Promise<DrillSession | undefined> {
  return getSetting<DrillSession>(SESSION_KEY).catch(() => undefined);
}

let pending: ReturnType<typeof setTimeout> | undefined;

/** Save soon: a burst of taps writes once. */
export function saveSession(session: DrillSession): void {
  clearTimeout(pending);
  pending = setTimeout(() => void putSetting(SESSION_KEY, session).catch(() => undefined), 300);
}
