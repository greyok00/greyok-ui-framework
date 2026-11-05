import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

V3_ROSTER = [
    "mono-console", "ghost-terminal", "cream-journal", "paper-press",
    "brutal-stamp", "brutal-index", "orbit-deep", "solar-halo",
    "agency-quartz", "agency-mono-plate", "maison-serif", "noir-couture",
    "sticker-pop", "sketchbook", "console-light", "grid-ledger",
    "kinetic-ink", "aperture-motion", "ma-quiet", "gesshoku",
]

REQUIRED = [
    "--el-bg", "--el-panel", "--el-panel-2", "--el-panel-3",
    "--el-line", "--el-line-2", "--el-line-strong",
    "--el-ink", "--el-ink-soft", "--el-mute", "--el-on-accent",
    "--el-accent", "--el-accent-hover", "--el-accent-soft",
    "--el-ok", "--el-warn", "--el-fail", "--el-info", "--el-live", "--el-teal",
    "--el-focus-ring", "--el-font-body", "--el-font-display", "--el-font-mono",
    "--el-ornament", "--el-rule-style", "--el-hero-pad", "--el-hero-min",
    "--el-head-weight", "--el-head-case", "--el-card-pad", "--el-ctl-min-h",
]

V3_FILES = {
    "mono-console": "tech-mono.css", "ghost-terminal": "tech-mono.css",
    "cream-journal": "editorial.css", "paper-press": "editorial.css",
    "brutal-stamp": "neo-brutalist.css", "brutal-index": "neo-brutalist.css",
    "orbit-deep": "webgl-immersive.css", "solar-halo": "webgl-immersive.css",
    "agency-quartz": "agency-classic.css", "agency-mono-plate": "agency-classic.css",
    "maison-serif": "fashion-serif.css", "noir-couture": "fashion-serif.css",
    "sticker-pop": "illustration.css", "sketchbook": "illustration.css",
    "console-light": "dashboard-light.css", "grid-ledger": "dashboard-light.css",
    "kinetic-ink": "motion-brand.css", "aperture-motion": "motion-brand.css",
    "ma-quiet": "quiet-minimal.css", "gesshoku": "quiet-minimal.css",
}


def src(name):
    return (ROOT / "themes" / "src" / name).read_text()


def test_roster_sources_complete():
    for group in sorted(set(V3_FILES.values())):
        assert (ROOT / "themes" / "src" / group).exists(), f"missing source {group}"


def test_blocks_match_roster_exactly():
    for name, group in V3_FILES.items():
        heads = set(re.findall(r'\[data-theme="([a-z0-9-]+)"\]', src(group)))
        assert name in heads, f"{group} does not declare {name}"


def test_full_token_set_per_theme():
    for name, group in V3_FILES.items():
        flat = re.sub(r"\s+", "", src(group)).split('[data-theme="' + name + '"', 1)
        assert len(flat) == 2, f"{name} block missing"
        body = flat[1][:5000]
        for tok in REQUIRED:
            assert tok + ":" in body, f"{name} missing {tok}"


def test_unique_display_faces():
    seen = {}
    for name, group in V3_FILES.items():
        css = src(group)
        block = css.split('[data-theme="' + name + '"', 1)[1]
        m = re.search(r"--el-font-display:\s*'([^']+)'", block)
        assert m, f"{name} has no display font"
        fam = m.group(1)
        if fam == "Helvetica Neue":
            fam = "system-helvetica"
        assert fam not in seen or seen[fam] == name, \
            f"display face '{fam}' shared by {seen.get(fam)} and {name}"
        seen[fam] = name
    assert len(seen) == 20, f"expected 20 unique display faces, got {len(seen)}"


def test_no_root_block_in_sources():
    for name, group in V3_FILES.items():
        css = re.sub(r"/\*.*?\*/", "", src(group), flags=re.S)
        assert ":root" not in css, f"{group} leaks a :root block"


def test_built_themes_css_covers_roster():
    css = (ROOT / "themes.css").read_text()
    blocks = set(re.findall(r'\[data-theme="([a-z0-9-]+)"\]', css))
    assert blocks == set(V3_ROSTER), f"themes.css mismatch: {sorted(blocks)}"


def test_harness_and_shot_exists():
    assert (ROOT / "demo" / "harness.html").exists()
    assert (ROOT / "qa" / "shot.py").exists()
