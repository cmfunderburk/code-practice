import 'fake-indexeddb/auto';
import { describe, expect, it } from 'bun:test';
import { BackupError, exportState, parseBackup, restoreBackup } from './backup';
import { listPasses, savePass, type PassRecord } from './store/db';

const pass = (unitId: string, at: number): PassRecord => ({
  implId: 'Hangman/functional-core/python', unitId, at, steps: 4, missed: [1], signatureShown: false, sourceHash: 'abc',
});

describe('backup', () => {
  it('round-trips passes and settings, and never doubles a pass', async () => {
    await savePass(pass('masked', 1));
    await savePass(pass('status', 2));
    const file = await exportState({ fontSize: 14 });
    const restored = await restoreBackup(new File([await file.text()], file.name));
    expect(restored).toEqual({ added: 0, total: 2, settings: { fontSize: 14 } });
    expect(await listPasses()).toHaveLength(2);

    const state = parseBackup(await file.text());
    state.passes.push(pass('guess', 3));
    expect((await restoreBackup(new File([JSON.stringify(state)], 'b.json'))).added).toBe(1);
    expect((await listPasses()).map((p) => p.unitId).sort()).toEqual(['guess', 'masked', 'status']);
  });

  it('rejects other files and drops malformed passes', () => {
    expect(() => parseBackup('nope')).toThrow(BackupError);
    expect(() => parseBackup('{"app":"reader-lite","version":1}')).toThrow('not a Code Practice backup');
    expect(() => parseBackup('{"app":"code-practice","version":9,"passes":[]}')).toThrow('newer version');
    const state = parseBackup(JSON.stringify({ app: 'code-practice', version: 1, exportedAt: 0, passes: [pass('a', 1), { unitId: 'x' }] }));
    expect(state.passes).toHaveLength(1);
  });
});
