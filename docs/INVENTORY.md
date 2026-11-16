# INVENTORY — the element set, chosen by evidence

Owner: "we must figure out elements that are actually used by browsers and sites and GTK 6 …
whatever is actually used by people." Nothing stays in the set without a citation. This file is
the contract for the v0.4.0 element rebuild; every demo site must use every row.

Evidence sources:
- **GTK6** — libadwaita stable widget vocabulary (GTK 6; desktop-native grade).
- **LIBS** — the component sets of the web libraries people actually ship: shadcn/ui,
  Ant Design, MUI, Bootstrap, Radix, WebAwesome. A row marked LIBS appears in at least
  three of these five (universal usage), or is flagged.
- **CORPUS** — a 328-site wave-1 corpus + guide corpus (dashboard/tools UX,
  magazine/editorial, design-system, long-form-reading guides). Corpus contributes pattern
  evidence (style-level); where a row lives only in CORPUS it is a v2 survivor, not new invention.

Coverage rule: for each theme slug, its demo site (home + pages + app mocks) must reference
every row's class at least once. tools/check_sites.py enforces this.

## Group 1 — Structure
| Class | Evidence | Notes |
|---|---|---|
| .el-page | LIBS | page frame; measure/gutter tokens |
| .el-navbar (variants --top, --rail, --headerbar) | GTK6+LIBS | structural slot: nav form |
| .el-sidebar | GTK6+LIBS | nav rail w/ section list |
| .el-hero (variants --centered, --left, --split, --poster) | LIBS | structural slot: hero anatomy |
| .el-section | LIBS | heading + body + actions shell |
| .el-footer | LIBS | columns + small print + colophon |

## Group 2 — Surfaces
| Class | Evidence | Notes |
|---|---|---|
| .el-card (anatomy: flat/raised/press/print) | LIBS | structural slot: card anatomy |
| .el-panel | LIBS | quiet container |
| .el-chip | LIBS | tag / filter chip (selectable) |
| .el-badge | LIBS | status/count badge |
| .el-pill | LIBS | nav/small-caps pill (exists) |
| .el-avatar | LIBS | image/initials, sizes |
| .el-empty | LIBS | empty state (icon + title + action) |
| .el-media-band | LIBS | image/case band w/ caption |
| .el-pricing | LIBS | price row / plan card |
| .el-testimonial | LIBS | quote w/ attribution |
| .el-kbd | LIBS | keyboard key chip (docs sites) |

## Group 3 — Data
| Class | Evidence | Notes |
|---|---|---|
| .el-table (variants ruled/zebra/bank/broadsheet) | LIBS+CORPUS | structural slot: table treatment |
| .el-stat | LIBS+CORPUS | metric tile: label, big value, delta, sparkline |
| .el-progress / .el-progress-truth | CORPUS(v2) | stages-based honest progress |
| .el-meter | GTK6 | level bar (capacity/health) |
| .el-fact-grid | CORPUS(v2) | sourced fact cards |
| .el-timeline | LIBS | vertical event list |
| .el-sparkline / [data-chart] | LIBS+CORPUS | charts.js (exists) |
| .el-status-dot | GTK6+CORPUS | idle/running/ok/warn/fail/live |
| .el-source-card, .el-citation-rail | CORPUS(v2) | keep |

## Group 4 — Input
| Class | Evidence | Notes |
|---|---|---|
| .el-input / textarea (+ .el-field label/hint/error) | LIBS | exists |
| .el-select | LIBS | styled native select |
| .el-switch | GTK6+LIBS | exists |
| .el-check | LIBS | checkbox + radio |
| .el-segmented | GTK6+LIBS | segmented control (radio group) |
| .el-slider | GTK6+LIBS | range |
| .el-search | LIBS | search field w/ icon + focus voice |
| .el-btn (+ ghost/outline/squared variants, group) | LIBS | exists |
| .el-stepper (.el-ladder-step) | CORPUS(v2) | keep |
| .el-pagination | LIBS | page list + prev/next |

## Group 5 — Overlays
| Class | Evidence | Notes |
|---|---|---|
| .el-dialog | GTK6+LIBS | modal (JS open/close) |
| .el-drawer | LIBS | side sheet (inspector variant family) |
| .el-popover | GTK6+LIBS | anchored menu popover |
| .el-tooltip | LIBS | hover tip |
| .el-toast | GTK6+LIBS | toast stack (JS push) |
| .el-command | LIBS | command palette (JS) |
| .el-menu | GTK6+LIBS | dropdown menu list |
| .el-inspector, .el-reader, .el-assistant-panel | CORPUS(v2) | keep |

## Group 6 — Feedback
| Class | Evidence | Notes |
|---|---|---|
| .el-spinner | LIBS | indeterminate |
| .el-inline-alert | LIBS | info/warn/fail/success inline |
| .el-skeleton | LIBS | loading placeholder shimmer |
| .el-status-pill | CORPUS(v2) | queued/running/ok/stale/live (v2 stage tokens) |
| .el-banner | LIBS | dismissible announcement bar |

## Group 7 — App chrome (GTK 6 grade; app-mockup layer)
| Class | Evidence | Notes |
|---|---|---|
| .el-appwin | GTK6 | window frame: titlebar + window buttons |
| .el-listbox | GTK6+LIBS | rows: leading icon, label, trailing action |
| .el-actionbar | GTK6 | bottom bar: primary + secondary actions |
| .el-headerbar | GTK6 | window-attached toolbar (persona nav slot) |
| .el-notification | LIBS | notification center card stack |
| .el-tabbar | LIBS | bottom/app tab bar |
| .el-menu | (dup w/ overlays) | |

## Group 8 — Workflow (v2 survivors)
.el-stage-rail, .el-ladder-step, .el-progress-truth, .el-pt-chunk, .el-fact-grid,
.el-source-card, .el-citation-rail, .el-inspector, .el-reader, .el-assistant-panel — kept as-is.

## Structural slots (persona contract)
Themes set and restyle, sites mark up: nav form (--el-nav-form: top|rail|headerbar via variant
classes), hero anatomy, card anatomy, table treatment, density. check_sites.py enforces ELEMENT
coverage; persona coherence reviewed by eye per site.

## Files (v0.4 target)
New: elements-app.css, elements-overlay.css. Rebuilt: elements-display, elements-lists,
elements-controls, elements-inputs, elements-dataviz, elements-containers, elements-interactions,
elements-misc. Kept: elements-workflow, elements-inspector, elements-reader, elements-assistant,
elements-size, base.css, tokens.css, tokens-v2.css. Single JS owner for elements.js upgrades.