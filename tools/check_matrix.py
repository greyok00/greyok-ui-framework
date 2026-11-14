#!/usr/bin/env python3
"""tools/check_matrix.py - verify the theme x layout matrix.

Two jobs:

1. Compatibility: every theme over every layout, at desktop (1440) and
   mobile (390) width, must render with no horizontal overflow and no page
   errors. 20 themes x 20 layouts = 400 combinations per mode.

2. Uniqueness: each layout must have a distinct structural fingerprint in
   each mode. The fingerprint is the normalized geometry of the main
   column's direct children (x, y, width as fractions), theme-independent,
   so two layouts that merely re-skin the same page are caught.

Usage:
  python3 tools/check_matrix.py                     # full matrix
  python3 tools/check_matrix.py --mode desktop
  python3 tools/check_matrix.py --layouts bento-dashboard,magazine-grid
  python3 tools/check_matrix.py --json out.json
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "demo" / "layouts"

GEOM_JS = """
() => {
  const main = document.querySelector('main.site-main') || document.querySelector('main');
  const doc = document.documentElement;
  const boxes = [];
  if (main) {
    const mr = main.getBoundingClientRect();
    const mw = mr.width || 1, mh = Math.max(mr.height, 1);
    for (const el of main.children) {
      const r = el.getBoundingClientRect();
      if (r.height < 3) continue;
      boxes.push([
        Math.round((r.left - mr.left) / mw * 100) / 100,
        Math.round((r.top - mr.top) / mh * 100) / 100,
        Math.round(r.width / mw * 100) / 100
      ]);
    }
  }
  const cs = main ? getComputedStyle(main) : null;
  const struct = main ? {
    display: cs.display,
    cols: cs.gridTemplateColumns && cs.gridTemplateColumns !== 'none'
          ? cs.gridTemplateColumns.split(' ').length : 0,
    flow: cs.flexDirection || '',
    kids: [...main.children].map(el => {
      const k = getComputedStyle(el);
      return [k.gridColumnStart, k.gridColumnEnd, k.gridRowStart, k.order].join('/');
    }).join(';')
  } : null;
  return {
    overflow: doc.scrollWidth > doc.clientWidth + 2,
    scrollW: doc.scrollWidth, clientW: doc.clientWidth,
    boxes, struct,
    display: cs ? cs.display : null,
    cols: cs ? cs.gridTemplateColumns : null
  };
}
"""


def themes() -> list[str]:
    js = (ROOT / "theme-switcher.js").read_text()
    block = re.search(r"const THEMES = \[(.*?)\];", js, re.S).group(1)
    return [s for s in re.findall(r"'([a-z0-9-]+)'", block) if s != "neutral"]


def layouts() -> list[str]:
    return sorted(p.stem for p in PAGES.glob("*.html"))


MOBILE = ['m-stack', 'm-bottom-tabs', 'm-sticky-header', 'm-full-cover',
          'm-stats-first', 'm-two-up', 'm-carousel', 'm-swipe-lanes',
          'm-list-rows', 'm-timeline', 'm-chip-index', 'm-media-first',
          'm-hero-band', 'm-pricing-stack', 'm-masonry-2', 'm-boxed',
          'm-overlap', 'm-zen', 'm-atlas', 'm-scroll-sections']


def fingerprint(boxes) -> str:
    return "|".join(f"{x:.2f},{y:.2f},{w:.2f}" for x, y, w in boxes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("desktop", "mobile", "both"), default="both")
    ap.add_argument("--layouts", help="comma list")
    ap.add_argument("--themes", help="comma list")
    ap.add_argument("--json")
    ap.add_argument("--shots", help="directory for one PNG per combo")
    args = ap.parse_args()

    lays = args.layouts.split(",") if args.layouts else layouts()
    ths = args.themes.split(",") if args.themes else themes()
    modes = [("desktop", 1440, 900), ("mobile", 390, 844)]
    if args.mode != "both":
        modes = [m for m in modes if m[0] == args.mode]

    from patchright.sync_api import sync_playwright

    results = {"modes": {}, "themes": ths, "layouts": lays}
    failures = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for mode, w, h in modes:
            page.set_viewport_size({"width": w, "height": h})
            mode_out = {"combos": 0, "overflow": [], "pageerrors": [], "by_layout": {}}
            if mode == "mobile":
                # a phone layout is selected per page; the page itself is a
                # desktop specimen that carries the mobile attribute
                work = [(m, "split-hero-left", m) for m in MOBILE]
            else:
                work = [(slug, slug, None) for slug in lays]
            for label, page_slug, mobile in work:
                url = (PAGES / f"{page_slug}.html").resolve().as_uri()
                prints = {}
                structs = {}
                for theme in ths:
                    errors.clear()
                    q = f"?theme={theme}" + (f"&mobile={mobile}" if mobile else "")
                    page.goto(f"{url}{q}", wait_until="load")
                    page.wait_for_timeout(60)
                    geom = page.evaluate(GEOM_JS)
                    mode_out["combos"] += 1
                    if geom["overflow"]:
                        mode_out["overflow"].append(f"{label}/{theme}")
                    if errors:
                        mode_out["pageerrors"].append(f"{label}/{theme}: {errors[0]}")
                    prints[theme] = fingerprint(geom["boxes"])
                    structs[theme] = json.dumps(geom["struct"], sort_keys=True)
                    if args.shots:
                        out = Path(args.shots) / mode / f"{label}__{theme}.png"
                        out.parent.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(out), full_page=True)
                # structure is theme-independent; group by the neutral print
                mode_out["by_layout"][label] = {
                    "boxes": len(prints[ths[0]].split("|")),
                    "signature": prints[ths[0]],
                    "theme_varies": len(set(structs.values())) > 1,
                }
            # uniqueness: group identical signatures
            groups = {}
            for slug, d in mode_out["by_layout"].items():
                groups.setdefault(d["signature"], []).append(slug)
            dupes = {k: v for k, v in groups.items() if len(v) > 1}
            mode_out["duplicate_layouts"] = list(dupes.values())
            mode_out["distinct_layouts"] = len(groups)
            failures += len(mode_out["overflow"]) + len(mode_out["pageerrors"])
            results["modes"][mode] = {
                "combos": mode_out["combos"],
                "overflow": mode_out["overflow"],
                "pageerrors": mode_out["pageerrors"],
                "distinct_layouts": mode_out["distinct_layouts"],
                "duplicate_layouts": mode_out["duplicate_layouts"],
                "by_layout": mode_out["by_layout"],
            }
            print(f"[{mode}] {mode_out['combos']} combos, "
                  f"{len(mode_out['overflow'])} overflow, "
                  f"{len(mode_out['pageerrors'])} page errors, "
                  f"{mode_out['distinct_layouts']}/{len(lays)} distinct layouts")
            for group in mode_out["duplicate_layouts"]:
                print(f"  duplicate structure: {', '.join(group)}")
        browser.close()

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2))
        print(f"wrote {args.json}")
    return 1 if failures or any(
        results["modes"][m]["duplicate_layouts"] for m in results["modes"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
