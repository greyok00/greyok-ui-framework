(function Charts() {
  'use strict';

  // ── helpers ────────────────────────────────────────────────────────────────
  const NS = 'http://www.w3.org/2000/svg';
  const svg = (w, h) => {
    const s = document.createElementNS(NS, 'svg');
    s.setAttribute('width', w); s.setAttribute('height', h);
    s.setAttribute('viewBox', `0 0 ${w} ${h}`);
    s.setAttribute('role', 'img');
    s.classList.add('el-chart-svg');
    return s;
  };
  const el = (name, attrs, title) => {
    const n = document.createElementNS(NS, name);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (title) {
      const t = document.createElementNS(NS, 'title');
      t.textContent = title;
      n.appendChild(t);
    }
    return n;
  };
  const num = (v, d) => (Number.isFinite(+v) ? +v : d);
  const cssVar = (v) => v || 'currentColor';

  function resolve(vals, opts) {
    const width  = num(opts.width, 240);
    const height = num(opts.height, 64);
    const pad    = num(opts.padding, 4);
    const maxV   = num(opts.max, Math.max(...vals, 1));
    const minV   = num(opts.min, Math.min(...vals, 0));
    const span   = (maxV - minV) || 1;
    const pts    = vals.map((v, i) => ({
      x: vals.length > 1 ? pad + (i / (vals.length - 1)) * (width - pad * 2) : width / 2,
      y: height - pad - ((v - minV) / span) * (height - pad * 2),
      v
    }));
    return { width, height, pad, pts };
  }

  function linePath(pts) {
    return pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' ');
  }

  // ── primitives ─────────────────────────────────────────────────────────────
  function Sparkline(values, opts) {
    opts = opts || {};
    const vals = values.map(Number);
    const { width, height, pts } = resolve(vals, opts);
    const s = svg(width, height);
    s.appendChild(el('polyline', {
      points: pts.map(p => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' '),
      fill: 'none',
      stroke: cssVar(opts.color),
      'stroke-width': num(opts.strokeWidth, 1.5),
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      class: 'el-chart-anim-line'
    }, opts.label || null));
    return s;
  }

  function Line(values, opts) {
    opts = opts || {};
    const vals = values.map(Number);
    const { width, height, pad, pts } = resolve(vals, opts);
    const s = svg(width, height);
    // baseline
    s.appendChild(el('line', {
      x1: pad, y1: height - pad, x2: width - pad, y2: height - pad,
      stroke: 'var(--el-line, currentColor)', 'stroke-width': 1, opacity: 0.6
    }));
    // fill area (subtle)
    const path = linePath(pts);
    s.appendChild(el('path', {
      d: `${path} L${pts[pts.length - 1].x.toFixed(2)},${height - pad} L${pts[0].x.toFixed(2)},${height - pad} Z`,
      fill: 'var(--el-accent-soft, transparent)', stroke: 'none'
    }));
    pts.forEach((p, i) => {
      s.appendChild(el('line', {
        x1: p.x, y1: pad, x2: p.x, y2: height - pad,
        stroke: 'var(--el-line, currentColor)', 'stroke-width': 1, opacity: 0.15
      }));
      s.appendChild(el('circle', {
        cx: p.x.toFixed(2), cy: p.y.toFixed(2), r: 2.5,
        fill: cssVar(opts.color), class: 'el-chart-dot'
      }, opts.label ? `${opts.label}: ${p.v}` : (opts.labels ? `${opts.labels[i]}: ${p.v}` : String(p.v))));
    });
    const ln = el('path', {
      d: path, fill: 'none', stroke: cssVar(opts.color),
      'stroke-width': num(opts.strokeWidth, 2),
      'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      class: 'el-chart-anim-line'
    });
    s.appendChild(ln);
    return s;
  }

  function Area(values, opts) {
    opts = opts || {};
    const vals = values.map(Number);
    const { width, height, pad, pts } = resolve(vals, opts);
    const s = svg(width, height);
    const d = `${linePath(pts)} L${pts[pts.length - 1].x.toFixed(2)},${height - pad} L${pts[0].x.toFixed(2)},${height - pad} Z`;
    s.appendChild(el('path', {
      d, fill: cssVar(opts.color) === 'currentColor' ? 'var(--el-accent-soft, currentColor)' : cssVar(opts.color),
      stroke: 'none', opacity: 0.25, class: 'el-chart-anim-fade'
    }));
    s.appendChild(el('path', {
      d: linePath(pts), fill: 'none', stroke: cssVar(opts.color),
      'stroke-width': num(opts.strokeWidth, 1.5),
      'stroke-linecap': 'round', class: 'el-chart-anim-line'
    }, opts.label || null));
    return s;
  }

  function Bar(values, opts) {
    opts = opts || {};
    const vals = values.map(Number);
    const { width, height, pad, pts } = resolve(vals, opts);
    const maxV = num(opts.max, Math.max(...vals, 1));
    const n = vals.length;
    const slot = (width - pad * 2) / n;
    const bw = Math.max(1, slot * 0.65);
    const s = svg(width, height);
    pts.forEach((p, i) => {
      const h = Math.max(1, height - pad - p.y);
      const x = pad + i * slot + (slot - bw) / 2;
      s.appendChild(el('rect', {
        x: x.toFixed(2), y: (height - pad - h).toFixed(2),
        width: bw.toFixed(2), height: h.toFixed(2),
        rx: Math.min(2, bw / 3),
        fill: cssVar(opts.color),
        class: 'el-chart-anim-bar',
        style: `transform-origin:${(x + bw / 2).toFixed(2)}px ${(height - pad).toFixed(2)}px;animation-delay:${(i * 30)}ms`
      }, opts.label ? `${opts.label}: ${p.v}` : (opts.labels ? `${opts.labels[i]}: ${p.v}` : String(p.v))));
    });
    return s;
  }

  function Donut(pct, opts) {
    opts = opts || {};
    const size = num(opts.width, num(opts.height, 96));
    const stroke = num(opts.strokeWidth, 10);
    const r = (size - stroke) / 2;
    const c = 2 * Math.PI * r;
    const p = Math.max(0, Math.min(100, num(pct, 0)));
    const offset = c * (1 - p / 100);
    const s = svg(size, size);
    s.appendChild(el('circle', {
      cx: size / 2, cy: size / 2, r,
      fill: 'none',
      stroke: 'var(--el-line, currentColor)',
      'stroke-width': stroke, opacity: 0.25
    }));
    s.appendChild(el('circle', {
      cx: size / 2, cy: size / 2, r,
      fill: 'none',
      stroke: cssVar(opts.color),
      'stroke-width': stroke,
      'stroke-linecap': 'round',
      'stroke-dasharray': c.toFixed(2),
      'stroke-dashoffset': offset.toFixed(2),
      transform: `rotate(-90 ${size / 2} ${size / 2})`,
      class: 'el-chart-anim-donut'
    }, opts.label ? `${opts.label}: ${p}%` : `${p}%`));
    if (opts.label !== null && opts.label !== false) {
      const txt = el('text', {
        x: '50%', y: '50%',
        'text-anchor': 'middle',
        'dominant-baseline': 'central',
        fill: 'var(--el-ink, currentColor)',
        'font-size': Math.max(10, size * 0.2),
        'font-family': 'var(--el-font-mono, monospace)'
      });
      txt.textContent = `${p}%`;
      s.appendChild(txt);
    }
    return s;
  }

  // ── auto-render ────────────────────────────────────────────────────────────
  const kinds = { sparkline: Sparkline, bar: Bar, line: Line, donut: Donut, area: Area };

  function auto(root) {
    (root || document).querySelectorAll('[data-chart]').forEach(node => {
      if (node.__chart) return;
      const kind = (node.dataset.chart || '').toLowerCase();
      const fn = kinds[kind];
      if (!fn) return;
      const vals = (node.dataset.values || '').split(/[\s,]+/).filter(Boolean).map(Number);
      if (!vals.length) return;
      const opts = {
        width: node.dataset.width, height: node.dataset.height,
        color: node.dataset.color, label: node.dataset.label,
        labels: node.dataset.labels ? node.dataset.labels.split('|') : undefined,
        max: node.dataset.max
      };
      node.__chart = kind === 'donut' ? fn(vals[0], opts) : fn(vals, opts);
      node.appendChild(node.__chart);
    });
  }

  // ── export ─────────────────────────────────────────────────────────────────
  window.Charts = { Sparkline, Bar, Line, Donut, Area, auto };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => auto(document));
  } else {
    auto(document);
  }
})();