#!/usr/bin/env python3
"""qa/sheet.py — controller-only contact sheets from qa/final dpr1 proofs.
Usage: sheet.py <out_prefix> [slug1 slug2 ...]  (default: v3 roster order)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROSTER = ["mono-console", "ghost-terminal", "cream-journal", "paper-press",
          "brutal-stamp", "brutal-index", "orbit-deep", "solar-halo",
          "agency-quartz", "agency-mono-plate", "maison-serif", "noir-couture",
          "sticker-pop", "sketchbook", "console-light", "grid-ledger",
          "kinetic-ink", "aperture-motion", "ma-quiet", "gesshoku"]

REPO = Path(__file__).resolve().parents[1]
FINAL = REPO / "qa" / "final"
COLS, TH_W = 5, 560


def main():
    out_prefix = sys.argv[1]
    slugs = sys.argv[2:] or ROSTER
    cells = []
    for slug in slugs:
        p = FINAL / f"{slug}.png"
        if not p.exists():
            print(f"MISSING {slug}")
            continue
        img = Image.open(p)
        s = TH_W / img.width
        cells.append((slug, img.resize((TH_W, round(img.height * s)), Image.LANCZOS)))
    rows = (len(cells) + COLS - 1) // COLS
    row_h = (max(c[1].height for c in cells) + 28) if cells else 1
    sheet = Image.new("RGB", (COLS * (TH_W + 12) + 12, rows * row_h), "#222")
    d = ImageDraw.Draw(sheet)
    for i, (slug, im) in enumerate(cells):
        x = 12 + (i % COLS) * (TH_W + 12)
        y = 12 + (i // COLS) * row_h
        sheet.paste(im, (x, y + 24))
        d.rectangle((x, y + 24, x + im.width - 1, y + 24 + im.height - 1),
                    outline="#555")
        d.text((x + 4, y + 6), slug, fill="#eee")
    out = FINAL / "sheet0.png"
    n = 0
    while out.exists():
        n += 1
        out = FINAL / f"sheet{n}.png"
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()