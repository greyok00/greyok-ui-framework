#!/usr/bin/env python3
"""throwaway probe — contrast + computed styles for neo-brutalist pages (not shipped)
usage: probe_brutal.py <url> <mode>
modes:
  wash      — identify elementStack under the top-left wash (x=8,y=140)
  pairs     — contrast report for a fixed list of (selector-experiment) real pairs
  acc       — accent text usages: color+bg+fs+weight for accent-coloured text nodes
"""
import sys, json
from pathlib import Path
from fractions import Fraction

def lum(c):
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c[:3]
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def cr(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

JS = r"""
() => {
  const transp = (s) => !s || /^rgba?\(\s*(0,\s*){3}0(\s*,\s*0)?\s*\)$/.test(s.trim()) || /transparent/.test(s);
  const opaqueMix = (s) => {
    // resolve color-mix with rgb() components when chrome reports it opaque enough
    const pct = s.match(/([\d.]+)%\)/);
    return s;
  };
  const bgOf = (el) => {
    let n = el;
    let steps = 0;
    while (n && steps++ < 30) {
      const cs = getComputedStyle(n);
      const bg = cs.backgroundColor;
      if (bg && !transp(bg) && /^rgba?\(/i.test(bg)) return bg;
      n = n.parentElement;
    }
    // fall back to body-computed page background (solid)
    return getComputedStyle(document.body).backgroundColor;
  };
  const parse = (s) => {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x));
    return p;
  };
  const out = [];
  const all = document.querySelectorAll('[data-theme] *');
  for (const el of all) {
    const kids = Array.from(el.childNodes).filter(n => n.nodeType === 3 && n.textContent.trim());
    if (!kids.length) continue;
    const cs = getComputedStyle(el);
    const col = cs.color;
    const fs = parseFloat(cs.fontSize), fw = cs.fontWeight;
    const bgRaw = fs >= 0 ? bgOf(el) : null;
    const b = parse(bgRaw);
    if (!b) continue;
    out.push({cls: (el.className||'').toString().slice(0,60), color: col, bg: b.slice(0,3).join(','), fs, fw, text: (el.textContent||'').trim().slice(0,30), owner: bgOf.last && bgOf.last === el});
  }
  return out;
}
"""

WASH_JS = r"""
({x, y}) => {
  const stack = document.elementsFromPoint(x, y);
  return stack.slice(0, 8).map(el => {
    const cs = getComputedStyle(el);
    return {tag: el.tagName, cls: (el.className||'').toString().slice(0,70),
            bg: cs.backgroundColor, bgImage: cs.backgroundImage.slice(0,120),
            pos: cs.position, pseudo: '', z: cs.zIndex};
  });
}
"""

def main():
    url, mode = sys.argv[1], sys.argv[2]
    from patchright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page.goto(url, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(700)
    if mode == "wash":
        out = page.evaluate(WASH_JS, {"x": 8, "y": 140})
        print(json.dumps(out, indent=1))
        out2 = page.evaluate(WASH_JS, {"x": 4, "y": 300})
        print("--- deeper x=4 y=300")
        print(json.dumps(out2, indent=1))
    else:
        rows = page.evaluate(JS)
        seen = set(); bad = []; counted = 0
        for t in rows:
            try:
                fg = parse_col(t['color']); bg = [float(x) for x in t['bg'].split(',')[:3]]
                counted += 1
                ratio = cr(fg, bg)
            except Exception:
                continue
            big = t['fs'] >= 23.99 or (t['fw'] in ('bold','700','800','900') and t['fs'] >= 18.667)
            need = 3.0 if big else 4.5
            if ratio < need:
                bad.append({**t, 'ratio': round(ratio, 2), 'need': need})
        uniq = []
        for b in bad:
            k = (b['cls'], b['color'], b['fs'], b['text'], b['bg'])
            if k in seen: continue
            seen.add(k); uniq.append(b)
        for b in uniq[:60]:
            print(f"{b['ratio']:>5} <{b['cls'] or '∅'}> fs{b['fs']:.0f}/{b['fw']} fg{b['color']} bg{b['bg']} :: {b['text'][:38]!r}")
        print("evaluated:", counted, "| bad pairs:", len(bad), "| unique:", len(uniq))
    browser.close(); pw.stop()

def parse_col(s):
    import re
    m = re.match(r'rgba?\(([^)]+)\)', s)
    p = [float(x) for x in m.group(1).split(',')[:3]]
    return p

if __name__ == "__main__":
    main()