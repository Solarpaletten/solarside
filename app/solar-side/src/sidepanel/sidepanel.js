// src/sidepanel/sidepanel.js — Solar Side v0.2
import {
  processText,
  executeConnectorAction,
  checkHealth,
  getSettings,
  setSettings,
  ENDPOINTS,
  ApiError,
} from "../lib/api.js";
import {
  getHistory,
  addToHistory,
  clearHistory,
  removeFromHistory,
  onHistoryChange,
} from "../lib/history.js";
import { MSG } from "../lib/messages.js";

// ──────────── DOM refs ────────────
const $ = (id) => document.getElementById(id);
const els = {
  status: $("solar-status"),
  settingsBtn: $("solar-settings-btn"),
  historyBtn: $("solar-history-btn"),
  settings: $("solar-settings"),
  baseUrl: $("solar-base-url"),
  apiKey: $("solar-api-key"),
  envProd: $("solar-env-prod"),
  envLocal: $("solar-env-local"),
  saveSettings: $("solar-save-settings"),
  testConnection: $("solar-test-connection"),
  settingsMsg: $("solar-settings-msg"),

  empty: $("solar-empty"),

  loading: $("solar-loading"),
  loadingDetail: $("solar-loading-detail"),

  error: $("solar-error"),
  errorMsg: $("solar-error-msg"),
  errorHint: $("solar-error-hint"),
  errorTitle: $("solar-error-title"),
  errorRetry: $("solar-error-retry"),
  errorOpenSettings: $("solar-error-settings"),

  result: $("solar-result"),
  resultAction: $("solar-result-action"),
  resultProvider: $("solar-result-provider"),
  resultDuration: $("solar-result-duration"),
  resultBody: $("solar-result-body"),
  sourceText: $("solar-source-text"),
  sourceUrl: $("solar-source-url"),

  history: $("solar-history"),
  historyList: $("solar-history-list"),
  historyEmpty: $("solar-history-empty"),
  historyClear: $("solar-history-clear"),
};

// ──────────── State ────────────
let lastRequest = null;
let lastResponse = null;
let activeAction = "translate";
let activeLanguage = "ru";

// ──────────── View transitions ────────────
const SECTIONS = ["empty", "loading", "error", "result", "history"];
function show(section) {
  for (const k of SECTIONS) {
    els[k].classList.toggle("hidden", k !== section);
  }
  // Hide settings panel when switching primary sections
  if (section !== null) els.settings.classList.add("hidden");
  // Toggle header active state
  els.historyBtn.classList.toggle("is-active", section === "history");
}

// ──────────── Health badge ────────────
async function refreshHealth() {
  try {
    const h = await checkHealth();
    const providers = Object.entries(h.ai_providers).filter(([, v]) => v).map(([k]) => k);
    els.status.textContent = providers.length
      ? `● ${h.env} · ${providers.join(", ")}`
      : `● ${h.env} · no AI key`;
    els.status.className = `solar-status ${providers.length ? "ok" : "warn"}`;
  } catch (e) {
    els.status.textContent = "● offline";
    els.status.className = "solar-status err";
  }
}

// ──────────── Settings ────────────
function syncEnvRadio(url) {
  // Reflect the current URL in the dev/prod radio. A custom URL (neither known
  // endpoint) leaves both unchecked, which is fine — the text field still rules.
  if (url === ENDPOINTS.local) {
    els.envLocal.checked = true;
  } else if (url === ENDPOINTS.production) {
    els.envProd.checked = true;
  }
}

async function loadSettings() {
  const s = await getSettings();
  els.baseUrl.value = s.baseUrl;
  els.apiKey.value = s.apiKey;
  syncEnvRadio(s.baseUrl);
}

// Dev/Prod toggle: clicking a radio fills the URL field with that endpoint.
// The user still presses Save to persist (keeps one explicit commit point).
function onEnvChange(env) {
  els.baseUrl.value = ENDPOINTS[env] || els.baseUrl.value;
}
els.envProd.addEventListener("change", () => onEnvChange("production"));
els.envLocal.addEventListener("change", () => onEnvChange("local"));

