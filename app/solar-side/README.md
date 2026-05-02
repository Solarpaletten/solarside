# Solar Side

> Chrome extension that turns any web selection into a Solar Core action.
>
> **Highlight text → click "Solar" → AI processes it → result in side panel → save / send to Solar ERP.**

## Status s

**Phase 1 / Step 2 — Extension v0.1.0**

- ✅ Manifest V3
- ✅ Floating "Solar" button on text selection
- ✅ Right-click context menu (Summarize / Extract / Translate to RU)
- ✅ Side panel UI with result + actions
- ✅ Health badge — shows whether Core is reachable
- ✅ Save selection as a Solar ERP note (mock — real ERP in Step 3)
- ✅ Settings page (Core URL + API key)

## Prerequisites

Solar Core must be running locally:

```bash
cd ../solar-core
uvicorn solar_core.main:app --reload --port 8000
```

You can verify it's up:

```bash
curl http://localhost:8000/v1/health
```

## Install (unpacked, for development)

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select this folder (`solar-side/`)
5. Pin the **Solar** icon to your toolbar (puzzle icon → pin)

## Configuration

Click the Solar icon → **Settings**, or right-click the icon → **Options**.

| Field    | Default                  | Notes                                  |
|----------|--------------------------|----------------------------------------|
| Core URL | `http://localhost:8000`  | Where Solar Core is reachable          |
| API key  | `dev-key-1`              | Must match `SOLAR_API_KEYS` in Core    |

Press **Test connection** — you should see `OK — Solar Core v0.1.0`.

## Usage

### Floating button

1. Highlight any text on any page
2. A small orange **Solar** button appears just above the selection
3. Click it → side panel opens with the summary (in your browser language)

### Context menu

1. Highlight text
2. Right-click → choose one of:
   - **Solar — Summarize**
   - **Solar — Extract entities**
   - **Solar — Translate to Russian**
3. Side panel opens with the result

### Quick actions in the side panel

- **Copy result** — clipboard
- **Summarize again** — re-run with the same source
- **Translate to RU** — re-run as translation
- **→ Save as Solar Note** — POST to Solar Core's `solar_erp.create_note` connector (currently a mock; will become a real ERP entry in Step 3)

## Project structure

```
solar-side/
├── manifest.json
├── icons/                 (16, 32, 48, 128 px)
├── src/
│   ├── background/
│   │   └── service_worker.js   # context menu, side panel, message routing
│   ├── content/
│   │   ├── content.js          # floating button on selection
│   │   └── content.css
│   ├── sidepanel/
│   │   ├── sidepanel.html
│   │   └── sidepanel.js
│   ├── popup/
│   │   ├── popup.html / popup.js
│   │   └── options.html        # settings page
│   ├── lib/
│   │   ├── api.js              # Solar Core HTTP client
│   │   └── messages.js         # message type constants
│   └── styles/
│       └── sidepanel.css
```

## Troubleshooting

| Symptom                                            | Fix                                                     |
|----------------------------------------------------|---------------------------------------------------------|
| Status badge shows `● offline`                     | Start Solar Core (`uvicorn solar_core.main:app --reload`) |
| Side panel shows `HTTP 401`                        | API key in extension settings ≠ `SOLAR_API_KEYS` in Core |
| Status shows `no AI key configured`                | Set `ANTHROPIC_API_KEY` in Core's `.env`                |
| Floating button doesn't appear                     | Some sites block content scripts (e.g. `chrome://*`) — use the right-click menu instead |
| `chrome.sidePanel` is undefined                    | Need Chrome ≥ 114                                       |

## Architecture decisions

- **Side panel over popup.** Popups close on every click outside; side panel stays open while you read the source. Better fit for the "AI assistant working alongside you" metaphor.
- **Floating button + context menu.** Discoverable for newcomers, fast for power users.
- **No build step.** Pure ES modules, no bundler. Trivial to inspect, modify, and ship.
- **All Core logic stays in Core.** The extension is a thin client. We can replace it with a desktop app or a Chromium shell later without touching Solar Core (per ADR-001).

## License

Proprietary — Solar Team / Leanid Kanoplich.
