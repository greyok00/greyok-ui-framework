#!/usr/bin/env python3
"""qa/m-probe.py — mobile-pass probe: overflow, h-scroll, touch targets, focus order.
Usage: python3 qa/m-probe.py <url> <w> <h> [dpr] [--tabs N]
Reports per page: client width vs scroll width (horizontal-scroll check), elements
whose right edge passes the client width, interactive elements shorter than 44px,
and optionally the sequential-focus-navigation order (--tabs).
"""
import sys

JS_H = r"""
(() => {
  const doc = document.documentElement;
  const cw = doc.clientWidth, sw = doc.scrollWidth;
  const out = {cw, sw, hscroll: sw > cw, wide: [], small: []};
  for (const e of document.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width > 0 && r.right > cw + 0.6) {
      const sel = e.tagName.toLowerCase()
        + (e.classList.length ? '.' + Array.from(e.classList).slice(0,2).join('.') : '');
      out.wide.push(sel + '×' + Math.round(r.right - cw));
      if (out.wide.length > 12) break;
    }
  }
  const inter = document.querySelectorAll(
    'a[href],button,input,select,textarea,summary,[role="button"],[role="tab"],[role="switch"]');
  const seen = new Set();
  for (const e of inter) {
    const r = e.getBoundingClientRect();
    const st = getComputedStyle(e);
    if (st.display === 'none' || st.visibility === 'hidden' || r.width === 0) continue;
    let box = e;
    const lbl = e.closest('label');
    if (lbl) { const lr = lbl.getBoundingClientRect(); if (lr.height > r.height) box = lbl; }
    const h = box.getBoundingClientRect().height;
    if (h < 43.5) {
      const sel = box.tagName.toLowerCase()
        + (box.classList.length ? '.' + Array.from(box.classList).slice(0,2).join('.') : '')
        + '=' + Math.round(h) + 'px';
      const key = sel + '|' + e.textContent.trim().slice(0,14);
      if (!seen.has(key)) { out.small.push(key); seen.add(key); }
      if (out.small.length > 18) break;
    }
  }
  return out;
})()
"""

JS_WALKFOCUS = r"""
(async (n) => {
  const isFocusable = (e) => {
    if (e.disabled || e.hidden || e.getAttribute('aria-hidden') === 'true') return false;
    const st = getComputedStyle(e);
    if (st.display === 'none' || st.visibility === 'hidden') return false;
    const tag = e.tagName.toLowerCase();
    const native = ['a','button','input','select','textarea','summary','iframe'].includes(tag)
      && (tag !== 'a' || e.hasAttribute('href'));
    const t = e.getAttribute('tabindex');
    if (t !== null) return parseInt(t) >= 0;
    return native || e.isContentEditable;
  };
  const all = Array.from(document.querySelectorAll('*')).filter(isFocusable)
    .filter(e => { const r = e.getBoundingClientRect(); return r.width || r.height; });
  // tabindex=1.. groups first, then tabindex=0 in document order
  const sorted = all.sort((a, b) => {
    const ta = parseInt(a.getAttribute('tabindex') ?? '0');
    const tb = parseInt(b.getAttribute('tabindex') ?? '0');
    return ta === tb
      ? (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1)
      : ta - tb;
  });
  // flag anything whose resting box lies outside the client width (focus invisible)
  const cw = document.documentElement.clientWidth;
  return sorted.slice(0, n).map(e => {
    const r = e.getBoundingClientRect();
    const off = r.left < -1 || r.right > cw + 1;
    const sel = e.tagName.toLowerCase() + (e.id ? '#' + e.id
      : (e.classList.length ? '.' + Array.from(e.classList).slice(0,2).join('.') : ''));
    return sel + (off ? '[OFF]' : '');
  });
})
"""


def open_page(url, w, h, dpr, nojs=False):
    from patchright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=dpr,
                            java_script_enabled=not nojs)
    if nojs:
        page.route("**/*", lambda r: r.abort() if r.request.resource_type == "script" else r.continue_())
    page.goto(url, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(600)
    return pw, browser, page


def probe(url, w, h, dpr):
    pw = browser = page = None
    try:
        pw, browser, page = open_page(url, w, h, dpr)
        d = page.evaluate(JS_H)
        name = url.rsplit('/', 1)[-1]
        print(f"== {name} @ {w}x{h}")
        print(f"   client={d['cw']} scrollW={d['sw']} hscroll={d['hscroll']}")
        if d["wide"]:
            print("   wide:", " ".join(d["wide"][:12]))
        if d["small"]:
            print(f"   small(<44px) x{len(d['small'])}:", "; ".join(d["small"][:14]))
    except Exception as e:
        print("   probe failed:", type(e).__name__, e)
        return False
    finally:
        if page is not None:
            try: browser.close()
            except Exception: pass
            try: pw.stop()
            except Exception: pass
    return True


def walk(url, w, h, tabs):
    pw = browser = page = None
    try:
        pw, browser, page = open_page(url, w, h, 2)
        seq = page.evaluate(JS_WALKFOCUS, tabs)
        print("   focus-order[:%d]:" % tabs, " -> ".join(seq))
    finally:
        if page is not None:
            try: browser.close()
            except Exception: pass
            try: pw.stop()
            except Exception: pass


def shoot(url, out, w, h, dpr):
    """full-page audit render (whole page, not the viewport crop)"""
    from pathlib import Path
    pw, browser, page = open_page(url, w, h, dpr)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=out, full_page=True)
    d = page.evaluate(JS_H)
    print(f"shot {out} | hscroll={d['hscroll']} scrollW={d['sw']}")
    browser.close(); pw.stop()


def main():
    url, w, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    args = sys.argv[4:]
    if "--shot" in args:
        shoot(url, args[args.index("--shot") + 1], w, h, 1)
        return 0
    dpr = 1
    nums = [a for a in args if not a.startswith("--")]
    if nums:
        dpr = float(nums[0])
    tabs = int(args[args.index("--tabs") + 1]) if "--tabs" in args else 0
    if not probe(url, w, h, dpr):
        return 2
    if tabs:
        walk(url, w, h, tabs)
    return 0


if __name__ == "__main__":
    sys.exit(main())