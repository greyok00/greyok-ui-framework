#!/usr/bin/env python3
"""tools/check_sites.py — prove every theme's demo site uses EVERY inventory element.

Contract: docs/INVENTORY.md. For each slug with a site at demo/sites/<slug>/,
all *.html pages concatenated must mark up every `.el-*` class the contract
lists at least once. Structural slots (nav/hero/card/table variants) are the
persona layer, reviewed by eye; element-class coverage is the hard proof here.

Run: python3 tools/check_sites.py [slug ...]    (default: all built sites)
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "docs" / "INVENTORY.md"
SITES = ROOT / "demo" / "sites"


def required_classes() -> set:
    text = INVENTORY.read_text()
    # the "Files (v0.4 target)" tail lists filenames, not classes — drop it
    text = text.split("## Files (v0.4 target)")[0]
    return set(re.findall(r"\.el-[a-z0-9-]+", text))


def main() -> int:
    wanted = [a for a in sys.argv[1:] if a not in ("--slug", "--slug-mode")]
    classes = required_classes()
    dirs = sorted(d for d in SITES.iterdir() if d.is_dir()) if SITES.exists() else []
    if wanted:
        dirs = [d for d in dirs if d.name in wanted]
        missing_dirs = [w for w in wanted if w not in {d.name for d in dirs}]
        if missing_dirs:
            print("sites: ✗ no site dir for", missing_dirs, file=sys.stderr)
            return 1
    if not dirs:
        print("sites: ✗ no sites built yet under demo/sites/", file=sys.stderr)
        return 1
    problems = []
    for d in dirs:
        pages = sorted(d.glob("*.html"))
        if not pages:
            problems.append(f"{d.name}: no pages")
            continue
        html = " ".join(p.read_text() for p in pages)
        have = {t for c in re.findall(r'class="([^"]+)"', html) for t in re.findall(r"[\w-]+", c)}
        missing = sorted(c.lstrip(".") for c in classes if c.lstrip(".") not in have)
        if missing:
            problems.append(f"{d.name}: missing elements ({len(missing)}): {' '.join(missing)}")
        else:
            print(f"sites: ✓ {d.name} covers all {len(classes)} elements across {len(pages)} pages")
    if problems:
        for p in problems:
            print("sites: ✗", p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())