#!/usr/bin/env python3
"""tools/render_shots.py — render repo screenshots from the demo pages.

One browser pass, three jobs:
  posters    demo/sites/<slug>/index.html -> demo/posters/<slug>.png
             (full page, 1440 CSS px wide, the wall image on the README)
  showcase   demo/index.html -> docs/screenshots/showcase.png (viewport 1440x1250)
  layouts    demo/layout-previews/*.png already exist; this only re-shoots them
             when asked, using the same browser so the sizes match.

Everything runs from file:// so no server is needed. Fonts are awaited before
the shot; a short settle keeps lazy images in place.

Usage:
  python3 tools/render_shots.py --posters            # all sites
  python3 tools/render_shots.py --posters --slug herald
  python3 tools/render_shots.py --showcase
  python3 tools/render_shots.py --viewport docs/screenshots/phone-430.png \
      --width 430 --height 932 --page demo/index.html
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITES = ROOT / "demo" / "sites"
POSTERS = ROOT / "demo" / "posters"


def _page_url(path: Path) -> str:
    return path.resolve().as_uri()


def _shot(page, url: str, out: Path, width: int, height: int,
          full_page: bool, settle: int = 600, click: str | None = None) -> None:
    page.set_viewport_size({"width": width, "height": height})
    page.goto(url, wait_until="load")
    page.wait_for_timeout(settle)
    if click:
        page.click(click)
        page.wait_for_timeout(400)
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(200)
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=full_page)
    print(f"shot {out.relative_to(ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--posters", action="store_true")
    ap.add_argument("--showcase", action="store_true")
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--page")
    ap.add_argument("--viewport")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--click", help="CSS selector to click before the shot")
    args = ap.parse_args()

    jobs: list[tuple[str, Path, int, int, bool, str | None]] = []
    if args.posters:
        slugs = args.slug or sorted(p.name for p in SITES.iterdir() if p.is_dir())
        for slug in slugs:
            src = SITES / slug / "index.html"
            if not src.exists():
                print(f"skip {slug}: no index.html", file=sys.stderr)
                continue
            jobs.append((_page_url(src), POSTERS / f"{slug}.png", 1440, 900, True, None))
    if args.showcase:
        jobs.append((_page_url(ROOT / "demo" / "index.html"),
                     ROOT / "docs" / "screenshots" / "showcase.png",
                     1440, 1250, False, None))
    if args.viewport:
        page_ref = args.page or "demo/index.html"
        page_path, _, query = page_ref.partition("?")
        url = _page_url(ROOT / page_path) + (("?" + query) if query else "")
        jobs.append((url, ROOT / args.viewport,
                     args.width, args.height, False, args.click))
    if not jobs:
        ap.error("nothing to do: pick --posters, --showcase, or --viewport")

    from patchright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        for url, out, w, h, full, click in jobs:
            _shot(page, url, out, w, h, full, click=click)
        browser.close()
    print(f"{len(jobs)} shot(s) written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
