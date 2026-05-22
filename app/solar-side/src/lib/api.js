// src/lib/api.js
// Solar Core API client. Shared between background, sidepanel, popup, content.
// Uses fetch — works in Manifest V3 service workers.

// Named endpoints for the dev/prod toggle (4C.9b). A fresh install defaults to
// PRODUCTION so the extension works out of the box without a local backend.
// Switch to LOCAL in settings only when running Docker on your own machine.
export const ENDPOINTS = {
  production: "https://solar-core-rrp5.onrender.com",
  local: "http://localhost:8000",
};

const DEFAULT_BASE = ENDPOINTS.production;
const DEFAULT_KEY = "";  // no baked-in key; the prod key is entered in settings

export async function getSettings() {
  const stored = await chrome.storage.sync.get(["solar_base_url", "solar_api_key"]);
  return {
    baseUrl: stored.solar_base_url || DEFAULT_BASE,
    apiKey: stored.solar_api_key || DEFAULT_KEY,
  };
}

export async function setSettings({ baseUrl, apiKey }) {
  const update = {};
  if (baseUrl !== undefined) update.solar_base_url = baseUrl;
  if (apiKey !== undefined) update.solar_api_key = apiKey;
  await chrome.storage.sync.set(update);
}

async function request(path, { method = "GET", body, signal } = {}) {
  const { baseUrl, apiKey } = await getSettings();
  const url = baseUrl.replace(/\/+$/, "") + path;
  const headers = {
    "Content-Type": "application/json",
    "X-API-Key": apiKey,
  };

  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (e) {
    throw new ApiError(
      `Cannot reach Solar Core at ${baseUrl}. Is the server running?`,
      0,
      { cause: e }
    );
  }

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    const message = data?.message || data?.detail?.message || data?.detail || `HTTP ${response.status}`;
    throw new ApiError(message, response.status, data);
  }
  return data;
}

export class ApiError extends Error {
  constructor(message, status = 0, body = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// ---------- High-level helpers ----------

export async function processText({ text, url, action, language = "en", vertical }) {
  return request("/v1/process", {
    method: "POST",
    body: { text, url, action, language, vertical },
  });
}

export async function translateAir({ text, targetLanguage = "auto", signal }) {
  // Fast lane for short selections (<1000 chars). Goes to Haiku, no DB write.
  // targetLanguage="auto" lets backend pick: RU→EN, otherwise→RU.
  return request("/v1/translate-air", {
    method: "POST",
    body: { text, target_language: targetLanguage },
    signal,
  });
}

export async function listDocuments({ limit = 20, offset = 0 } = {}) {
  return request(`/v1/documents?limit=${limit}&offset=${offset}`);
}

export async function getDocument(id) {
  return request(`/v1/documents/${encodeURIComponent(id)}`);
}

export async function listConnectors() {
  return request("/v1/connectors");
}

export async function executeConnectorAction({ connector, action, payload, documentId }) {
  return request("/v1/action", {
    method: "POST",
    body: {
      connector,
      action,
      payload,
      document_id: documentId,
    },
  });
}

export async function checkHealth() {
  return request("/v1/health");
}
