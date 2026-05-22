// src/content/content.js — Solar Side v0.3 (Phase 1.6 — Air Translator)
// Injected into every page. Shows a floating "Solar" button when text is selected.
//
// v0.2: fade-in, larger tap target, hover quick-menu (Summarize / Translate / Extract),
//       loading state, smarter positioning.
// v0.3: Air Translator — hover the Solar button on a SHORT selection (<120 chars)
//       and an inline bubble appears with the instant translation, powered by Haiku.
//       For longer selections, the existing hover quick-menu still opens.
//
// IMPORTANT: content scripts in MV3 cannot use ES modules directly.
// All API calls go through chrome.runtime.sendMessage → background service worker.

(function () {
  if (window.__SOLAR_INJECTED__) return;
  window.__SOLAR_INJECTED__ = true;

  const BTN_ID = "solar-floating-btn";
  const MENU_ID = "solar-quick-menu";
  const BUBBLE_ID = "solar-air-bubble";
  const ICON_URL = chrome.runtime.getURL("icons/icon-32.png");
  const MIN_SELECTION_LENGTH = 3;
  const FADE_OUT_AFTER_HIDE_MS = 160;

  // Air mode trigger: only for short selections (single word / phrase / UI text).
  // Longer selections fall through to the original hover quick-menu.
  const AIR_MAX_LENGTH = 120;
  const AIR_HOVER_DELAY_MS = 220;       // wait before triggering Air on hover
  const AIR_AUTO_HIDE_MS = 6000;        // bubble auto-hides if user moves away
  const AIR_DEBOUNCE_MS = 200;          // ignore rapid hover-in/out

  let button = null;
  let menu = null;
  let bubble = null;

  let lastSelection = "";
  let lastRect = null;
  let menuOpen = false;
  let hideTimer = null;

  // Air state
  let airHoverTimer = null;
  let airAutoHideTimer = null;
  let airActiveForSelection = null;     // string — selection that bubble currently shows
  let airIsLoading = false;

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
    btn.addEventListener("mouseenter", onButtonMouseEnter);
    btn.addEventListener("mouseleave", onButtonMouseLeave);
    document.documentElement.appendChild(btn);
    return btn;
  }

  function createMenu() {
    const m = document.createElement("div");
    m.id = MENU_ID;
    m.className = "solar-quick-menu";
    m.setAttribute("role", "menu");
    m.innerHTML = `
      <button type="button" data-action="translate" data-language="ru" role="menuitem">
        <span class="solar-q-icon">⇄</span><span class="solar-q-label">Translate to RU</span>
      </button>
      <button type="button" data-action="translate" data-language="en" role="menuitem">
        <span class="solar-q-icon">⇄</span><span class="solar-q-label">Translate to EN</span>
      </button>
      <button type="button" data-action="summarize" data-language="auto" role="menuitem">
        <span class="solar-q-icon">≡</span><span class="solar-q-label">Summarize</span>
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

  function createBubble() {
    const b = document.createElement("div");
    b.id = BUBBLE_ID;
    b.className = "solar-air-bubble";
    b.setAttribute("role", "tooltip");
    b.innerHTML = `
      <div class="solar-air-loading" data-state="loading">
        <span class="solar-air-spinner"></span>
        <span class="solar-air-loading-label">Translating…</span>
      </div>
      <div class="solar-air-content" data-state="ready" hidden>
        <div class="solar-air-translation"></div>
        <div class="solar-air-meta">
          <span class="solar-air-model"></span>
          <span class="solar-air-duration"></span>
          <button type="button" class="solar-air-expand" aria-label="Open in Solar">
            ↗ Open in Solar
          </button>
        </div>
      </div>
      <div class="solar-air-error" data-state="error" hidden>
        <span class="solar-air-error-text"></span>
      </div>
    `;
    b.addEventListener("mousedown", (e) => e.preventDefault());
    b.addEventListener("mouseenter", () => {
      clearTimeout(airAutoHideTimer);
      clearTimeout(hideTimer);
    });
    b.addEventListener("mouseleave", () => {
      scheduleMenuClose();
      scheduleAirAutoHide();
    });
    b.addEventListener("click", (e) => {
      const expand = e.target.closest(".solar-air-expand");
      if (expand) {
        e.preventDefault();
        e.stopPropagation();
        runAction("translate", "ru");  // open Workspace with same selection, full pipeline
      }
    });
    document.documentElement.appendChild(b);
    return b;
  }

  function ensureUi() {
    if (!button || !document.documentElement.contains(button)) {
      button = createButton();
    }
    if (!menu || !document.documentElement.contains(menu)) {
      menu = createMenu();
    }
    if (!bubble || !document.documentElement.contains(bubble)) {
      bubble = createBubble();
    }
  }

  // ---------- Visibility ----------
  function showAt(rect) {
    ensureUi();
    const padding = 8;
    const btnHeight = 36;
    const menuHeight = 180; // approx

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
      ? top - menuHeight - 4
      : top + btnHeight + 4;
    menu.style.top = `${Math.max(menuTop, window.scrollY + 4)}px`;
    menu.style.left = `${left}px`;

    // Bubble follows the same column as button.
    // It's positioned immediately to the right of the button when there's space,
    // otherwise below the button.
    positionBubbleNear(top, left, btnHeight, placeAbove);

    requestAnimationFrame(() => button.classList.add("is-visible"));
  }

  function positionBubbleNear(btnTop, btnLeft, btnHeight, placeAbove) {
    const viewportW = document.documentElement.clientWidth;
    const bubbleWidth = 280; // matches CSS max-width
    const padding = 8;

    // Try right of button
    let bubbleLeft = btnLeft + 110 + padding; // ~width of pill button
    let bubbleTop = btnTop;

    // If overflows right, place below the button instead
    if (bubbleLeft + bubbleWidth > window.scrollX + viewportW - padding) {
      bubbleLeft = btnLeft;
      bubbleTop = placeAbove ? btnTop - 8 - 80 : btnTop + btnHeight + padding;
    }

    bubble.style.top = `${bubbleTop}px`;
    bubble.style.left = `${bubbleLeft}px`;
  }

  function hide() {
    if (!button) return;
    button.classList.remove("is-visible");
    closeMenu(true);
    closeBubble(true);
    setTimeout(() => {
      if (!button.classList.contains("is-visible")) {
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
    menu.classList.remove("is-visible");
    menuOpen = false;
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

  // ---------- Air bubble ----------
  function isShortSelection(text) {
    return text && text.length > 0 && text.length <= AIR_MAX_LENGTH;
  }

  function detectTargetLanguage() {
    const lang = (navigator.language || "en").split("-")[0];
    return lang || "en";
  }

  function showBubbleLoading() {
    if (!bubble) return;
    bubble.classList.add("is-visible");
    bubble.querySelector('[data-state="loading"]').hidden = false;
    bubble.querySelector('[data-state="ready"]').hidden = true;
    bubble.querySelector('[data-state="error"]').hidden = true;
  }

  function showBubbleResult(translation, model, durationMs) {
    if (!bubble) return;
    const ready = bubble.querySelector('[data-state="ready"]');
    ready.querySelector(".solar-air-translation").textContent = translation;
    ready.querySelector(".solar-air-model").textContent = model || "";
    ready.querySelector(".solar-air-duration").textContent = durationMs ? `${durationMs} ms` : "";

    bubble.querySelector('[data-state="loading"]').hidden = true;
    bubble.querySelector('[data-state="error"]').hidden = true;
    ready.hidden = false;
    bubble.classList.add("is-visible");
  }

  function showBubbleError(message) {
    if (!bubble) return;
    const err = bubble.querySelector('[data-state="error"]');
    err.querySelector(".solar-air-error-text").textContent = message;
    bubble.querySelector('[data-state="loading"]').hidden = true;
    bubble.querySelector('[data-state="ready"]').hidden = true;
    err.hidden = false;
    bubble.classList.add("is-visible");
  }

  function closeBubble(immediate = false) {
    if (!bubble) return;
    bubble.classList.remove("is-visible");
    airActiveForSelection = null;
    airIsLoading = false;
    clearTimeout(airAutoHideTimer);
  }

  function scheduleAirAutoHide() {
    clearTimeout(airAutoHideTimer);
    airAutoHideTimer = setTimeout(() => closeBubble(), AIR_AUTO_HIDE_MS);
  }

  async function triggerAirTranslation() {
    if (!lastSelection) return;
    if (airActiveForSelection === lastSelection && !airIsLoading) {
      // Already showing translation for this exact selection — just keep visible.
      bubble.classList.add("is-visible");
      scheduleAirAutoHide();
      return;
    }

    airActiveForSelection = lastSelection;
    airIsLoading = true;
    showBubbleLoading();

    // Air mode uses "auto" — backend decides target based on source language
    // (RU → EN, anything else → RU). This matches multilingual workflows.
    const targetLanguage = "auto";
    const requestedFor = lastSelection;

    console.log("[Solar Air] sending:", {
      text: requestedFor.slice(0, 60) + (requestedFor.length > 60 ? "..." : ""),
      length: requestedFor.length,
      targetLanguage,
    });

    chrome.runtime.sendMessage(
      {
        type: "solar.translate_air",
        payload: {
          text: requestedFor,
          targetLanguage,
        },
      },
      (resp) => {
        airIsLoading = false;

        if (chrome.runtime.lastError) {
          console.warn("[Solar Air] runtime error:", chrome.runtime.lastError);
          showBubbleError("Background not responding");
          scheduleAirAutoHide();
          return;
        }

        console.log("[Solar Air] response:", resp);

        // Guard: another selection may have happened while we waited.
        if (airActiveForSelection !== requestedFor) {
          console.log("[Solar Air] selection changed, dropping response");
          return;
        }

        if (!resp || !resp.ok) {
          const msg = resp?.status === 0
            ? "Solar Core not running"
            : (resp?.error || "Translation failed");
          showBubbleError(msg);
          scheduleAirAutoHide();
          return;
        }

        const data = resp.data;
        const modelLabel = data.model ? `${data.provider}/${data.model}` : "";
        showBubbleResult(data.translation, modelLabel, data.duration_ms);
        scheduleAirAutoHide();
      }
    );
  }

  function onButtonMouseEnter() {
    clearTimeout(hideTimer);

    // For short selections — Air mode (instant inline translation).
    // For long selections — fall back to original hover quick-menu.
    if (isShortSelection(lastSelection)) {
      clearTimeout(airHoverTimer);
      airHoverTimer = setTimeout(triggerAirTranslation, AIR_HOVER_DELAY_MS);
    } else {
      hideTimer = setTimeout(openMenu, AIR_HOVER_DELAY_MS);
    }
  }

  function onButtonMouseLeave() {
    clearTimeout(airHoverTimer);
    clearTimeout(hideTimer);
    // Don't close bubble immediately — user might be moving toward it.
    hideTimer = setTimeout(() => {
      if (!bubble || !bubble.matches(":hover")) {
        closeMenu();
      }
    }, AIR_DEBOUNCE_MS);
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
      // If the selection genuinely changed, clear any previous Air bubble state.
      if (sel.text !== lastSelection) {
        closeBubble(true);
      }
      lastSelection = sel.text;
      lastRect = sel.rect;
      showAt(sel.rect);
    }, 50);
  }

  // ---------- Action dispatch (sidepanel pipeline) ----------
  function onPrimaryClick(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    if (menuOpen) {
      closeMenu();
      return;
    }
    runAction("translate", "ru");
  }

  async function runAction(action, language) {
    if (!lastSelection) return;
    button.classList.add("is-loading");
    closeMenu(true);
    closeBubble(true);

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
        hide();
      }
    );
  }

  // ---------- Listeners ----------
  document.addEventListener("selectionchange", onSelectionChanged);
  document.addEventListener("mousedown", (e) => {
    if (!button) return;
    if (e.target?.id === BTN_ID || e.target?.closest?.(`#${BTN_ID}`)) return;
    if (e.target?.id === MENU_ID || e.target?.closest?.(`#${MENU_ID}`)) return;
    if (e.target?.id === BUBBLE_ID || e.target?.closest?.(`#${BUBBLE_ID}`)) return;
    hide();
  });
  window.addEventListener("scroll", hide, { passive: true });
  window.addEventListener("blur", hide);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hide();
  });
})();
