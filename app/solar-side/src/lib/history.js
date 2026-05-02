// src/lib/history.js — Solar Side v0.2
// Last-N processed results, persisted in chrome.storage.local.
// Async API; small, simple.

const KEY = "solar_history_v1";
const MAX_ITEMS = 10;

export async function getHistory() {
  const data = await chrome.storage.local.get(KEY);
  return Array.isArray(data[KEY]) ? data[KEY] : [];
}

export async function addToHistory(entry) {
  const list = await getHistory();
  // Dedup: drop any prior entry with the same document_id
  const filtered = entry?.document_id
    ? list.filter((e) => e.document_id !== entry.document_id)
    : list;
  const next = [
    {
      ...entry,
      savedAt: Date.now(),
    },
    ...filtered,
  ].slice(0, MAX_ITEMS);
  await chrome.storage.local.set({ [KEY]: next });
  return next;
}

export async function clearHistory() {
  await chrome.storage.local.remove(KEY);
  return [];
}

export async function removeFromHistory(documentId) {
  const list = await getHistory();
  const next = list.filter((e) => e.document_id !== documentId);
  await chrome.storage.local.set({ [KEY]: next });
  return next;
}

/**
 * Subscribe to history changes (across the extension).
 * @param {(history: any[]) => void} cb
 * @returns unsubscribe function
 */
export function onHistoryChange(cb) {
  const listener = (changes, area) => {
    if (area === "local" && changes[KEY]) {
      cb(changes[KEY].newValue || []);
    }
  };
  chrome.storage.onChanged.addListener(listener);
  return () => chrome.storage.onChanged.removeListener(listener);
}
