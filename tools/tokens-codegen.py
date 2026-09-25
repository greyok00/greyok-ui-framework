#!/usr/bin/env python3
"""tools/tokens-codegen.py — emit CSS custom properties from design-token JSON.

Feeds (in ~/ui-framework-notes/design-tokens/):
  colors.json      → --el-bg/--el-panel*/--el-line*/--el-ink*/--el-accent*/--el-ok/--el-warn/
                     --el-fail/--el-info/--el-live/--el-teal/--el-on-accent (per theme,
                     utility.semantic → ok/warn/fail/info fallbacks, utility.border → line tokens)
  spacing.json     → --el-space-* (space.xs..5xl)
  typography.json  → --el-fs-* (scale.caption..display) + --el-font-* (font-family fallbacks)

Honest mapping: only keys that exist in the JSON are emitted; anything missing is skipped.
The framework's own tokens.css is the source of truth for shipped values — this tool is a
starting point for regenerating a palette from an audit JSON, not a replacement for it.

Usage:
  python3 tools/tokens-codegen.py                     # all sources → stdout
  python3 tools/tokens-codegen.py -o out.css          # → file
  python3 tools/tokens-codegen.py --dir ~/path/tokens # custom notes dir
"""
import argparse
import json
import pathlib
import sys

DEFAULT_DIR = pathlib.Path.home() / "ui-framework-notes" / "design-tokens"

SIZE_MAP = {  # typography.json scale key → framework token
    "caption": "xs", "body-small": "sm", "body": "md", "body-large": "lg",
    "h2": "xl", "h1": "2xl",
}


def load(d, name):
    p = d / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError) as e:
        print(f"# ! skipped {name}: {e}", flush=True)
        return None


def first(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return None


def emit(lines, name, value):
    if value is None:
        return
    lines.append(f"  --el-{name}: {value};")


def colors(out, data):
    themes = data.get("themes", {})
    for tname, t in themes.items():
        if tname in ("brand", "utility"):
            continue
        out.append(f"\n/* theme: {tname} — {t.get('description', '')} */")
        out.append(f'[data-theme="{tname}"] {{')
        lines = []
        bg = t.get("background", {})
        emit(lines, "bg", bg.get("primary"))
        emit(lines, "panel", first(bg, "secondary", "card") or t.get("surface", {}).get("card"))
        p2 = bg.get("tertiary")
        if p2:
            emit(lines, "panel-2", p2)
            emit(lines, "panel-3", p2)
        text = t.get("text", {})
        emit(lines, "ink", text.get("primary"))
        emit(lines, "ink-soft", text.get("secondary"))
        emit(lines, "mute", text.get("tertiary"))
        accents = t.get("accent", {})
        # accent = first non-description accent found
        for group in accents.values():
            if isinstance(group, dict) and group:
                emit(lines, "accent", next(iter(group.values())))
                break
        states = t.get("states", {})
        emit(lines, "focus-ring", states.get("focus"))
        out.extend(lines)
        out.append("}")

    util = themes.get("utility", {})
    if util:
        out.append("\n/* utility tokens (semantic + border) */")
        sem = util.get("semantic", {})
        bor = util.get("border", {})
        for src, dst in (("success", "ok"), ("warning", "warn"), ("error", "fail"), ("info", "info")):
            if src in sem:
                out.append(f"  --el-{dst}: {sem[src]};")
        if "default" in bor:
            out.append(f"  --el-line: {bor['default']};")
        if "subtle" in bor:
            out.append(f"  --el-line-2: {bor['subtle']};")
        if "strong" in bor:
            out.append(f"  --el-line-strong: {bor['strong']};")
    return bool(themes) or bool(util)


def spacing(out, data):
    space = data.get("space", {})
    if not space:
        return False
    out.append("\n/* spacing */")
    for k, v in space.items():
        val = v.get("px") if isinstance(v, dict) else v
        out.append(f"  --el-space-{k}: {val};")
    return True


def typography(out, data):
    scale = data.get("scale", {})
    fonts = data.get("font-family", {})
    if not scale and not fonts:
        return False
    out.append("\n/* typography */")
    for k, t in scale.items():
        val = t.get("size-rem") or t.get("size")
        if val:
            out.append(f"  --el-fs-{SIZE_MAP.get(k, k)}: {val};")
    for k, f in fonts.items():
        if k == "display" and "fallback" in f:
            out.append(f"  --el-font-display: {f['fallback']};")
        elif k in ("modern", "heritage") and "fallback" in f:
            out.append(f"  --el-font-body: {f['fallback']};")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--out", help="output file (default stdout)")
    ap.add_argument("--dir", default=str(DEFAULT_DIR), help="design-tokens JSON dir")
    args = ap.parse_args()
    d = pathlib.Path(args.dir).expanduser()

    out = ["/* generated by tools/tokens-codegen.py — do not hand-edit */"]
    wrote = []
    data = load(d, "colors.json")
    if data and colors(out, data):
        wrote.append("colors")
    data = load(d, "spacing.json")
    if data and spacing(out, data):
        wrote.append("spacing")
    data = load(d, "typography.json")
    if data and typography(out, data):
        wrote.append("typography")

    if not wrote:
        print("no token JSON found — nothing emitted", file=__import__("sys").stderr)
        return 1
    out.append(f"\n/* sources: {', '.join(w + '.json' for w in wrote)} */\n")
    text = "\n".join(out)
    if args.out:
        pathlib.Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())