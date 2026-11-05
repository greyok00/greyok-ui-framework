#!/usr/bin/env python3
"""forensics.py <url> <selector> <w> — walk ancestors of first selector match, print layout boxes."""
import sys
sel, url, w = sys.argv[1], sys.argv[2], int(sys.argv[3])
h = int(sys.argv[4]) if len(sys.argv) > 4 else 900
from patchright.sync_api import sync_playwright
JS_CENSUS = """() => {
  const vw = document.documentElement.clientWidth;
  const rows = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (r.right <= vw + 1) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none') continue;
    // nearest overflow-X ancestor
    let kind = 'document', anc = el.parentElement, ancDesc = '';
    while (anc && anc !== document.documentElement) {
      const acs = getComputedStyle(anc);
      if (acs.overflowX !== 'visible') { kind = acs.overflowX; ancDesc = anc.tagName.toLowerCase() + (typeof anc.className === 'string' && anc.className ? '.' + anc.className.trim().split(/\\s+/).slice(0, 2).join('.') : ''); break; }
      anc = anc.parentElement;
    }
    if (kind === 'document')
      rows.push({ d: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + String(el.className).trim().split(/\\s+/).slice(0, 4).join('.') : '') + (cs.visibility === 'hidden' ? ' [vis:hidden]' : '') + (cs.opacity === '0' ? ' [op:0]' : ''), right: Math.round(r.right), w: Math.round(r.w || r.width), top: Math.round(r.top), style: (el.getAttribute('style') || '').slice(0, 70) });
  }
  rows.sort((a, b) => b.right - a.right);
  return rows.slice(0, 12);
}"""
JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const out = [];
  let n = el;
  while (n && n !== document.documentElement) {
    const r = n.getBoundingClientRect();
    const cs = getComputedStyle(n);
    out.push({
      tag: n.tagName.toLowerCase() + (n.className && typeof n.className === 'string' ? '.' + String(n.className).trim().split(/\\s+/).join('.') : ''),
      style: n.getAttribute('style') || '',
      left: Math.round(r.left), w: Math.round(r.width), right: Math.round(r.right),
      disp: cs.display + '|' + cs.position,
      oflow: cs.overflowX, minw: cs.minWidth, maxw: cs.maxWidth,
      grid: cs.gridTemplateColumns, flex: cs.flex, scrollW: n.scrollWidth, cliW: n.clientWidth
    });
    n = n.parentElement;
  }
  return out;
}"""
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2).new_page()
    pg.goto(url, wait_until="networkidle", timeout=45000)
    if sel == "--census":
        for r in pg.evaluate(JS_CENSUS):
            print(f"DOC right={r['right']} w={r['w']} top={r['top']} {r['d'][:60]}   style={r['style']}")
    else:
        rows = pg.evaluate(JS, sel)
        if rows is None:
            print("selector not found:", sel); sys.exit(1)
        for r in rows:
            print(f"{r['tag'][:70]}")
            print(f"   style={r['style'][:90]}")
            print(f"   box w={r['w']} left={r['left']} right={r['right']} {r['disp']} oflow={r['oflow']} min={r['minw']} max={r['maxw']} grid={r['grid'][:40]} flex={r['flex'][:24]} scrollW={r['scrollW']} cliW={r['cliW']}")
    b.close()