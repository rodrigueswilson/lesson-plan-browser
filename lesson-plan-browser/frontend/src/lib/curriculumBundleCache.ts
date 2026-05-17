/**
 * Persistent IndexedDB cache for curriculum lesson bundles (stale-while-revalidate).
 * LRU eviction when exceeding MAX_ENTRIES.
 */

const DB_NAME = 'lp_curriculum_bundle';
const DB_VERSION = 2;
const STORE_BUNDLES = 'bundles';
const STORE_META = 'meta';
const META_ORDER_KEY = 'lru_order';
const MAX_ENTRIES = 80;

export type DiskBundlePayload = {
  lesson: unknown;
  vocabulary: unknown[];
  standards: unknown[];
  /** Science day segments from bundle API (optional for caches written before this field existed). */
  science_day_segments?: unknown[];
  /** Grade 2 Science student workbook PDF pages when bundle was fetched with include_book_extracts. */
  book_page_extracts?: unknown[];
  etag: string;
  contentHash: string;
  storedAt: number;
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onerror = () => reject(req.error ?? new Error('IndexedDB open failed'));
    req.onsuccess = () => resolve(req.result);
    req.onupgradeneeded = (ev) => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_BUNDLES)) {
        db.createObjectStore(STORE_BUNDLES);
      }
      if (!db.objectStoreNames.contains(STORE_META)) {
        db.createObjectStore(STORE_META);
      }
      if (ev.oldVersion < 2) {
        /* v2: optional book_page_extracts on bundle entries; no store shape change */
      }
    };
  });
}

function txDone(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('IndexedDB transaction failed'));
    tx.onabort = () => reject(tx.error ?? new Error('IndexedDB transaction aborted'));
  });
}

async function readOrder(db: IDBDatabase): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_META, 'readonly');
    const req = tx.objectStore(STORE_META).get(META_ORDER_KEY);
    req.onsuccess = () => {
      const v = req.result;
      resolve(Array.isArray(v) ? (v as string[]) : []);
    };
    req.onerror = () => reject(req.error ?? new Error('readOrder failed'));
  });
}

export async function getCachedBundle(lessonId: string): Promise<DiskBundlePayload | null> {
  if (typeof indexedDB === 'undefined') return null;
  try {
    const db = await openDb();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_BUNDLES, 'readonly');
      const req = tx.objectStore(STORE_BUNDLES).get(lessonId);
      req.onsuccess = () => {
        const raw = req.result as DiskBundlePayload | undefined;
        resolve(raw ?? null);
      };
      req.onerror = () => reject(req.error ?? new Error('get bundle failed'));
    });
  } catch {
    return null;
  }
}

export async function setCachedBundle(
  lessonId: string,
  payload: Omit<DiskBundlePayload, 'storedAt'>,
): Promise<void> {
  if (typeof indexedDB === 'undefined') return;
  try {
    const db = await openDb();
    const entry: DiskBundlePayload = { ...payload, storedAt: Date.now() };
    let order = await readOrder(db);
    order = order.filter((id) => id !== lessonId);
    while (order.length >= MAX_ENTRIES) {
      const victim = order.shift();
      if (victim) {
        const tx0 = db.transaction(STORE_BUNDLES, 'readwrite');
        tx0.objectStore(STORE_BUNDLES).delete(victim);
        await txDone(tx0);
      }
    }
    order.push(lessonId);
    const tx = db.transaction([STORE_BUNDLES, STORE_META], 'readwrite');
    tx.objectStore(STORE_BUNDLES).put(entry, lessonId);
    tx.objectStore(STORE_META).put(order, META_ORDER_KEY);
    await txDone(tx);
  } catch {
    /* best-effort */
  }
}

export function saveDataPreferred(): boolean {
  try {
    const c = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
    return Boolean(c?.saveData);
  } catch {
    return false;
  }
}
