#!/usr/bin/env python3
"""tools/build_layouts.py - assemble the 20 layout archetypes into layouts.css.

The archetypes are authored in the studio's site emitter (pipeline/site.py,
_LAYOUT_KITS_CSS) because that is where they are exercised against real pages.
This tool copies that kit sheet into the framework, renames the two
emitter-only hooks to public ones, and minifies:

    main.site-main  ->  main.el-main
    .card-grid      ->  .el-card-grid

A layout is structure only: it re-orders the home blocks a page already has
(el-hero, el-section, el-stat-row, el-card-grid, el-issue-index, el-disclaimer)
and never paints anything, so every theme still matches every layout. Two
independent axes ship here: 20 desktop kits (data-layout) and 20 phone kits
(data-layout-mobile, <=700px).

Run: python3 tools/build_layouts.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "layouts.css"
STUDIO = Path(os.environ.get("GREYOK_STUDIO")
              or Path.home() / "webstudioai" / "studio")

BASE = """main.el-main{padding:0 0 56px;line-height:1.6}
.el-card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:var(--el-space-4)}
[data-layout] main.el-main>*{grid-column:1/-1}
@media (max-width:1080px){.el-navbar{flex-wrap:wrap;row-gap:var(--el-space-1,4px)}}
"""


def minify(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)
    return css.strip()


def main() -> int:
    sys.path.insert(0, str(STUDIO))
    from pipeline import site

    kits = site._LAYOUT_KITS_CSS + site.LAYOUT_MOBILE_CSS
    kits = kits.replace("main.site-main", "main.el-main")
    kits = kits.replace(".card-grid", ".el-card-grid")
    css = BASE + kits
    if css.count("{") != css.count("}"):
        print("build: unbalanced braces in layout kits", file=sys.stderr)
        return 1
    OUT.write_text(minify(css), encoding="utf-8")
    slugs = sorted(set(re.findall(r'\[data-layout="([a-z-]+)"\]', css)))
    print(f"layouts.css: {OUT.stat().st_size} bytes, {len(slugs)} layouts")
    print(" ".join(slugs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
