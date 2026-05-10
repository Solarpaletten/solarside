// src/background/service_worker.js
// Background service worker (Manifest V3).
// Owns: context menu, sidepanel, message routing, Core calls.

import { processText, executeConnectorAction, checkHealth, translateAir, ApiError } from "../lib/api.js";
import { MSG } from "../lib/messages.js";

// ---------- Install / startup ----------

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "solar-summarize",
    title: "Solar — Summarize",
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "solar-extract",
    title: "Solar — Extract entities",
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "solar-translate-ru",
    title: "Solar — Translate to Russian",
    contexts: ["selection"],
  });

  // Open side panel when toolbar icon is clicked
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((e) => console.warn("[Solar] sidePanel.setPanelBehavior:", e));
});

// ---------- Context menu ----------

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!info.selectionText || !tab?.id) return;

  let action = "summarize";
  let language = "en";
  if (info.menuItemId === "solar-extract") action = "extract";
  if (info.menuItemId === "solar-translate-ru") {
    action = "translate";
    language = "ru";
  }

  await openSidePanelAndProcess(tab, {
    text: info.selectionText,
    url: info.pageUrl || tab.url,
    action,
    language,
  });
});

// ---------- Messages from content / sidepanel ----------

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // Use IIFE because onMessage doesn't natively await async handlers.
  (async () => {
    try {
      if (msg.type === MSG.PROCESS_SELECTION) {
        // Content script asked to run an action on selected text
        const tab = sender.tab;
        if (!tab?.id) {
          sendResponse({ ok: false, error: "No active tab" });
          return;
        }
        await openSidePanelAndProcess(tab, msg.payload);
        sendResponse({ ok: true });
      } else if (msg.type === MSG.TRANSLATE_AIR) {
        // Air translator: short-selection inline translation, no sidepanel.
        console.log("[Solar bg] TRANSLATE_AIR payload:", msg.payload);
        const result = await translateAir(msg.payload);
        console.log("[Solar bg] TRANSLATE_AIR result:", {
          translation: result?.translation?.slice(0, 60),
          model: result?.model,
          duration_ms: result?.duration_ms,
        });
        sendResponse({ ok: true, data: result });
      } else if (msg.type === MSG.EXECUTE_ACTION) {
        const result = await executeConnectorAction(msg.payload);
        sendResponse({ ok: true, data: result });
      } else if (msg.type === MSG.HEALTH_CHECK) {
        const result = await checkHealth();
        sendResponse({ ok: true, data: result });
      } else {
        sendResponse({ ok: false, error: "Unknown message type" });
      }
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError(String(e?.message || e));
      console.error("[Solar bg]", err);
      sendResponse({ ok: false, error: err.message, status: err.status });
    }
  })();
  return true; // keep the message channel open for async response
});

// ---------- Helpers ----------

async function openSidePanelAndProcess(tab, payload) {
  // 1. Open the side panel (must happen in response to a user gesture; menu click counts)
  try {
    await chrome.sidePanel.open({ tabId: tab.id });
  } catch (e) {
    console.warn("[Solar] sidePanel.open failed:", e);
  }

  // 2. Stash the pending request — sidepanel reads it on load
  await chrome.storage.session.set({
    solar_pending: {
      ...payload,
      requestedAt: Date.now(),
      tabId: tab.id,
    },
  });

  // 3. Notify any open sidepanel instances directly
  try {
    chrome.runtime.sendMessage({ type: MSG.OPEN_SIDEPANEL, payload });
  } catch {
    // sidepanel may not be open yet — it'll pick up from storage
  }
}

// Expose processText for sidepanel (sidepanel imports api.js directly,
// but in case we want background to centralise calls in the future).
self.solarBackground = { processText };
