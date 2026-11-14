#!/usr/bin/env python3
"""tools/build_themes.py — assemble themes/src families into minified themes.css.

Each family file holds TWO theme blocks (the v3 rule: every theme is radically
different, so sources stay grouped by family). Roster order defines output
order; body is wrapped in @layer el-themes (declared last in base.css so
signatures outrank the element baseline).

Run: python3 tools/build_themes.py
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "themes" / "src"
OUT = ROOT / "themes.css"

FAMILY_SLUGS = {
    "tech-mono":       ["mono-console", "ghost-terminal"],
    "editorial":       ["cream-journal", "paper-press"],
    "neo-brutalist":   ["brutal-stamp", "brutal-index"],
    "webgl-immersive": ["orbit-deep", "solar-halo"],
    "agency-classic":  ["agency-quartz", "agency-mono-plate"],
    "fashion-serif":   ["maison-serif", "noir-couture"],
    "illustration":    ["sticker-pop", "sketchbook"],
    "dashboard-light": ["console-light", "grid-ledger"],
    "motion-brand":    ["kinetic-ink", "aperture-motion"],
    "quiet-minimal":   ["ma-quiet", "gesshoku"],
}

REQUIRED_TOKENS = [
    "--el-bg", "--el-panel", "--el-panel-2", "--el-panel-3",
    "--el-line", "--el-line-2", "--el-line-strong",
    "--el-ink", "--el-ink-soft", "--el-mute", "--el-on-accent",
    "--el-accent", "--el-accent-hover", "--el-accent-soft",
    "--el-ok", "--el-warn", "--el-fail", "--el-info", "--el-live", "--el-teal",
    "--el-focus-ring", "--el-font-body", "--el-font-display", "--el-font-mono",
]

HEAD = re.compile(r'\[data-theme="([a-z0-9-]+)"]\s*\{')

STR_SPAN = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'')

def top_level_segments(raw: str) -> list:
    """Split comment-stripped CSS into top-level segments (brace-balanced cuts).

    A segment is one top-level rule or one whole at-rule (@media, @property,
    @keyframes, @font-face …) — anything that starts a block at brace depth 0
    and ends at its matching `}` (or a top-level `;` statement). Strings are
    skipped while walking: data-URI values and font names may carry braces.
    An unterminated tail is returned as its own segment so the balance gate
    still fires on it.
    """
    segs, start = [], 0
    depth, i, n = 0, 0, len(raw)
    in_str = ""
    while i < n:
        c = raw[i]
        if in_str:
            if c == in_str:
                in_str = ""
            i += 1
            continue
        if c in "\"'":
            in_str = c
        elif c == '{':
            depth += 1
        elif c == '}':
            if depth == 0:  # orphan close: own segment (gate flags it)
                seg = raw[start:i + 1]
                if seg.strip():
                    segs.append(seg)
                start = i + 1
            else:
                depth -= 1
                if depth == 0:  # a block just closed: segment complete
                    seg = raw[start:i + 1]
                    if seg.strip():
                        segs.append(seg)
                    start = i + 1
        elif c == ';' and depth == 0:
            seg = raw[start:i + 1]
            if seg.strip():
                segs.append(seg)
            start = i + 1
        i += 1
    if raw[start:].strip():
        segs.append(raw[start:])  # unterminated tail — balance gate flags
    return segs

def block_of(raw: str, slug: str) -> str:
    """Concatenate every top-level segment that references the slug, in file order.

    The old rule cut at the next different-slug head; the v0.4 mobile pass
    ships shared narrow blocks with later `[data-theme="a"] { … }` token
    lines inside them, so the cut landed mid-media. Grouping by reference
    routes every rule to the right theme wherever it was appended.
    """
    return "".join(s for s in top_level_segments(raw)
                   if f'[data-theme="{slug}"]' in s)

def minify(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)
    stripped = css.strip()
    if ":root" in stripped:
        raise ValueError("minifier output contains :root — tokens must live on [data-theme] block heads")
    return stripped

def main() -> int:
    # Optional scoping: --src DIR --out FILE builds an alternative roster
    # (e.g. the local-only program) with the SAME gates. Roster is derived
    # from the files' own [data-theme] heads so the local program never
    # has to edit FAMILY_SLUGS. Default (no flags) behavior is unchanged.
    global FAMILY_SLUGS, SRC, OUT
    argv = sys.argv[1:]
    local_roster = None
    if "--src" in argv:
        SRC = Path(argv[argv.index("--src") + 1]).resolve()
        local_roster = True
    if "--out" in argv:
        OUT = Path(argv[argv.index("--out") + 1]).resolve()
    if local_roster:
        FAMILY_SLUGS = {}
        for f in sorted(SRC.glob("*.css")):
            raw = re.sub(r"/\*.*?\*/", "", f.read_text(), flags=re.S)
            heads = []
            for m in HEAD.finditer(raw):
                if m.group(1) not in heads:
                    heads.append(m.group(1))
            if heads:
                FAMILY_SLUGS[f.stem] = heads

    problems = []
    seen_slugs, display_refs, chunks = set(), {}, {}
    for fam, slugs in FAMILY_SLUGS.items():
        src = SRC / f"{fam}.css"
        if not src.exists():
            problems.append(f"missing source: {src}")
            continue
        raw = re.sub(r"/\*.*?\*/", "", src.read_text(), flags=re.S)
        heads = sorted(set(m.group(1) for m in HEAD.finditer(raw)))
        if heads != sorted(slugs):
            problems.append(f"{fam}: must declare exactly {slugs}, got {heads}")
            continue
        for slug in slugs:
            block = block_of(raw, slug)
            if not block:
                problems.append(f"{slug}: empty block")
                continue
            if block.count("{") != block.count("}"):
                problems.append(f"{slug}: unbalanced braces")
            flat = re.sub(r"\s+", "", block)
            for tok in REQUIRED_TOKENS:
                if tok + ":" not in flat:
                    problems.append(f"{slug}: missing token {tok}")
            m = re.search(r"--el-font-display:\s*'([^']+)'", block)
            if m and m.group(1) != "Helvetica Neue":
                if m.group(1) in display_refs:
                    problems.append(f"{slug}: display face '{m.group(1)}' already used by {display_refs[m.group(1)]}")
                display_refs[m.group(1)] = slug
            seen_slugs.add(slug)
            chunks[slug] = block
    missing = {s for sl in FAMILY_SLUGS.values() for s in sl} - seen_slugs
    for slug, chunk in chunks.items():
        if len(chunk) < 4000:
            problems.append(f"{slug}: suspiciously small slice ({len(chunk)} chars) — signatures may be cut")
    if missing:
        problems.append(f"roster incomplete: {sorted(missing)}")
    if problems:
        for p in problems:
            print("build: ✗", p, file=sys.stderr)
        return 1

    roster_order = [s for sl in FAMILY_SLUGS.values() for s in sl]

    # Top-level @property/@keyframes at-rules declared outside any slug slice
    # are still part of a family's theme and must ship (registrations are
    # document-global; slice placement only matters for keyframe names that a
    # theme references). Names inside slices win; orphans only fill gaps.
    AT_RULE_SPAN = re.compile(
        r'(@property\s+-[\w-]+|@keyframes\s+[\w-]+)\s*\{(?:[^{}]|\{[^{}]*\})*\}')
    slice_names = set()
    leftover_by_fam = {}
    for fam, slugs in FAMILY_SLUGS.items():
        raw = re.sub(r"/\*.*?\*/", "", (SRC / f"{fam}.css").read_text(), flags=re.S)
        leftover = []
        for seg in top_level_segments(raw):
            if any(f'[data-theme="{s}"]' in seg for s in slugs):
                slice_names |= set(re.findall(AT_RULE_SPAN, seg))
            else:
                leftover.append(seg)
        leftover_by_fam[fam] = "".join(leftover)
    orphan_css = []
    for fam, slugs in FAMILY_SLUGS.items():
        for m in AT_RULE_SPAN.finditer(leftover_by_fam[fam]):
            name = m.group(1).strip()
            if name in slice_names:
                continue  # slice already carries an identical-named rule
            orphan_css.append(m.group(0))
            slice_names.add(name)

    body = "@layer el-themes{" + minify("".join(chunks[s] for s in roster_order) + " ".join(orphan_css)) + "}"
    tmp = OUT.with_suffix(".css.tmp")
    tmp.write_text(body + "\n")          # atomic: never leave a half-written artifact
    tmp.replace(OUT)
    blocks = len(re.findall(r'\[data-theme=', body))
    print(f"themes.css: {OUT.stat().st_size} bytes, {blocks} theme blocks, "
          f"{len(display_refs)} unique display faces, {len(orphan_css)} orphan at-rules retained")
    return 0

if __name__ == "__main__":
    sys.exit(main())