els.settingsBtn.addEventListener("click", () => {
  els.settings.classList.toggle("hidden");
});

els.saveSettings.addEventListener("click", async () => {
  await setSettings({
    baseUrl: els.baseUrl.value.trim(),
    apiKey: els.apiKey.value.trim(),
  });
  syncEnvRadio(els.baseUrl.value.trim());
  els.settingsMsg.textContent = "Saved.";
  els.settingsMsg.className = "solar-msg ok";
  await refreshHealth();
});

els.testConnection.addEventListener("click", async () => {
  els.settingsMsg.textContent = "Checking…";
  els.settingsMsg.className = "solar-msg";
  try {
    await setSettings({
      baseUrl: els.baseUrl.value.trim(),
      apiKey: els.apiKey.value.trim(),
    });
    const h = await checkHealth();
    els.settingsMsg.textContent = `OK — Solar Core v${h.version} (${h.env})`;
    els.settingsMsg.className = "solar-msg ok";
    await refreshHealth();
  } catch (e) {
    els.settingsMsg.textContent = `Failed: ${e.message}`;
    els.settingsMsg.className = "solar-msg err";
  }
});

// ──────────── Action selector ────────────
function setActiveAction(action, language = null) {
  activeAction = action;
  if (language !== null) activeLanguage = language;
  for (const btn of document.querySelectorAll(".solar-action")) {
    const isActive = btn.dataset.action === action;
    btn.setAttribute("aria-pressed", String(isActive));
  }
}

document.querySelectorAll(".solar-action").forEach((btn) => {
  btn.addEventListener("click", () => {
    const action = btn.dataset.action;
    const language = btn.dataset.language || "auto";
    setActiveAction(action, language);
    // If a request is currently displayed, re-run with the new action
    if (lastRequest) {
      runProcess({
        ...lastRequest,
        action,
        language: language === "auto" ? lastRequest.language || "en" : language,
      });
    }
  });
});

// ──────────── Process flow ────────────
async function runProcess(req) {
  lastRequest = req;
  // Reflect BOTH action and language in the action bar so the highlighted
  // button always matches what is actually running (translate-first invariant).
  setActiveAction(req.action, req.language || null);
  els.loadingDetail.textContent = `${req.action} · ${req.text.length} chars`;
  show("loading");

  try {
    const resp = await processText(req);
    lastResponse = resp;
    renderResult(req, resp);
    // ── Save to history ──
    await addToHistory({
      document_id: resp.document_id,
      action: req.action,
      language: req.language,
      url: req.url,
      preview: extractPreview(resp.result, req.action),
      provider: resp.provider,
    });
  } catch (e) {
    renderError(e);
  }
}

function extractPreview(result, action) {
  if (action === "summarize" && result?.summary) return result.summary;
  if (action === "translate" && result?.translation) return result.translation;
  if (action === "extract" && result?.entities) {
    const counts = Object.entries(result.entities)
      .filter(([, v]) => Array.isArray(v) && v.length)
      .map(([k, v]) => `${k}: ${v.length}`)
      .join(", ");
    return counts || "no entities";
  }
  return "";
}

function renderResult(req, resp) {
  els.resultAction.textContent = resp.action;
  els.resultProvider.textContent = resp.provider ? `${resp.provider}/${resp.model}` : "—";
  els.resultDuration.textContent = resp.duration_ms ? `${resp.duration_ms} ms` : "";

  els.resultBody.innerHTML = "";
  if (req.action === "summarize" && resp.result?.summary) {
    els.resultBody.append(makePara(resp.result.summary));
  } else if (req.action === "translate" && resp.result?.translation) {
    els.resultBody.append(makePara(resp.result.translation));
  } else if (req.action === "extract" && resp.result?.entities) {
    els.resultBody.append(renderEntities(resp.result.entities));
  } else {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(resp.result, null, 2);
    els.resultBody.append(pre);
  }

  els.sourceText.textContent = (req.text || "").slice(0, 600);
  if (req.url) {
    els.sourceUrl.href = req.url;
    els.sourceUrl.textContent = req.url;
    els.sourceUrl.style.display = "";
  } else {
    els.sourceUrl.style.display = "none";
  }
  show("result");
}

