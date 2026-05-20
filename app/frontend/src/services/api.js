/**
 * DeepFind — API Service Layer
 *
 * Central module for all HTTP calls to the Python FastAPI backend.
 * All fetch calls go through this file — never call fetch directly from components.
 *
 * Step 4: Health check only.
 * Future steps will add: search(), indexFolder(), getFileDetail(), getSettings()...
 */

const BASE_URL = 'http://127.0.0.1:8765';

/** Milliseconds before a fetch request times out */
const TIMEOUT_MS = 5000;

/**
 * Wraps fetch with a timeout using AbortController.
 * Throws if the request takes longer than TIMEOUT_MS.
 */
async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timeoutId);
    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}

/**
 * GET /health
 *
 * Checks if the DeepFind engine is running.
 *
 * Returns:
 *   { status, service, version, backend, timestamp }
 *
 * Throws:
 *   Error if the backend is unreachable or returns a non-OK response.
 */
export async function checkHealth() {
  const response = await fetchWithTimeout(`${BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Engine returned HTTP ${response.status}`);
  }

  return response.json();
}

// ── Folder Management (Step 6) ─────────────────────────────────────────────────

/**
 * GET /folders/discover
 * Detects common user folders and drives (no DB writes).
 */
export async function discoverFolders() {
  const response = await fetchWithTimeout(`${BASE_URL}/folders/discover`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * POST /folders/initialize-defaults
 * Saves all detected folders/drives to the DB with their default active states.
 */
export async function initializeDefaults() {
  const response = await fetchWithTimeout(`${BASE_URL}/folders/initialize-defaults`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * GET /folders
 * Returns ALL folders (active and inactive) for the UI.
 */
export async function getAllFolders() {
  const response = await fetchWithTimeout(`${BASE_URL}/folders`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * POST /folders
 * Manually add a folder (from Electron dialog).
 */
export async function addFolder(folderPath, sourceType = 'manual') {
  const response = await fetchWithTimeout(`${BASE_URL}/folders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_path: folderPath, source_type: sourceType }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * PATCH /folders/{id}/toggle
 * Flip a folder's is_active state.
 */
export async function toggleFolder(folderId) {
  const response = await fetchWithTimeout(`${BASE_URL}/folders/${folderId}/toggle`, {
    method: 'PATCH',
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/**
 * DELETE /folders/{id}
 * Soft-deletes a folder (sets is_active=0).
 */
export async function removeFolder(folderId) {
  const response = await fetchWithTimeout(`${BASE_URL}/folders/${folderId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// ── Indexing (Step 7) ──────────────────────────────────────────────────────────

/** POST /index/start — start background scan */
export async function startIndexing() {
  const response = await fetchWithTimeout(`${BASE_URL}/index/start`, { method: 'POST' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** GET /index/status — live progress (poll while active=true) */
export async function getIndexStatus() {
  const response = await fetchWithTimeout(`${BASE_URL}/index/status`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** GET /index/summary — total files in DB by status */
export async function getIndexSummary() {
  const response = await fetchWithTimeout(`${BASE_URL}/index/summary`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// ── Search (Step 8) ────────────────────────────────────────────────────────────

/**
 * GET /search?q=&type=&limit=&offset=
 * Searches indexed file metadata and/or extracted content.
 * type: 'all' | 'metadata' | 'content'
 */
const searchCache = new Map();

export async function searchFiles(query, { limit = 50, offset = 0, searchType = 'all' } = {}) {
  const cacheKey = `${query}|${searchType}|${limit}|${offset}`;
  
  if (searchCache.has(cacheKey)) {
    const cached = searchCache.get(cacheKey);
    if (Date.now() - cached.timestamp < 30000) {
      return cached.data;
    }
  }

  // Passing debug=true to get timing metrics (Step 12.5)
  const params = new URLSearchParams({ q: query, type: searchType, limit, offset, debug: 'true' });
  const response = await fetchWithTimeout(`${BASE_URL}/search?${params}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();

  searchCache.set(cacheKey, { data, timestamp: Date.now() });
  if (searchCache.size > 20) {
    searchCache.delete(searchCache.keys().next().value);
  }

  return data;
}

// ── Extraction (Step 9) ────────────────────────────────────────────────────────

/** POST /extract/start — start background text extraction */
export async function startExtraction() {
  const response = await fetchWithTimeout(`${BASE_URL}/extract/start`, { method: 'POST' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** GET /extract/status — live extraction progress */
export async function getExtractStatus() {
  const response = await fetchWithTimeout(`${BASE_URL}/extract/status`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** GET /extract/summary — totals from the database */
export async function getExtractSummary() {
  const response = await fetchWithTimeout(`${BASE_URL}/extract/summary`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// ── Auto-Tagging (Step 11) ──────────────────────────────────────────────────

/** POST /tags/generate?force= */
export async function startTagging(force = false) {
  const url = `${BASE_URL}/tags/generate${force ? '?force=true' : ''}`;
  const response = await fetchWithTimeout(url, { method: 'POST' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** GET /tags/status */
export async function getTagStatus() {
  const response = await fetchWithTimeout(`${BASE_URL}/tags/status`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** GET /tags/summary */
export async function getTagSummary() {
  const response = await fetchWithTimeout(`${BASE_URL}/tags/summary`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// ── Dashboard & History (Step 12) ───────────────────────────────────────────

export async function getSearchHistory(limit = 10) {
  const response = await fetchWithTimeout(`${BASE_URL}/history/searches?limit=${limit}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function clearSearchHistory() {
  const response = await fetchWithTimeout(`${BASE_URL}/history/searches`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function getRecentModifiedFiles(limit = 10) {
  const response = await fetchWithTimeout(`${BASE_URL}/files/recent?limit=${limit}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function getRecentIndexedFiles(limit = 10) {
  const response = await fetchWithTimeout(`${BASE_URL}/files/recent-indexed?limit=${limit}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function getDashboardSummary() {
  const response = await fetchWithTimeout(`${BASE_URL}/dashboard/summary`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// Future API functions:
// export async function getFileDetail(fileId) { ... }
// export async function getSettings() { ... }
