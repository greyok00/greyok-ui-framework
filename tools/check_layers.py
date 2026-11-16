#!/usr/bin/env python3
"""tools/check_layers.py — element-sheet @layer discipline (v0.4 rule).

The cascade root cause: unlayered element CSS outranks ALL named layers, so
one stray top-level rule starves theme signatures in the built themes.css.
Every elements-*.css sheet must therefore carry its entire rule set inside a
single top-level `@layer el-elements { ... }` wrap. This tool fails on any
top-level rule that sits outside the wrap.

Run: python3 tools/check_layers.py   (exit 1 on violation)
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEETS = sorted(ROOT.glob("elements-*.css")) + [ROOT / "base.css"]

SKIP_AT = ("@charset", "@import")  # never expected, but report distinctly


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def match_brace(css: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(css)  # unterminated


def survey(path: Path):
    """Return list of violation strings for one sheet."""
    css = strip_comments(path.read_text())
    problems = []
    if css.count("@layer") == 0:
        return [f"{path.name}: no @layer at all — every rule is unlayered"]

    # Walk top level; anything outside layer blocks must be layer statements.
    i, wraps = 0, 0
    while i < len(css):
        j = css.find("{", i)
        if j == -1:
            tail = css[i:].strip()
            for stmt in filter(None, (s.strip() for s in tail.split(";"))):
                if stmt.startswith("@layer"):
                    continue  # bare `@layer x;` ok
                if stmt:
                    problems.append(f"{path.name}: stray top-level content `{stmt[:60]}`")
            break
        before = css[i:j].strip()
        m = re.search(r"@layer\s+[\w,\s-]+$", before)
        if m and not before[m.start() + 7:].strip().startswith(";"):
            end = match_brace(css, j)
            wraps += 1
            i = end + 1
            continue
        if m:  # `@layer x;` statement — consume through the semicolon
            semi = css.find(";", j)
            i = (semi + 1) if semi != -1 else j + 1
            continue
        # A rule or at-rule at top level, outside any layer wrap.
        head = before.split("\n")[-1].strip() if before else css[max(0, i - 1):j].strip()
        head = " ".join(head.split())
        at = head.startswith("@")
        end = match_brace(css, j)
        body_probe = re.sub(r"\s+", "", css[j + 1:end])
        if not at and not body_probe:
            i = end + 1
            continue  # stray `;`-ish noise
        kind = "at-rule" if at else "rule"
        problems.append(f"{path.name}: top-level {kind} outside layer wrap: `{head[:70]}`")
        i = end + 1

    if wraps != 1:
        problems.append(f"{path.name}: expected exactly 1 @layer wrap, found {wraps}")
    return problems


def main() -> int:
    all_problems = []
    for path in SHEETS:
        if path.exists():
            all_problems.extend(survey(path))
    if all_problems:
        for p in all_problems:
            print("layer: ✗", p, file=sys.stderr)
        return 1
    print(f"layer: OK {len(SHEETS)} sheets fully wrapped in @layer el-elements")
    return 0


if __name__ == "__main__":
    sys.exit(main())