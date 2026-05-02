// src/content/content.js — Solar Side v0.2
// Injected into every page. Shows a floating "Solar" button when text is selected.
// New in v0.2: fade-in, larger tap target, hover quick-menu (Summarize / Translate / Extract),
// loading state, smarter positioning (above selection by default; flips below if no room).

(function () {
  if (window.__SOLAR_INJECTED__) return;
  window.__SOLAR_INJECTED__ = true;

  const BTN_ID = "solar-floating-btn";
  const MENU_ID = "solar-quick-menu";
  const ICON_URL = chrome.runtime.getURL("icons/icon-32.png");
  const MIN_SELECTION_LENGTH = 3;
  const FADE_OUT_AFTER_HIDE_MS = 160;

  let button = null;
  let menu = null;
  let lastSelection = "";
  let lastRect = null;
  let menuOpen = false;
  let hideTimer = null;

  // ---------- DOM construction ----------
  function createButton() {
    const btn = document.createElement("button");
    btn.id = BTN_ID;
    btn.className = "solar-floating-btn";
    btn.type = "button";
    btn.setAttribute("aria-label", "Solar — process selection");
    btn.innerHTML = `
      <img src="${ICON_URL}" alt="" class="solar-icon" />
      <span class="solar-label">Solar</span>
      <span class="solar-caret" aria-hidden="true">▾</span>
    `;
    btn.addEventListener("mousedown", (e) => e.preventDefault()); // don't lose selection
    btn.addEventListener("click", onPrimaryClick);
    btn.addEventListener("contextmenu", onContextRequest);
    btn.addEventListener("mouseenter", scheduleMenuOpen);
    btn.addEventListener("mouseleave", scheduleMenuClose);
    document.documentElement.appendChild(btn);
    return btn;
  }

  function createMenu() {
    const m = document.createElement("div");
    m.id = MENU_ID;
    m.className = "solar-quick-menu";
    m.setAttribute("role", "menu");
    m.innerHTML = `
      <button type="button" data-action="summarize" data-language="auto" role="menuitem">
        <span class="solar-q-icon">≡</span><span class="solar-q-label">Summarize</span>
      </button>
      <button type="button" data-action="translate" data-language="ru" role="menuitem">
        <span class="solar-q-icon">⇄</span><span class="solar-q-label">Translate to RU</span>
      </button>
      <button type="button" data-action="translate" data-language="en" role="menuitem">
        <span class="solar-q-icon">⇄</span><span class="solar-q-label">Translate to EN</span>
      </button>
      <button type="button" data-action="extract" data-language="auto" role="menuitem">
        <span class="solar-q-icon">⌘</span><span class="solar-q-label">Extract entities</span>
      </button>
    `;
    m.addEventListener("mousedown", (e) => e.preventDefault());
    m.addEventListener("mouseenter", () => clearTimeout(hideTimer));
    m.addEventListener("mouseleave", scheduleMenuClose);
    m.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-action]");
      if (!b) return;
      e.preventDefault();
      e.stopPropagation();
      runAction(b.dataset.action, b.dataset.language || "auto");
    });
    document.documentElement.appendChild(m);
    return m;
  }

  function ensureUi() {
    if (!button || !document.documentElement.contains(button)) {
      button = createButton();
    }
    if (!menu || !document.documentElement.contains(menu)) {
      menu = createMenu();
    }
  }

  // ---------- Visibility ----------
  function showAt(rect) {
    ensureUi();
    const padding = 8;
    const btnHeight = 36;
    const menuHeight = 180; // approx
    const viewportH = window.innerHeight;

    // Default: above the selection
    const spaceAbove = rect.top;
    const placeAbove = spaceAbove > btnHeight + menuHeight + padding;

    let top, left;
    if (placeAbove) {
      top = window.scrollY + rect.top - btnHeight - padding;
    } else {
      top = window.scrollY + rect.bottom + padding;
    }
    left = window.scrollX + rect.left + rect.width / 2 - 50;

    // Clamp to viewport horizontally
    const maxLeft = window.scrollX + document.documentElement.clientWidth - 130;
    if (left < window.scrollX + 4) left = window.scrollX + 4;
    if (left > maxLeft) left = maxLeft;

    button.style.top = `${top}px`;
    button.style.left = `${left}px`;
    button.dataset.placement = placeAbove ? "above" : "below";

    // Position menu just below button (or above if button is below selection)
    const menuTop = placeAbove
      ? top - menuHeight - 4 // open menu above the button
      : top + btnHeight + 4;
    menu.style.top = `${Math.max(menuTop, window.scrollY + 4)}px`;
    menu.style.left = `${left}px`;

    // Fade-in next frame so the transition runs
    requestAnimationFrame(() => button.classList.add("is-visible"));
  }

  function hide() {
    if (!button) return;
    button.classList.remove("is-visible");
    closeMenu(true);
    // CSS transition runs out before we actually hide for hit-testing.
    setTimeout(() => {
      if (!button.classList.contains("is-visible")) {
        // We rely on opacity:0 + pointer-events:none from .is-loading? No — opacity:0 alone leaves clickable.
        // Move it offscreen safely:
        button.style.top = "-9999px";
        button.style.left = "-9999px";
      }
    }, FADE_OUT_AFTER_HIDE_MS);
  }

  function openMenu() {
    ensureUi();
    if (!button.classList.contains("is-visible")) return;
    menu.classList.add("is-visible");
    menuOpen = true;
  }
  function closeMenu(immediate = false) {
    if (!menu) return;
    if (immediate) {
      menu.classList.remove("is-visible");
      menuOpen = false;
      return;
    }
    menu.classList.remove("is-visible");
    menuOpen = false;
  }
  function scheduleMenuOpen() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(openMenu, 220);
  }
  function scheduleMenuClose() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => closeMenu(), 200);
  }

  function onContextRequest(ev) {
    ev.preventDefault();
    if (menuOpen) closeMenu();
    else openMenu();
  }

  // ---------- Selection tracking ----------
  function getSelectionRect() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return null;
    const text = sel.toString().trim();
    if (text.length < MIN_SELECTION_LENGTH) return null;
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return null;
    return { rect, text };
  }

  function onSelectionChanged() {
    setTimeout(() => {
      const sel = getSelectionRect();
      if (!sel) {
        hide();
        return;
      }
      lastSelection = sel.text;
      lastRect = sel.rect;
      showAt(sel.rect);
    }, 50);
  }

  // ---------- Action dispatch ----------
  function onPrimaryClick(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    if (menuOpen) {
      closeMenu();
      return;
    }
    runAction("summarize", "auto");
  }

  async function runAction(action, language) {
    if (!lastSelection) return;
    button.classList.add("is-loading");
    closeMenu(true);

    const lang = language === "auto" ? detectTargetLanguage() : language;

    chrome.runtime.sendMessage(
      {
        type: "solar.process_selection",
        payload: {
          text: lastSelection,
          url: location.href,
          action,
          language: lang,
        },
      },
      (resp) => {
        button.classList.remove("is-loading");
        if (chrome.runtime.lastError) {
          console.error("[Solar content]", chrome.runtime.lastError);
        }
        // Hide once side panel takes over
        hide();
      }
    );
  }

  function detectTargetLanguage() {
    const lang = (navigator.language || "en").split("-")[0];
    return lang || "en";
  }

  // ---------- Listeners ----------
  document.addEventListener("selectionchange", onSelectionChanged);
  document.addEventListener("mousedown", (e) => {
    if (!button) return;
    if (e.target?.id === BTN_ID || e.target?.closest?.(`#${BTN_ID}`)) return;
    if (e.target?.id === MENU_ID || e.target?.closest?.(`#${MENU_ID}`)) return;
    hide();
  });
  window.addEventListener("scroll", hide, { passive: true });
  window.addEventListener("blur", hide);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hide();
  });
})();
