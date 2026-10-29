// IndexedDB storage, on the device: settings (and the resume state kept with
// them) and one record per finished drill pass.

const DB_NAME = 'code-practice';
const DB_VERSION = 2;

type StoreName = 'settings' | 'passes';

/** One finished pass over a unit: every step revealed, the misses flagged. */
export interface PassRecord {
  id?: number;
  implId: string;
  unitId: string;
  /** When the pass was finished (first fully revealed). */
  at: number;
  /** Steps recalled: the unit's steps minus any given by the signature toggle. */
  steps: number;
  missed: number[];
  signatureShown: boolean;
  /** The unit's hash then; a different hash now makes the pass stale. */
  sourceHash: string;
}

let dbPromise: Promise<IDBDatabase> | null = null;

function openDb(): Promise<IDBDatabase> {
  dbPromise ??= new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = request.result;
      if (event.oldVersion < 1) db.createObjectStore('settings');
      if (event.oldVersion < 2) {
        const passes = db.createObjectStore('passes', { keyPath: 'id', autoIncrement: true });
        passes.createIndex('implId', 'implId');
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  return dbPromise;
}

function promisify<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function transaction<T>(
  stores: StoreName[],
  mode: IDBTransactionMode,
  work: (tx: IDBTransaction) => Promise<T> | T,
): Promise<T> {
  const db = await openDb();
  const tx = db.transaction(stores, mode);
  const done = new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error ?? new Error('transaction aborted'));
  });
  const result = await work(tx);
  await done;
  return result;
}

export function getSetting<T>(key: string): Promise<T | undefined> {
  return transaction(['settings'], 'readonly', (tx) =>
    promisify(tx.objectStore('settings').get(key) as IDBRequest<T | undefined>),
  );
}

export function putSetting<T>(key: string, value: T): Promise<void> {
  return transaction(['settings'], 'readwrite', (tx) => {
    tx.objectStore('settings').put(value, key);
  });
}

/** Store a pass: a new one without `id`, or an update of an earlier one. Returns its id. */
export function savePass(pass: PassRecord): Promise<number> {
  return transaction(['passes'], 'readwrite', (tx) =>
    promisify(tx.objectStore('passes').put(pass) as IDBRequest<number>),
  );
}

/** Every pass, or one impl's. */
export function listPasses(implId?: string): Promise<PassRecord[]> {
  return transaction(['passes'], 'readonly', (tx) => {
    const store = tx.objectStore('passes');
    const request = implId === undefined ? store.getAll() : store.index('implId').getAll(implId);
    return promisify(request as IDBRequest<PassRecord[]>);
  });
}

/** Add passes from a backup, skipping any already here (same unit, same time). Returns how many were added. */
export function importPasses(passes: PassRecord[]): Promise<number> {
  return transaction(['passes'], 'readwrite', async (tx) => {
    const store = tx.objectStore('passes');
    const existing = await promisify(store.getAll() as IDBRequest<PassRecord[]>);
    const seen = new Set(existing.map(passKey));
    let added = 0;
    for (const pass of passes) {
      if (seen.has(passKey(pass))) continue;
      const { id: _, ...record } = pass;
      store.add(record);
      seen.add(passKey(pass));
      added += 1;
    }
    return added;
  });
}

const passKey = (pass: PassRecord) => `${pass.implId}\u0000${pass.unitId}\u0000${pass.at}`;