function makePara(text) {
  const p = document.createElement("p");
  p.textContent = text;
  return p;
}

function renderEntities(entities) {
  const wrap = document.createElement("div");
  for (const [category, items] of Object.entries(entities)) {
    if (!Array.isArray(items) || items.length === 0) continue;
    const h = document.createElement("h5");
    h.textContent = category.replace(/_/g, " ");
    const ul = document.createElement("ul");
    for (const item of items) {
      const li = document.createElement("li");
      li.textContent = typeof item === "string" ? item : JSON.stringify(item);
      ul.append(li);
    }
    wrap.append(h, ul);
  }
  if (wrap.children.length === 0) {
    wrap.textContent = "No entities extracted.";
  }
  return wrap;
}

// ──────────── Error rendering ────────────
function renderError(e) {
  let title = "Something went wrong";
  let hint = "";
  let msg = "";

  if (e instanceof ApiError) {
    if (e.status === 0) {
      // Network failure → Core unreachable
      title = "Solar Core not available";
      msg = e.message;
      hint = "Make sure Solar Core is running:\n  uvicorn solar_core.main:app --reload";
    } else if (e.status === 401) {
      title = "Authentication failed";
      msg = e.message;
      hint = "Check your API key in Settings (must match SOLAR_API_KEYS in Core).";
    } else if (e.status === 502) {
      title = "AI provider error";
      msg = e.message;
      hint = "Check ANTHROPIC_API_KEY (or other provider) in Core's .env.";
    } else if (e.status >= 500) {
      title = "Solar Core error";
      msg = e.message;
      hint = "Check the Core terminal for details.";
    } else {
      title = "Request rejected";
      msg = `${e.message} (HTTP ${e.status})`;
    }
  } else {
    msg = String(e?.message || e);
  }

  els.errorTitle.textContent = title;
  els.errorMsg.textContent = msg;
  els.errorHint.textContent = hint;
  els.errorHint.classList.toggle("hidden", !hint);
  show("error");
}

els.errorRetry.addEventListener("click", () => {
  if (lastRequest) runProcess(lastRequest);
});
els.errorOpenSettings.addEventListener("click", () => {
  show("empty");
  els.settings.classList.remove("hidden");
});

// ──────────── Quick actions / connector actions in result ────────────
document.addEventListener("click", async (e) => {
  const quick = e.target.closest("[data-quick-action]");
  if (quick) {
    const action = quick.dataset.quickAction;
    if (action === "copy" && lastResponse) {
      const txt =
        lastResponse.result?.summary ||
        lastResponse.result?.translation ||
        JSON.stringify(lastResponse.result, null, 2);
      await navigator.clipboard.writeText(txt);
      flashButton(quick, "Copied!");
    }
    return;
  }

  const connector = e.target.closest("[data-connector-action]");
  if (connector) {
    const [name, action] = connector.dataset.connectorAction.split(".");
    const docId = lastResponse?.document_id;
    if (!docId) return;
    flashButton(connector, "Sending…");
    try {
      const result = await executeConnectorAction({
        connector: name,
        action,
        documentId: docId,
        payload: buildConnectorPayload(name, action),
      });
      flashButton(
        connector,
        result.success ? "Sent ✓" : "Failed",
        result.success ? "ok" : "err"
      );
    } catch (err) {
      flashButton(connector, "Failed", "err");
      console.error("[Solar sidepanel]", err);
    }
  }
});

function buildConnectorPayload(connector, action) {
  // Helper: extract human-readable text from current result
  const resultText = () =>
    lastResponse?.result?.summary ||
    lastResponse?.result?.translation ||
    (lastResponse?.result ? JSON.stringify(lastResponse.result, null, 2) : "");

  if (connector === "solar_erp" && action === "create_note") {
    return {
      entity: "Solar",
      title: lastRequest?.url || "Web note",
      body: resultText(),
      tags: ["solar-side", lastRequest?.action].filter(Boolean),
    };
  }

  if (connector === "telegram" && action === "send_message") {
    // chat_id omitted on purpose — backend uses TELEGRAM_DEFAULT_CHAT_ID
    return {
      text: resultText(),
    };
  }

  return {};
}

