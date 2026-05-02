import { getSettings, setSettings, checkHealth } from "../lib/api.js";

const el = (id) => document.getElementById(id);
const msg = el("msg");

(async () => {
  const s = await getSettings();
  el("base-url").value = s.baseUrl;
  el("api-key").value = s.apiKey;
})();

el("save").addEventListener("click", async () => {
  await setSettings({
    baseUrl: el("base-url").value.trim(),
    apiKey: el("api-key").value.trim(),
  });
  msg.textContent = "Saved.";
  msg.className = "msg ok";
});

el("test").addEventListener("click", async () => {
  msg.textContent = "Checking…";
  msg.className = "msg";
  try {
    await setSettings({
      baseUrl: el("base-url").value.trim(),
      apiKey: el("api-key").value.trim(),
    });
    const h = await checkHealth();
    msg.textContent = `OK — Solar Core v${h.version}`;
    msg.className = "msg ok";
  } catch (e) {
    msg.textContent = `Failed: ${e.message}`;
    msg.className = "msg err";
  }
});