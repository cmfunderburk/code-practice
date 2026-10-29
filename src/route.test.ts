import { describe, expect, it } from 'bun:test';
import { parseRoute, routeHash, type Route } from './route';

describe('routes', () => {
  const routes: Route[] = [
    { screen: 'library' },
    { screen: 'program', program: 'Hangman', lang: 'python' },
    { screen: 'read', program: 'Hangman', lang: 'python', tab: 'defense' },
    { screen: 'read', program: 'Snake-Engine', lang: 'python', tab: 'code', unit: 'WIDTH, HEIGHT' },
    { screen: 'read', program: 'Editor-Buffer', lang: 'python', tab: 'code', unit: 'EditorBuffer.__init__' },
    { screen: 'drill', program: 'Hangman', lang: 'python', scope: 'all', unit: 'imports' },
    { screen: 'drill', program: 'Snake-Engine', lang: 'python', scope: 'one', unit: 'WIDTH, HEIGHT' },
    { screen: 'drill', program: 'Editor-Buffer', lang: 'python', scope: 'flagged', unit: 'EditorBuffer.undo' },
  ];

  it('round-trip through the hash', () => {
    for (const route of routes) expect(parseRoute(routeHash(route))).toEqual(route);
  });

  it('fall back to the library, and to the code tab', () => {
    expect(parseRoute('')).toEqual({ screen: 'library' });
    expect(parseRoute('#/p/Hangman/cobol')).toEqual({ screen: 'library' });
    expect(parseRoute('#/p/Hangman/python/drill/some/main')).toEqual({ screen: 'program', program: 'Hangman', lang: 'python' });
    expect(parseRoute('#/p/Hangman/python/read/nope')).toEqual({
      screen: 'read', program: 'Hangman', lang: 'python', tab: 'code',
    });
  });
});
