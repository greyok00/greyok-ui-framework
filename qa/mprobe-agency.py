#!/usr/bin/env python3
"""qa/mprobe-agency.py — mobile-rung probe for the v0.4.0 mobile pass (agency-classic).

Usage: python3 qa/mprobe-agency.py <slug> <page.html>... [--rungs 430:932,360:800,768:1024]
       [--dpr 2] [--shots] [--nojs] [--tab] [--max 12]

Per page x rung measures, via live DOM walks:
  - document-level horizontal scroll (the hard gate: none may h-scroll)
  - elements whose bbox crosses the viewport edge (the overflow offenders)
  - interactive elements shorter than 44px (touch-target gate, 430 rung)
  - tab-order walkthrough (--tab): first 24 activeElement stops
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNGS = [(430, 932), (360, 800), (768, 1024)]

JS_OFFENDERS = """() => {
  const w = document.documentElement.clientWidth;
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.visibility !== 'visible' || cs.display === 'none') continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right > w + 0.5 || r.left < -0.5) {
      const s = el.getAttribute('class') || '';
      const cls = ('el-' + s.trim().split(/\\s+/).slice(0,2).join('.el-')) || el.tagName.toLowerCase();
      out.push({t: el.tagName.toLowerCase(), c: cls.slice(0, 64),
                left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width)});
    }
  }
  return out;
}"""

JS_TOUCH = """() => {
  const sel = 'a, button, [role=tab], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  const bad = [];
  const seen = new Set();
  for (const el of document.querySelectorAll(sel)) {
    const cs = getComputedStyle(el);
    if (cs.visibility !== 'visible' || cs.display === 'none' || cs.pointerEvents === 'none') continue;
    let surface = el;
    if (parseFloat(cs.opacity) === 0) {
      // invisible native checkbox/radio: HTML forwards label taps, so the
      // effective tap surface is the nearest <label> row; without a label the
      // drawn box it overlays is the only surface there is
      surface = el.closest('label') || el;
      if (getComputedStyle(surface).pointerEvents === 'none' ||
          getComputedStyle(surface).visibility !== 'visible') continue;
    }
    const r = surface.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.height < 43.5 && surface.offsetParent !== null) {
      const label = (surface.innerText || surface.getAttribute('aria-label') || surface.value || '').trim().slice(0, 24);
      const key = (surface.getAttribute('class') || surface.tagName.toLowerCase()).split(' ').slice(0, 2).join(' ') + '@' + Math.round(r.height);
      if (seen.has(key)) continue;
      seen.add(key);
      bad.push({c: (surface.getAttribute('class') || surface.tagName.toLowerCase()).split(' ').slice(0, 2).join(' '),
                h: Math.round(r.height), l: label});
    }
  }
  return bad;
}"""

def walk(page, label, max_offenders=12):
    h = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    body_h = page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
    off = page.evaluate(JS_OFFENDERS)
    dedup = []
    for o in off:
        key = (o["c"], o["t"])
        if not any(d["c"] == key[0] and d["t"] == key[1] for d in dedup):
            dedup.append(o)
    res = {"page": label, "w": page.viewport_size["width"],
           "hscroll": h, "pageH": body_h, "offenderKinds": dedup[:max_offenders], "offenderN": len(off)}
    return res

def main():
    args = sys.argv[1:]
    slugs = []
    pages = []
    rungs = RUNGS
    dpr = 2
    shots = nojs = tabwalk = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--rungs":
            rungs = [tuple(int(x) for x in r.split(":")) for r in args[i+1].split(",")]; i += 2
        elif a == "--dpr": dpr = float(args[i+1]); i += 2
        elif a == "--shots": shots = True; i += 1
        elif a == "--nojs": nojs = True; i += 1
        elif a == "--tab": tabwalk = True; i += 1
        elif a == "--max": max_o = int(args[i+1]); i += 2
        elif a.startswith("qa/"): i += 1  # ignore
        else:
            p = Path(a)
            if p.suffix == ".html": pages.append(p)
            else: slugs.append(a)
            i += 1
    if slugs and not pages:
        for s in slugs:
            pages += sorted((ROOT / "demo/sites" / s).glob("*.html"))
    from patchright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    ctx_opts = {"device_scale_factor": dpr}
    page = browser.new_page(viewport={"width": rungs[0][0], "height": rungs[0][1]}, **ctx_opts)
    out = []
    for p in pages:
        url = f"http://127.0.0.1:8920/demo/sites/{p.parent.name}/{p.name}"
        for (w, hh) in rungs:
            page.set_viewport_size({"width": w, "height": hh})
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(500)
            r = walk(page, f"{p.parent.name}/{p.stem}", 12)
            r["nojs"] = False
            if shots:
                q = Path(f"qa/sites/{p.parent.name}/m-{p.stem}-{w}.png")
                q.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(q), full_page=True)
            if tabwalk and w == 430:
                stops = page.evaluate(JS_TABWALK) if False else None
                stops = None
                seq = []
                page.keyboard.press("Tab")
                for k in range(24):
                    ae = page.evaluate(
                        "() => { const e = document.activeElement; if (!e || e === document.body) return null;"
                        " const r = e.getBoundingClientRect();"
                        " let path = e.tagName.toLowerCase();"
                        " if (e.id) path += '#' + e.id;"
                        " else if (typeof e.className === 'string' && e.className) path += '.' + e.className.trim().split(/\\s+/).slice(0,2).join('.');"
                        " return path.slice(0,64) + ' @' + Math.round(r.left) + ',' + Math.round(r.top); }")
                    if ae is None:
                        seq.append("(body)")
                        break
                    seq.append(ae)
                    page.keyboard.press("Tab")
                r["tabstops"] = seq
            if w == 430 and not nojs:
                r["touch"] = page.evaluate(JS_TOUCH)
            if nojs:
                r["nojs"] = True
            out.append(r)
            print(json.dumps(r), flush=True)
    browser.close(); pw.stop()

if __name__ == "__main__":
    main()