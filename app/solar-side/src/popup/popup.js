// src/popup/popup.js
import { checkHealth } from "../lib/api.js";

const status = document.getElementById("status");

(async () => {
  try {
    const h = await checkHealth();
    const providers = Object.entries(h.ai_providers).filter(([, v]) => v).map(([k]) => k);
    status.textContent = providers.length
      ? `Core ok · ${providers.join(", ")}`
      : "Core ok · no AI key configured";
    status.className = "status ok";
  } catch (e) {
    status.textContent = `Core unreachable: ${e.message}`;
    status.className = "status err";
  }
})();

document.getElementById("open-side-panel").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    await chrome.sidePanel.open({ tabId: tab.id });
    window.close();
  }
});

document.getElementById("open-options").addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});
