// src/lib/messages.js
// Message types used across content / background / sidepanel / popup.

export const MSG = {
  // From content → background → sidepanel
  PROCESS_SELECTION: "solar.process_selection",
  // From content → background (Air translator, no sidepanel)
  TRANSLATE_AIR: "solar.translate_air",
  // From sidepanel → background (connector action)
  EXECUTE_ACTION: "solar.execute_action",
  // From background → sidepanel (open with payload)
  OPEN_SIDEPANEL: "solar.open_sidepanel",
  // From sidepanel/popup → background to ping core
  HEALTH_CHECK: "solar.health_check",
};