function flashButton(btn, text, state = "ok") {
  const original = btn.textContent;
  btn.textContent = text;
  btn.classList.add(state === "ok" ? "is-ok" : "is-err");
  setTimeout(() => {
    btn.textContent = original;
    btn.classList.remove("is-ok", "is-err");
  }, 1600);
}

// ──────────── History ────────────
els.historyBtn.addEventListener("click", async () => {
  if (!els.history.classList.contains("hidden")) {
    show(lastResponse ? "result" : "empty");
    return;
  }
  await renderHistory();
  show("history");
});

els.historyClear.addEventListener("click", async () => {
  await clearHistory();
  await renderHistory();
});

els.historyList.addEventListener("click", async (e) => {
  const remove = e.target.closest("[data-history-remove]");
  if (remove) {
    e.stopPropagation();
    await removeFromHistory(remove.dataset.historyRemove);
    await renderHistory();
    return;
  }
  const item = e.target.closest(".solar-history-item");
  if (item && item.dataset.docId) {
    await replayFromHistory(item.dataset.docId);
  }
});

async function renderHistory() {
  const list = await getHistory();
  els.historyList.innerHTML = "";
  els.historyEmpty.classList.toggle("hidden", list.length > 0);
  for (const entry of list) {
    const li = document.createElement("li");
    li.className = "solar-history-item";
    li.dataset.docId = entry.document_id;
    li.innerHTML = `
      <div class="solar-history-item-header">
        <span class="solar-history-item-action">${escapeHtml(entry.action || "")}</span>
        <span class="solar-history-item-lang">${escapeHtml(entry.language || "")}</span>
        <span class="solar-history-item-time">${formatTime(entry.savedAt)}</span>
        <button class="solar-link" data-history-remove="${escapeHtml(entry.document_id)}" title="Remove">✕</button>
      </div>
      <div class="solar-history-item-text">${escapeHtml(entry.preview || "(no preview)")}</div>
    `;
    els.historyList.append(li);
  }
}

async function replayFromHistory(documentId) {
  // Re-fetch the document from Core to show full result
  try {
    const { getDocument } = await import("../lib/api.js");
    const doc = await getDocument(documentId);
    const lastAction = doc.actions?.[0];
    lastRequest = {
      text: doc.selected_text || "",
      url: doc.source_url || null,
      action: lastAction?.type || "summarize",
      language: doc.language || "en",
    };
    lastResponse = {
      document_id: doc.id,
      action: lastAction?.type || "summarize",
      result: lastAction?.result || doc.ai_result || {},
      provider: lastAction?.provider,
      model: lastAction?.model,
      duration_ms: lastAction?.duration_ms,
      saved: true,
    };
    renderResult(lastRequest, lastResponse);
  } catch (e) {
    renderError(e);
  }
}

function formatTime(ts) {
  if (!ts) return "";
  const diff = Date.now() - ts;
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return new Date(ts).toLocaleDateString();
}

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

// React to history changes (e.g. another tab cleared it)
onHistoryChange(async () => {
  if (!els.history.classList.contains("hidden")) {
    await renderHistory();
  }
});

// ──────────── Pick up pending request from session storage ────────────
async function checkPending() {
  const { solar_pending } = await chrome.storage.session.get("solar_pending");
  if (solar_pending && Date.now() - solar_pending.requestedAt < 30_000) {
    await chrome.storage.session.remove("solar_pending");
    runProcess({
      text: solar_pending.text,
      url: solar_pending.url,
      action: solar_pending.action,
      language: solar_pending.language,
    });
  }
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === MSG.OPEN_SIDEPANEL && msg.payload) {
    // Defensive: only run if we haven't already handled this exact request
    // via checkPending (avoids double-run and stale-action flashes).
    if (!lastRequest || lastRequest.text !== msg.payload.text) {
      runProcess(msg.payload);
    }
  }
});

// ──────────── Boot ────────────
(async function init() {
  await loadSettings();
  await refreshHealth();
  // Translate-first invariant: the action bar shows Translate active on open,
  // before any pending request is processed.
  setActiveAction("translate", "ru");
  await checkPending();
})();
