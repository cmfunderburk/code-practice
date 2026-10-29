import { useEffect, useState } from 'react';
import type { Lang } from './bundle';
import { getSetting, putSetting } from './store/db';

// Hash routes, so a reload (or reopening the home-screen app) lands on the same screen.
export const READ_TABS = ['code', 'spec', 'problem', 'notes', 'defense'] as const;
export type ReadTab = (typeof READ_TABS)[number];

export type Route =
  | { screen: 'library' }
  | { screen: 'program'; program: string; lang: Lang }
  | { screen: 'read'; program: string; lang: Lang; tab: ReadTab; unit?: string }
  // `all`: a whole-program run, now at `unit`; `one`: just `unit`.
  | { screen: 'drill'; program: string; lang: Lang; scope: DrillScope; unit: string };

// `flagged`: the units whose latest pass had misses, as a run.
export type DrillScope = 'all' | 'one' | 'flagged';
const SCOPES: readonly string[] = ['all', 'one', 'flagged'];

const LANGS: readonly string[] = ['python', 'rust', 'c'];

export function parseRoute(hash: string): Route {
  const parts = hash.replace(/^#\/?/, '').split('/').map(decodeURIComponent);
  // read/<tab>[/<unit>] or drill/<scope>/<unit>
  const [head, program, lang, view, sub, unit] = parts;
  if (head !== 'p' || !program || !lang || !LANGS.includes(lang)) return { screen: 'library' };
  const base = { program, lang: lang as Lang };
  if (view === 'read') {
    const readTab = (READ_TABS as readonly string[]).includes(sub ?? '') ? (sub as ReadTab) : 'code';
    return { screen: 'read', ...base, tab: readTab, ...(unit ? { unit } : {}) };
  }
  if (view === 'drill' && SCOPES.includes(sub ?? '') && unit) {
    return { screen: 'drill', ...base, scope: sub as DrillScope, unit };
  }
  return { screen: 'program', ...base };
}

export function routeHash(route: Route): string {
  if (route.screen === 'library') return '#/';
  const base = `#/p/${encodeURIComponent(route.program)}/${route.lang}`;
  if (route.screen === 'program') return base;
  if (route.screen === 'drill') return `${base}/drill/${route.scope}/${encodeURIComponent(route.unit)}`;
  return `${base}/read/${route.tab}${route.unit ? `/${encodeURIComponent(route.unit)}` : ''}`;
}

export function navigate(route: Route, { replace = false } = {}): void {
  const hash = routeHash(route);
  if (!replace) {
    location.hash = hash;
    return;
  }
  history.replaceState(null, '', hash);
  window.dispatchEvent(new HashChangeEvent('hashchange'));
}

// The route the app launched on, until the first navigation. A drill restores its
// session only when the app opened straight into it (a relaunch), not when you
// open it again from the outline.
let launchHash: string | null = null;

export function markLaunch(): void {
  launchHash = location.hash;
  window.addEventListener('hashchange', () => { launchHash = null; }, { once: true });
}

export function isLaunchRoute(): boolean {
  return launchHash !== null && launchHash === location.hash;
}

const LAST_ROUTE_KEY = 'lastRoute';

/** At launch with no route (the home-screen app always opens at /), go back to the last screen. */
export async function restoreLastRoute(): Promise<void> {
  if (location.hash && location.hash !== '#/') return;
  const saved = await getSetting<string>(LAST_ROUTE_KEY).catch(() => undefined);
  if (saved) history.replaceState(null, '', saved);
}

export function rememberRoutes(): void {
  const save = () => void putSetting(LAST_ROUTE_KEY, location.hash).catch(() => undefined);
  window.addEventListener('hashchange', save);
  save();
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseRoute(location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parseRoute(location.hash));
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return route;
}
