(function themeSwitcher() {
  const STORAGE_KEY = 'el-theme';
  const DEFAULT = 'neutral';
  const THEMES = [
    'neutral', 'mono-console', 'ghost-terminal', 'cream-journal', 'paper-press',
    'brutal-stamp', 'brutal-index', 'orbit-deep', 'solar-halo',
    'agency-quartz', 'agency-mono-plate', 'maison-serif', 'noir-couture',
    'sticker-pop', 'sketchbook', 'console-light', 'grid-ledger',
    'kinetic-ink', 'aperture-motion', 'ma-quiet', 'gesshoku'
  ];
  const VALID = new Set(THEMES);
  const NAMES = {
    'neutral': 'Neutral',
    'mono-console': 'Mono Console',
    'ghost-terminal': 'Ghost Terminal',
    'cream-journal': 'Cream Journal',
    'paper-press': 'Paper Press',
    'brutal-stamp': 'Brutal Stamp',
    'brutal-index': 'Brutal Index',
    'orbit-deep': 'Orbit Deep',
    'solar-halo': 'Solar Halo',
    'agency-quartz': 'Agency Quartz',
    'agency-mono-plate': 'Agency Mono-Plate',
    'maison-serif': 'Maison Serif',
    'noir-couture': 'Noir Couture',
    'sticker-pop': 'Sticker Pop',
    'sketchbook': 'Sketchbook',
    'console-light': 'Console Light',
    'grid-ledger': 'Grid Ledger',
    'kinetic-ink': 'Kinetic Ink',
    'aperture-motion': 'Aperture Motion',
    'ma-quiet': 'MA Quiet',
    'gesshoku': 'Gesshoku'
  };
  const GLYPHS = {
    'neutral': '<g fill="currentColor"><circle cx="4" cy="4" r="1.1"/><circle cx="8" cy="4" r="1.1"/><circle cx="12" cy="4" r="1.1"/><circle cx="4" cy="8" r="1.1"/><circle cx="8" cy="8" r="1.1"/><circle cx="12" cy="8" r="1.1"/><circle cx="4" cy="12" r="1.1"/><circle cx="8" cy="12" r="1.1"/><circle cx="12" cy="12" r="1.1"/></g>',
    'mono-console': '<rect x="1.75" y="2.75" width="12.5" height="10.5" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M5 6.25l2.4 2-2.4 2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M9.2 10.75h2.8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>',
    'ghost-terminal': '<path d="M2.5 5l2.8 2.75-2.8 2.75" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M7.4 5l2.8 2.75-2.8 2.75" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.45"/><path d="M11.4 11.25h2.2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>',
    'cream-journal': '<path d="M4.5 2.5h4.6l2.9 2.9v8.1H4.5z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M9.1 2.5v2.9H12" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M6.7 9.2h3.9M6.7 11.5h3.9" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>',
    'paper-press': '<rect x="2.6" y="2.4" width="10.8" height="2.3" rx="0.6" fill="currentColor"/><path d="M8 4.9v2.5" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="5.2" y="7.4" width="5.6" height="1.8" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M3.6 11.9h8.8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>',
    'brutal-stamp': '<rect x="2.2" y="2.2" width="11.6" height="11.6" fill="none" stroke="currentColor" stroke-width="2"/><rect x="6.1" y="6.1" width="3.8" height="3.8" fill="currentColor"/>',
    'brutal-index': '<path d="M2.4 3.2h11.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square"/><path d="M2.4 7.2h7.4M2.4 10.2h5.2M2.4 13.2h9.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="square"/>',
    'orbit-deep': '<circle cx="8" cy="8" r="2.1" fill="currentColor"/><ellipse cx="8" cy="8" rx="6.4" ry="2.5" fill="none" stroke="currentColor" stroke-width="1.3" transform="rotate(-26 8 8)"/>',
    'solar-halo': '<circle cx="8" cy="8" r="3" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M8 1.4v2.1M8 12.5v2.1M1.4 8h2.1M12.5 8h2.1" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>',
    'agency-quartz': '<path d="M8 1.8L13.2 8 8 14.2 2.8 8z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M2.8 8h10.4M8 1.8v12.4" fill="none" stroke="currentColor" stroke-width="1.1" opacity="0.6"/>',
    'agency-mono-plate': '<rect x="1.6" y="4.4" width="12.8" height="7.2" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.4"/><circle cx="4" cy="6.6" r="0.9" fill="currentColor"/><circle cx="12" cy="9.4" r="0.9" fill="currentColor"/><path d="M6.4 8h3.2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>',
    'maison-serif': '<path d="M8 4v8.2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M5.3 4h5.4M5.3 12.2h5.4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="1.9" r="1" fill="currentColor"/>',
    'noir-couture': '<circle cx="10.2" cy="5.8" r="3.4" fill="currentColor" opacity="0.85"/><rect x="2.6" y="5" width="3.6" height="8" fill="currentColor" opacity="0.55"/>',
    'sticker-pop': '<rect x="3.7" y="3.7" width="8.6" height="8.6" rx="2" transform="rotate(45 8 8)" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="11.6" cy="4.6" r="1.4" fill="currentColor"/>',
    'sketchbook': '<path d="M2.9 11.4l1.9-4.8 2.1 4.8 2-4.8 2.1 4.8 2-4.8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>',
    'console-light': '<rect x="2.2" y="2.6" width="11.6" height="10.8" rx="2" fill="none" stroke="currentColor" stroke-width="1.4"/><circle cx="8" cy="6.3" r="1.8" fill="currentColor"/><path d="M5.2 10.7h5.6" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>',
    'grid-ledger': '<rect x="2.4" y="2.4" width="11.2" height="11.2" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M8 2.4v11.2M2.4 8h11.2" fill="none" stroke="currentColor" stroke-width="1.1"/>',
    'kinetic-ink': '<path d="M8 2.4c2.5 3.5 3.9 5.4 3.9 7.1a3.9 3.9 0 0 1-7.8 0c0-1.7 1.4-3.6 3.9-7.1z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>',
    'aperture-motion': '<path d="M8 2l5.2 3v6L8 14 2.8 11V5z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><circle cx="8" cy="8" r="2" fill="currentColor"/>',
    'ma-quiet': '<circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.55"/><circle cx="8" cy="8" r="1.4" fill="currentColor"/>',
    'gesshoku': '<path d="M9.9 2.3a6 6 0 1 0 0 11.4 4.8 4.8 0 1 1 0-11.4z" fill="currentColor"/>',
  };
  // Local-only extension point: a page may predefine window.EL_EXTRA_THEMES =
  // {themes: [...slugs], names: {slug: Name}, glyphs: {slug: inner-svg}} to add
  // private (non-published) themes to the strip without touching this file.
  try {
    const EXTRA = window.EL_EXTRA_THEMES;
    if (EXTRA && Array.isArray(EXTRA.themes)) {
      EXTRA.themes.forEach(function (slug) {
        if (VALID.has(slug)) return;
        VALID.add(slug);
        THEMES.push(slug);
        if (EXTRA.names && EXTRA.names[slug]) NAMES[slug] = EXTRA.names[slug];
        if (EXTRA.glyphs && EXTRA.glyphs[slug]) GLYPHS[slug] = EXTRA.glyphs[slug];
      });
    }
  } catch (_) {}

  const STRIP_CSS = `
.el-theme-strip{display:flex;flex-wrap:wrap;gap:6px;align-items:center;max-width:100%}
.el-theme-strip button{width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center;padding:0;margin:0;background:var(--el-panel);border:1px solid var(--el-line);border-radius:9px;color:var(--el-ink-soft);cursor:pointer;appearance:none;font:inherit;transition:transform var(--el-dur-fast,140ms) var(--el-ease,cubic-bezier(.33,1,.68,1)),border-color var(--el-dur-fast,140ms) var(--el-ease,cubic-bezier(.33,1,.68,1)),color var(--el-dur-fast,140ms) var(--el-ease,cubic-bezier(.33,1,.68,1))}
.el-theme-strip button svg{display:block;pointer-events:none}
.el-theme-strip button:hover{color:var(--el-ink);transform:var(--el-lift,translateY(-1px))}
.el-theme-strip button:focus-visible{outline:2px solid var(--el-focus-ring);outline-offset:2px}
.el-theme-strip button[aria-checked="true"]{border-color:var(--el-accent);color:var(--el-accent);box-shadow:0 0 0 2px var(--el-focus-ring)}
.el-theme-strip button[aria-checked="true"]:focus-visible{outline-color:var(--el-accent)}
.el-theme-card{display:flex;flex-direction:column;gap:10px;padding:14px;background:var(--el-panel);border:1px solid var(--el-line);border-radius:var(--el-r-md,10px);cursor:pointer;transition:box-shadow var(--el-dur-fast,140ms) var(--el-ease,cubic-bezier(.33,1,.68,1)),border-color var(--el-dur-fast,140ms) var(--el-ease,cubic-bezier(.33,1,.68,1))}
.el-theme-card:hover{border-color:var(--el-line-strong);box-shadow:var(--el-shadow-2,0 4px 12px rgba(0,0,0,.35))}
.el-theme-card-swatch-row{display:flex;gap:5px}
.el-theme-card-swatch{width:18px;height:18px;border-radius:5px;border:1px solid var(--el-line)}
.el-theme-card-name{font-family:var(--el-font-display);font-size:13px;font-weight:600;letter-spacing:0.01em;color:var(--el-ink)}
@media (prefers-reduced-motion: reduce){
  .el-theme-strip button{transition:none;transform:none}
  .el-theme-card{transition:none}
}
`;

  function readInitial() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && VALID.has(stored)) return stored;
    } catch (_) { }
    const hash = (location.hash || '').match(/theme=([a-z\-]+)/);
    if (hash && VALID.has(hash[1])) return hash[1];
    return DEFAULT;
  }

  function current() {
    return document.documentElement.dataset.theme || DEFAULT;
  }

  function syncStrips(slug) {
    document.querySelectorAll('.el-theme-strip button[data-theme-slug]').forEach(btn => {
      const on = btn.dataset.themeSlug === slug;
      btn.setAttribute('aria-checked', on ? 'true' : 'false');
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  function syncPickers(slug) {
    document.querySelectorAll('[data-theme-picker], #theme-picker').forEach(el => {
      if ('value' in el && el.value !== slug) el.value = slug;
    });
  }

  function apply(slug) {
    if (!VALID.has(slug)) slug = DEFAULT;
    document.documentElement.dataset.theme = slug;
    try { localStorage.setItem(STORAGE_KEY, slug); } catch (_) { }
    syncPickers(slug);
    syncStrips(slug);
  }

  function tileSvg(slug) {
    return '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">' + (GLYPHS[slug] || GLYPHS[DEFAULT]) + '</svg>';
  }

  function makeTile(slug) {
    const name = NAMES[slug] || slug;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'el-theme-tile';
    btn.dataset.themeSlug = slug;
    btn.title = name;
    btn.setAttribute('aria-label', name);
    btn.setAttribute('aria-checked', 'false');
    btn.setAttribute('aria-pressed', 'false');
    btn.innerHTML = tileSvg(slug);
    btn.addEventListener('click', () => apply(slug));
    return btn;
  }

  function buildStrip() {
    const rail = document.createElement('div');
    rail.className = 'el-theme-strip';
    rail.setAttribute('role', 'radiogroup');
    rail.setAttribute('aria-label', 'Theme');
    THEMES.forEach(slug => rail.appendChild(makeTile(slug)));
    rail.addEventListener('keydown', e => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      const tiles = Array.from(rail.querySelectorAll('button[data-theme-slug]'));
      const i = tiles.indexOf(document.activeElement);
      if (i === -1) return;
      const step = e.key === 'ArrowLeft' ? -1 : 1;
      tiles[(i + step + tiles.length) % tiles.length].focus();
      e.preventDefault();
    });
    return rail;
  }

  function injectStyle() {
    if (document.getElementById('el-theme-strip-style')) return;
    const style = document.createElement('style');
    style.id = 'el-theme-strip-style';
    style.textContent = STRIP_CSS;
    document.head.appendChild(style);
  }

  function renderStrips() {
    injectStyle();
    const hosts = new Set();
    document.querySelectorAll('[data-theme-strip]').forEach(host => hosts.add(host));
    document.querySelectorAll('select#theme-picker, select[data-theme-picker]').forEach(sel => {
      sel.style.display = 'none';
      if (sel.dataset.elStripHost) return;
      const host = document.createElement('div');
      host.setAttribute('data-theme-strip', '');
      sel.dataset.elStripHost = '1';
      sel.insertAdjacentElement('afterend', host);
      hosts.add(host);
    });
    hosts.forEach(host => {
      if (!host.querySelector('.el-theme-strip')) host.appendChild(buildStrip());
    });
    syncStrips(current());
  }

  function wire() {
    document.querySelectorAll('[data-theme-picker], #theme-picker').forEach(el => {
      el.addEventListener('change', () => apply(el.value));
    });

    document.querySelectorAll('[data-set-theme]').forEach(el => {
      el.addEventListener('click', () => apply(el.dataset.setTheme));
    });

    window.addEventListener('hashchange', () => {
      const m = (location.hash || '').match(/theme=([a-z\-]+)/);
      if (m && VALID.has(m[1])) apply(m[1]);
    });
  }

  window.elTheme = { apply, list: () => Array.from(VALID), DEFAULT };

  document.addEventListener('DOMContentLoaded', () => {
    apply(readInitial());
    renderStrips();
    wire();
  });

  if (document.readyState !== 'loading') {
    apply(readInitial());
    renderStrips();
    wire();
  }
})();