// Backup: drill passes and settings as one small JSON file. Restoring adds the
// passes that aren't here yet (same unit, same time), so restoring twice, or
// onto a device with its own history, never doubles anything.

import { importPasses, listPasses, type PassRecord } from './store/db';

const BACKUP_APP = 'code-practice';
const BACKUP_VERSION = 1;

export class BackupError extends Error {}

export interface BackupState {
  app: typeof BACKUP_APP;
  version: number;
  exportedAt: number;
  settings?: unknown;
  passes: PassRecord[];
}

const today = () => new Date().toISOString().slice(0, 10);

export async function exportState(settings: unknown): Promise<File> {
  const passes = (await listPasses()).map(({ id: _, ...pass }) => pass);
  const state: BackupState = { app: BACKUP_APP, version: BACKUP_VERSION, exportedAt: Date.now(), settings, passes };
  return new File([JSON.stringify(state, null, 1)], `code-practice-${today()}.json`, { type: 'application/json' });
}

function isPass(value: unknown): value is PassRecord {
  if (typeof value !== 'object' || value === null) return false;
  const p = value as Record<string, unknown>;
  return typeof p.implId === 'string' && typeof p.unitId === 'string' && typeof p.at === 'number' &&
    typeof p.steps === 'number' && Array.isArray(p.missed) && p.missed.every((m) => typeof m === 'number') &&
    typeof p.signatureShown === 'boolean' && typeof p.sourceHash === 'string';
}

export function parseBackup(text: string): BackupState {
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    throw new BackupError('not a JSON file');
  }
  const state = raw as Partial<BackupState> | null;
  if (state?.app !== BACKUP_APP) throw new BackupError('not a Code Practice backup');
  if (typeof state.version !== 'number' || state.version > BACKUP_VERSION) throw new BackupError('made by a newer version of the app');
  if (!Array.isArray(state.passes)) throw new BackupError('no passes in the file');
  return { ...(state as BackupState), passes: state.passes.filter(isPass) };
}

export async function restoreBackup(file: File): Promise<{ added: number; total: number; settings?: unknown }> {
  const state = parseBackup(await file.text());
  return { added: await importPasses(state.passes), total: state.passes.length, settings: state.settings };
}

/**
 * Hand a file to the user: the share sheet where there is one (iPad: Save to
 * Files), else a download. False if the share sheet was closed without saving.
 */
export async function saveFile(file: File): Promise<boolean> {
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file] });
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return false; // closed the share sheet
      throw err;
    }
    return true;
  }
  const url = URL.createObjectURL(file);
  const link = document.createElement('a');
  link.href = url;
  link.download = file.name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
  return true;
}
