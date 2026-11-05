#!/usr/bin/env python3
"""qa/ct-probe.py — throwaway WCAG-contrast sweep for the color/typo pass.
Walks visible text nodes, composites fg over the ancestor background stack,
flags sub-AA pairs. Eyes on renders stay the primary instrument; this is the ruler.
Usage: python3 qa/ct-probe.py <file://url> [limit]
"""
import sys, re

def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(rgb):
    r, g, b = rgb
    return (0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b))

def parse_color(s):
    if not s:
        return None
    s = s.strip()
    m = re.match(r"^rgba?\(([^)]+)\)$", s, re.I)
    if m:
        p = [x for x in re.split(r"[\s,/]+", m.group(1)) if x]
        try:
            if len(p) >= 3:
                comp = [float(p[0]), float(p[1]), float(p[2])]
                if any(x.endswith("%") for x in p[:3]):
                    comp = [v * 2.55 for v in comp]
                a = float(p[3]) if len(p) > 3 else 1.0
                return (comp[0], comp[1], comp[2], a)
        except ValueError:
            return None
        return None
    if s.startswith("#"):
        h = s[1:]
        if len(h) in (4, 5):
            h = "".join(c * 2 for c in h)
        if len(h) in (6, 8):
            r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16)
            a = int(h[6:8], 16) / 255.0 if len(h) == 8 else 1.0
            return (r, g, b, a)
    return None

def over(top, bottom):
    tr, tg, tb, ta = top
    br, bg, bb, ba = bottom
    return (tr * ta + br * (1 - ta), tg * ta + bg * (1 - ta), tb * ta + bb * (1 - ta), 1.0)

def ratio(fg, bg):
    l1 = lum(fg[:3])
    l2 = lum(bg[:3])
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)

def fmt(rgb, a=1.0):
    return "#%02x%02x%02x a%.2f" % (round(rgb[0]), round(rgb[1]), round(rgb[2]), a)

JS = r"""
(() => {
  function parseCssColor(s){
    if(!s) return null;
    s = s.trim();
    const rgba = s.match(/^rgba?\(([^)]+)\)$/i);
    if(rgba){
      const p = rgba[1].split(/[\s,\/]+/).filter(Boolean);
      let r,g,b,a=1;
      if(p[0] && p[0].endsWith('%')){
        r=parseFloat(p[0])*2.55; g=parseFloat(p[1]||'0')*2.55; b=parseFloat(p[2]||'0')*2.55;
        if(p[3]!==undefined) a=parseFloat(p[3]);
      } else {
        r=parseFloat(p[0]); g=parseFloat(p[1]!==undefined?p[1]:'0'); b=parseFloat(p[2]!==undefined?p[2]:'0');
        if(p[3]!==undefined) a=parseFloat(p[3]);
      }
      if(isNaN(r)) r=0;
      if(isNaN(g)) g=0;
      if(isNaN(b)) b=0;
      if(isNaN(a)) a=1;
      return [r,g,b,a];
    }
    const hex = s.match(/^#([0-9a-f]{3,8})$/i);
    if(hex){
      let h = hex[1];
      if(h.length===3||h.length===4) h = h.split('').map(c=>c+c).join('');
      if(h.length===6||h.length===8){
        return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16),
                h.length===8?parseInt(h.slice(6,8),16)/255:1];
      }
    }
    return null;
  }
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  let n;
  while ((n = walker.nextNode())) {
    const txt = n.textContent.trim();
    if (!txt) continue;
    const el = n.parentElement;
    if (!el || seen.has(el)) continue;
    seen.add(el);
    const cs = getComputedStyle(el);
    const isSvg = el.namespaceURI === "http://www.w3.org/2000/svg" ||
      !!el.closest("svg, style, script, head, defs");
    if (el.closest("defs")) continue;
    const r = el.getBoundingClientRect();
    const vis = cs.visibility !== "hidden" && cs.display !== "none" &&
      parseFloat(cs.opacity) > 0.02 && r.width > 2 && r.height > 2 && el.getClientRects().length > 0;
    if (!vis) continue;
    const stack = [];
    let cur = el, depth = 0;
    while (cur && depth < 14) {
      const c = getComputedStyle(cur);
      const bgl = parseCssColor(c.backgroundColor || "");
      if (bgl && bgl[3] > 0) {
        stack.push(bgl);
        if (bgl[3] >= 0.999) break;
      }
      cur = cur.parentElement;
      depth++;
    }
    out.push({
      text: txt.slice(0, 50),
      color: isSvg ? cs.fill : cs.color,
      bgStack: stack,
      fontSize: parseFloat(cs.fontSize),
      weight: cs.fontWeight,
      op: cs.opacity,
      cls: (typeof el.className === "string" ? el.className : String(el.className.baseVal || "")).slice(0, 40),
      y: Math.round(r.top), x: Math.round(r.left)
    });
  }
  return out;
})()
"""

def probe_main():
    url = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 55
    from patchright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(900)
    rows = page.evaluate(JS)
    page_bg = parse_color(page.evaluate("getComputedStyle(document.body).backgroundColor")) or (14, 14, 16, 1)
    findings = []
    for r in rows:
        fg = parse_color(r["color"])
        if not fg:
            continue
        bg = page_bg
        for layer in r["bgStack"][::-1]:
            bg = over(layer, bg)
        op = float(r["op"]) if r["op"] else 1.0
        fa = fg[3] * op
        r_ = ratio((fg[0], fg[1], fg[2], fa), bg)
        size = r["fontSize"]
        bold = r["weight"] in ("bold", "600", "700", "800", "900")
        large = size >= 24 or (size >= 18.66 and bold)
        need = 3.0 if large else 4.5
        if r_ < need:
            findings.append((r_, need, r, bg, fa, fg))
    findings.sort(key=lambda f: f[0])
    for f in findings[:limit]:
        r_, need, r, bg, fa, fg = f
        print("%4.2f<%.1f %-5s %4.0fpx w%-3s | fg %s | bg %s | y%-5d %-14s | %r" % (
            r_, need, "LARGE" if need == 3.0 else "body",
            r["fontSize"], r["weight"],
            fmt((fg[0], fg[1], fg[2]), fa),
            fmt(bg[:3]),
            r["y"], (r["cls"] or "")[:14],
            r["text"][:46]))
    print("--- findings:", len(findings), "/", len(rows), "text nodes,", "| body bg:", fmt(page_bg[:3]))
    browser.close(); pw.stop()

probe_main()