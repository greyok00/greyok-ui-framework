#!/usr/bin/env python3
"""probe_brutal_mobile.py — mobile ladder probe for brutal-stamp + brutal-index.
Per page x width: hscroll, overflow offenders (excluding real scroll containers),
sub-44px touch targets, clipped text (scrollWidth>clientWidth), tab sequence.
Usage: probe_brutal_mobile.py [site1 site2 ...] [--w 430,390,360,768] [--tabs 2]
"""
import sys, json
from pathlib import Path

SITES = sys.argv[1:] or ["brutal-stamp", "brutal-index"]
WIDTHS = [430, 390, 360, 768]
RUNG_H = {430: 932, 390: 844, 360: 800, 768: 1024}
PAGES = ["index", "article", "catalog", "account", "app"]
TAB_PAGES = []  # filled below (--tabs site:page)
args = []
for a in SITES:
    if a.startswith("--w="):
        WIDTHS = [int(x) for x in a[4:].split(",")]
    elif a.startswith("--tabs="):
        TAB_PAGES.append(a[7:])
    else:
        args.append(a)
if args:
    SITES = args

SEL = "a[href], button, [role='button'], [role='tab'], [role='menuitem'], input, select, textarea, summary, .el-listbox-row, .el-tabbar-item, .el-tab, [tabindex]:not([tabindex='-1'])"

def desc(el):
    try:
        h = el.evaluate("e => e.tagName.toLowerCase() + (e.id ? '#'+e.id : '') + (e.className && typeof e.className==='string' ? '.'+e.className.trim().split(/\\s+/).slice(0,3).join('.') : '')")
        return h[:110]
    except Exception:
        return "?"

JS_OFFENDERS = """() => {
  const vw = document.documentElement.clientWidth;
  const out = [];
  const all = document.querySelectorAll('*');
  for (const el of all) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (r.right > vw + 1.5 || r.left < -1.5) {
      // skip if the element itself is an intended scroll container
      if (/(auto|scroll)/.test(cs.overflowX)) continue;
      let skip = false, p = el.parentElement;
      while (p && p !== document.body) {
        const pcs = getComputedStyle(p);
        if (/auto|scroll|hidden|clip/.test(pcs.overflowX) && p.scrollWidth <= p.clientWidth + 2) { skip = true; break; }
        p = p.parentElement;
      }
      if (skip) continue;
      out.push({d: (el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + String(el.className).trim().split(/\\s+/).slice(0,4).join('.') : '')), left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width), top: Math.round(r.top)});
    }
  }
  out.sort((a, b) => b.right - a.right);
  const seen = new Set(), ded = [];
  for (const o of out) { if (seen.has(o.d + o.right)) continue; seen.add(o.d + o.right); ded.push(o); if (ded.length >= 10) break; }
  return ded;
}"""

JS_TINY = """() => {
  const vw = document.documentElement.clientWidth;
  const out = [];
  for (const el of document.querySelectorAll(""" + json.dumps(SEL) + """)) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.pointerEvents === 'none') continue;
    let inWin = true, p = el.parentElement;
    while (p && p !== document.body) { if (getComputedStyle(p).position === 'fixed') inWin = false; p = p.parentElement; }
    if (r.height < 44) out.push({d: (el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + String(el.className).trim().split(/\\s+/).slice(0,4).join('.') : '')), h: +(r.height || 0).toFixed(1)});
  }
  const seen = new Map();
  for (const t of out) { const k = t.d; if (!seen.has(k) || seen.get(k).h > t.h) seen.set(k, t); }
  return Array.from(seen.values()).sort((a, b) => a.h - b.h).slice(0, 14);
}"""

JS_CLIP = """() => {
  const vw = document.documentElement.clientWidth;
  const out = [];
  for (const el of document.querySelectorAll('.el-fact,.el-stat-value,.el-mono,.el-stat-label,.el-badge,.el-chip,.el-status-pill,.el-pt-count,.el-table td,.el-table th,.el-price,.el-plan-price')) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none') continue;
    if (/(hidden|clip)/.test(cs.overflow) || (cs.whiteSpace === 'nowrap')) {
      if (el.scrollWidth > el.clientWidth + 1) out.push({d: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + String(el.className).trim().split(/\\s+/).slice(0,3).join('.') : ''), cut: el.scrollWidth - el.clientWidth, txt: (el.textContent || '').trim().slice(0, 24)});
    }
  }
  return out.slice(0, 10);
}"""

from patchright.sync_api import sync_playwright

def main():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    base = "http://127.0.0.1:8920/demo/sites"
    for site in SITES:
        for page in PAGES:
            url = f"{base}/{site}/{page}.html"
            for w in WIDTHS:
                h = RUNG_H[w]
                ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
                pg = ctx.new_page()
                try:
                    pg.goto(url, wait_until="networkidle", timeout=45000)
                    pg.wait_for_timeout(350)
                    hs = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth + ':' + (document.body.scrollWidth - document.body.clientWidth)")
                    off = pg.evaluate(JS_OFFENDERS)
                    tiny = pg.evaluate(JS_TINY)
                    clip = pg.evaluate(JS_CLIP)
                    flag = []
                    if hs != "0:0": flag.append("HSCROLL=" + hs)
                    if off: flag.append(f"offenders:{len(off)}")
                    if tiny: flag.append(f"tiny:{len(tiny)}")
                    if clip: flag.append(f"clip:{len(clip)}")
                    print(f"[{site}/{page} @{w}] {' '.join(flag) if flag else 'clean'}")
                    if hs != "0:0":
                        print("   hscroll", hs)
                    for o in off[:6]:
                        print(f"   OFF w={o['w']} right={o['right']} top={o['top']} {o['d']}")
                    for t in tiny[:8]:
                        print(f"   TINY h={t['h']} {t['d']}")
                    for c in clip[:6]:
                        print(f"   CLIP cut={c['cut']} {c['d']} '{c['txt']}'")
                    if f"{site}:{page}" in TAB_PAGES and w == 430:
                        seq = []
                        pg.evaluate("document.activeElement && document.activeElement.blur && document.activeElement.blur()")
                        pg.keyboard.press("Tab")
                        for i in range(30):
                            pos = pg.evaluate("() => { const a = document.activeElement; if (!a || a === document.body) return null; const r = a.getBoundingClientRect(); return {d: a.tagName.toLowerCase() + (a.className && typeof a.className === 'string' ? '.' + String(a.className).trim().split(/\\s+/).slice(0,3).join('.') : ''), x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height), txt: (a.textContent || a.getAttribute('aria-label') || '').trim().slice(0, 26), onscreen: (r.left >= -2 && r.right <= document.documentElement.clientWidth + 2)}; }")
                            if pos is None: break
                            seq.append(pos)
                            if i < 29: pg.keyboard.press("Tab")
                        print(f"   TABSEQ({len(seq)}): " + " | ".join(f"{s['d']}@{s['y']}" + ("" if s['onscreen'] else " OFFSCREEN") for s in seq[:30]) if seq else "   TABSEQ: body only")
                except Exception as e:
                    print(f"[{site}/{page} @{w}] PROBE FAIL {type(e).__name__} {e}")
                finally:
                    ctx.close()
    browser.close()
    pw.stop()

if __name__ == "__main__":
    main()