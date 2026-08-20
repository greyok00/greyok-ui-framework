# greyok-ui-framework

![logo](assets/wordmark.svg)

**CSS + JS framework — ~100 UI primitives, 12 themes, 6 size buckets.**

Distributable. Themeable. Works in HTML/CSS, Tkinter (via Python bridge), and TypeScript projects.

> 100 elements · 12 themes · 6 sizes · 3 languages
>
> `neutral` · `polaroid` · `cockpit` · `cockpit-paper` · `console` · `compact` · `casebook` · `agent-paper` · `agent-pulse` · `agent-history` · `terminal` · `swiss`

## Features

| Layer | What |
|---|---|
| **Elements** | ~100 primitives across 7 categories — Display, Lists, Controls, Data viz, Containers, Inputs, Interactions |
| **Themes** | 12 swappable themes via `[data-theme="…"]`. Switcher persists to `localStorage` + URL hash |
| **Sizes** | 6 buckets — xs (48×48) / sm (50×200) / md / lg (1200×400) / full (1200×800) / tray (720×420) |
| **Tokens** | ~55 CSS variables — color, type, space, radius, shadow, motion |
| **Languages** | HTML/CSS, TypeScript (declarations), Python (Tkinter bridge) |
| **No build step** | Drop in the CSS files and `<script>` tag; nothing to compile |

## Install

### HTML/CSS (zero config)

```html
<link rel="stylesheet" href="node_modules/greyok-ui-framework/tokens.css">
<link rel="stylesheet" href="node_modules/greyok-ui-framework/themes.css">
<link rel="stylesheet" href="node_modules/greyok-ui-framework/base.css">
<link rel="stylesheet" href="node_modules/greyok-ui-framework/elements-display.css">
<link rel="stylesheet" href="node_modules/greyok-ui-framework/elements-lists.css">
<link rel="stylesheet" href="node_modules/greyok-ui-framework/elements-controls.css">
<link rel="stylesheet" href="elements-dataviz.css">
<link rel="stylesheet" href="elements-containers.css">
<link rel="stylesheet" href="elements-inputs.css">
<link rel="stylesheet" href="elements-interactions.css">
<link rel="stylesheet" href="elements-size.css">
<script src="theme-switcher.js" defer></script>
<script src="elements.js" defer></script>
```

### npm

```bash
npm install greyok-ui-framework
```

### Python / Tkinter

```python
from greyok_ui_framework import ElTheme, ElWidget

theme = ElTheme("cockpit")  # or any of 12
btn = ElWidget("btn", label="Run", theme=theme)
btn.pack()
```

### TypeScript

```typescript
import "greyok-ui-framework/typescript/elements.d.ts";

const pill = document.querySelector(".el-pill.ok") as HTMLSpanElement;
```

## Theme switcher

The framework ships a tiny switcher (`theme-switcher.js`) that:

1. Reads `localStorage['el-theme']` on load
2. Falls back to URL hash `#theme=<slug>`
3. Falls back to `neutral`
4. Sets `document.documentElement.dataset.theme = <slug>`

Add a picker to any page:

```html
<select id="theme-picker">
  <option value="neutral">neutral</option>
  <option value="polaroid">polaroid</option>
  <option value="cockpit">cockpit</option>
  ...
</select>
<script>
  document.getElementById('theme-picker').addEventListener('change', e => {
    document.documentElement.dataset.theme = e.target.value;
    localStorage.setItem('el-theme', e.target.value);
  });
</script>
```

## Themes

| Slug | Aesthetic | Bg polarity | Accent |
|---|---|---|---|
| `neutral` | graphite + amber | dark | `#ffb000` |
| `polaroid` | warm paper | light | `#b8693c` |
| `cockpit` | aviation HMI | dark | `#ffb000` |
| `cockpit-paper` | warm cockpit | dark | `#d4a85a` |
| `console` | GitHub Dark | dark | `#58a6ff` |
| `compact` | neutral dark grey | dark | `#ff8c42` |
| `casebook` | cream paper | light | `#8b5e34` |
| `agent-paper` | textbook figure | light | `#0e7c86` |
| `agent-pulse` | breathing pulse | dark | `#ffb000` |
| `agent-history` | git-log on warm | light | `#0e7c86` |
| `terminal` | CRT green-on-black | dark | `#00ff66` |
| `swiss` | editorial B/W + red | light | `#d62828` |

## Sizes

| Token | Width | Use |
|---|---|---|
| `.el-xs-frame` | 48 px | icon button, status dot |
| `.el-sm-frame` | 50 × 200 | vertical tray popup |
| `.el-md-frame` | fluid | default |
| `.el-lg-frame` | 1200 × 400 | wide-short banner |
| `.el-full` | 1200 × 800 | desktop |
| `.el-tray` | 720 × 420 | popup-shaped wrapper |

Apply directly on any element: `<span class="el-pill el--xs">…</span>`

## Elements

See `demo/` for live examples. Each category has its own page:

```
demo/
├── index.html          ← landing
├── display.html        ← pill, dot, gauge, big-num, kbd, avatar, progress…
├── lists.html          ← timeline, accordion, table, kanban, tree, breadcrumb…
├── controls.html       ← dropdown, toggle, switch, slider, segmented, palette…
├── dataviz.html        ← mini-bar, mini-line, entity-graph, heatmap, diff-view…
├── containers.html     ← panel, tabs, modal, drawer, bento, split-pane…
├── inputs.html         ← input, textarea, search-bar, prompt, file-upload…
├── interactions.html   ← drag/drop, tooltip, popover, context-menu, toast…
├── themes.html         ← 4×3 grid of theme cards (every theme × 8 elements)
└── sizes.html          ← same element in all 6 size buckets × 2 themes
```

## Run the demo

```bash
python3 -m http.server 8768 --bind 127.0.0.1
# open http://127.0.0.1:8768/demo/
```

## Project layout

```
_elements/
├── tokens.css               # ~55 CSS vars (neutral defaults)
├── themes.css               # 12 [data-theme="..."] blocks
├── base.css                 # reset, focus ring, scrollbar, demo bar
├── elements-display.css     # 15 display primitives
├── elements-lists.css       # 15 list primitives
├── elements-controls.css    # 15 control primitives
├── elements-dataviz.css     # 10 data-viz primitives
├── elements-containers.css  # 12 container primitives
├── elements-inputs.css      # 10 input primitives
├── elements-interactions.css # 10 interaction primitives
├── elements-size.css        # 6 size buckets
├── elements.js              # all interactive hooks
├── theme-switcher.js        # localStorage + URL hash bridge
├── python/
│   └── greyok_ui_framework.py      # Tkinter bridge — converts theme tokens → tk config
├── typescript/
│   └── elements.d.ts        # declarations for every el-* class + data-* attr
├── demo/                    # 10 demo HTML files
├── package.json
├── LICENSE                  # MIT
└── README.md
```

## Conventions

- All elements prefixed with `.el-*` (or `data-*` for behavior)
- All status uses `--el-ok / --el-warn / --el-fail / --el-info / --el-live`
- All severity uses `.CRIT / .HIGH / .OK` (border-left-color hook)
- Themes declare the full token set; never partial overrides
- Demo pages use the theme switcher at the top

## License

MIT — see LICENSE.

## Author

greyok00
