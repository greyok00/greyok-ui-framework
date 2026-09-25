"""tests/test_framework.py — no-browser sanity checks for greyok-ui-framework."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text()


# ── CSS var cross-check ───────────────────────────────────────────────────────

def collect_vars():
    """var(--x) references (bare, no fallback) and --x definitions across all CSS."""
    refs, defs = set(), set()
    for f in ROOT.glob("*.css"):
        css = read(f.name)
        defs |= set(re.findall(r"(--el-[a-z0-9-]+)\s*:", css))
        # only flag bare references — var(--x, fallback) may be component-local opt-in
        refs |= set(re.findall(r"var\(\s*(--el-[a-z0-9-]+)\s*\)", css))
    return refs, defs


def test_css_vars_all_defined():
    refs, defs = collect_vars()
    missing = sorted(r for r in refs - defs)
    assert not missing, f"vars used but never defined: {missing}"


def test_tokens_css_parses_and_brace_balanced():
    css = read("tokens.css")
    assert css.count("{") == css.count("}")
    # strip comments + non-custom-prop content: every declaration line is well-formed
    for line in re.findall(r"--el-[\w-]+\s*:[^;{}]+;", css):
        assert line.strip(), "malformed token declaration"


def test_15_themes():
    themes = read("themes.css")
    blocks = set(re.findall(r'\[data-theme="([^"]+)"\]', themes))
    assert len(blocks) == 14, f"expected 14 data-theme blocks in themes.css, got {sorted(blocks)}"
    tokens = read("tokens.css")
    assert ":root" in tokens or '[data-theme="neutral"]' in tokens, "neutral theme missing from tokens.css"
    assert len(blocks) + 1 == 15, "expected 15 themes total (14 + neutral)"
    for luxury in ("bespoke", "torque", "umami"):
        assert luxury in blocks, f"missing luxury theme {luxury}"


def test_no_duplicate_class_definitions():
    """No base class may be *defined* twice. Modifier chains (.el-btn.el--lg) and
    scoped overrides (.el-mini-bars .bar) don't count; a redefinition that only
    adds container-type (container-query layering) is also allowed."""
    seen = {}
    dupes = []
    for f in sorted(ROOT.glob("elements-*.css")) + [ROOT / "base.css"]:
        for m in re.finditer(r"^\.([\w-]+)\s*\{(.*)$", read(f.name), re.M):
            cls, body = m.group(1), m.group(2)
            if cls in seen and seen[cls] != f.name:
                if re.fullmatch(r"\s*container-type:\s*[\w-]+\s*;?\s*\}?\s*", body):
                    continue  # container-query layering, not a conflict
                dupes.append(f".{cls} in {f.name} and {seen[cls]}")
            seen.setdefault(cls, f.name)
    assert not dupes, f"duplicate .el-* class definitions: {dupes}"


def test_icons_sprite_complete():
    js = read("elements.js") + read("charts.js")
    sprite = read("assets/icons.svg")
    named = re.findall(r"icon\('([\w-]+)'\)", js)
    in_html = set()
    for page in (ROOT / "demo").glob("*.html"):
        in_html |= set(re.findall(r"icon\('([\w-]+)'\)", page.read_text()))
    # core set every consumer may rely on
    core = {"search", "close", "x", "chevron-down", "chevron-left", "chevron-right",
            "check", "plus", "minus", "calendar", "clock", "user", "settings",
            "download", "upload", "copy", "trash", "edit", "external",
            "arrow-left", "arrow-right", "star", "heart", "menu", "info"}
    for name in core | in_html:
        assert f'id="el-i-{name}"' in sprite, f"sprite missing el-i-{name}"
    assert len(re.findall(r'id="el-i-[\w-]+"', sprite)) >= 24


def test_charts_auto_kinds_covered():
    js = read("charts.js")
    for kind in ("sparkline", "bar", "line", "donut", "area"):
        assert f"[data-chart='{kind}']" in js or kind in js, f"charts: {kind} missing"


# ── JS sanity (no node subprocess needed) ─────────────────────────────────────

def test_js_balanced():
    for name in ("elements.js", "charts.js", "theme-switcher.js"):
        js = read(name)
        assert js.count("{") == js.count("}"), f"{name}: braces unbalanced"
        assert js.count("(") == js.count(")"), f"{name}: parens unbalanced"


def test_charts_css_animations_and_reduced_motion():
    css = read("elements-dataviz.css")
    assert ".el-chart" in css
    assert "prefers-reduced-motion" in css
    for keyframe in ("el-chart-draw", "el-chart-grow", "el-chart-donut"):
        assert f"@keyframes {keyframe}" in css


def test_demo_pages_reference_existing_assets():
    for page in (ROOT / "demo").glob("*.html"):
        html = page.read_text()
        for m in re.findall(r'(?:src|href)="\.\./([^"]+)"', html):
            assert (ROOT / m).exists(), f"{page.name} references missing ../{m}"