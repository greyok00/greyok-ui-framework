"""tests/test_python_bridge.py — the Python/Tkinter theme bridge.

_resolve() must substitute var() references for every derived theme token:
_load_themes indexes vars under their `el-`-stripped names ('accent'), so the
reference var(--el-accent) has to be looked up under the same stripped name.
Before the fix every derived token (accent-soft, focus-ring, link, …) came
back as raw var() text, which Tk rejects as a color.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import greyok_ui_framework as bridge  # noqa: E402


def test_resolve_substitutes_stripped_token_names():
    assert bridge._resolve("var(--el-accent)", {"accent": "#ffb000"}) == "#ffb000"
    assert bridge._resolve(
        "color-mix(in oklab,var(--el-accent) 12%,transparent)",
        {"accent": "#ffb000"}) == "color-mix(in oklab,#ffb000 12%,transparent)"


def test_resolve_follows_chained_tokens():
    out = bridge._resolve(
        "var(--el-focus-ring)",
        {"focus-ring": "var(--el-accent)", "accent": "#ffb000"})
    assert out == "#ffb000"


def test_resolve_keeps_unknown_references_verbatim():
    assert bridge._resolve("var(--el-nothing)", {"accent": "#ffb000"}) \
        == "var(--el-nothing)"


def test_real_theme_tokens_are_concrete_colors():
    themes = bridge._load_themes()
    for slug, theme in themes.items():
        raw = dict(theme.tokens)
        for key, value in raw.items():
            if any(c in value for c in "rgba#"):  # color-bearing token
                assert "var(--" not in value, \
                    f"{slug}.{key} still carries an unresolved var(): {value}"
