#!/usr/bin/env python3
"""bisect.py <url> <w> — hide top-level+descendant subtrees to find what inflates document scrollWidth."""
import sys
url, w = sys.argv[1], int(sys.argv[2])
from patchright.sync_api import sync_playwright

JS_BISECT = """() => {
  const sc = document.documentElement;
  const base = () => sc.scrollWidth - sc.clientWidth;
  const over = base();
  if (!over) return null;
  // collect candidate hidden/translated elements
  const cands = [];
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.transform !== 'none' || cs.translate !== 'none') cands.push([el, null]);
    if (cs.position === 'fixed' || cs.position === 'sticky') cands.push([el, null]);
    // every element with a rect past vw that isn't inside an overflow container
    let anc = el.parentElement, clipped = false;
    while (anc && anc !== document.documentElement) { if (getComputedStyle(anc).overflowX !== 'visible') { clipped = true; break; } anc = anc.parentElement; }
    if (!clipped && el.getBoundingClientRect().right > document.documentElement.clientWidth) cands.push([el, null]);
  }
  const results = [];
  for (const [el] of cands) {
    const prevD = el.style.display, prevV = el.style.visibility;
    el.style.display = 'none';
    const d = base();
    el.style.display = prevD; el.style.visibility = prevV;
    if (d < over) {
      const r = el.getBoundingClientRect();
      results.push([d, over - d, el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\\s+/).slice(0, 3).join('.') : ''), Math.round(r.left), Math.round(r.right), getComputedStyle(el).position, getComputedStyle(el).transform]);
    }
  }
  results.sort((a, b) => a[0] - b[0]);
  return { over, results: results.slice(0, 10) };
}"""
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    pg = b.new_context(viewport={"width": w, "height": 932}, device_scale_factor=2).new_page()
    pg.goto(url, wait_until="networkidle", timeout=45000)
    data = pg.evaluate(JS_BISECT)
    if not data:
        print("no hscroll at all"); sys.exit(0)
    print("total overflow px:", data["over"])
    for d, gain, name, left, right, pos, tf in data["results"]:
        print(f"  hide->{d} (gains {gain}px) {name} left={left} right={right} pos={pos} tf={tf[:40]}")
    b.close()