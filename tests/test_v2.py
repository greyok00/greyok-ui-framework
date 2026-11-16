"""tests/test_v2.py — v0.2.0 workflow-layer checks plus a stricter freeze test
pinning the core color surface. The freeze re-pins deliberately per approved
wave: v0.1.0 commit d3b881c originally, then the v0.4.0 colortypo wave
(focus-ring derived from accent, ink-voice aliases added). Approved snapshot:
tests/baseline/tokens.css."""
import subprocess
import pathlib
import re
from pathlib import Path as PATH

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = "d3b881c"  # "reset version to 0.1.0" — freeze pin


def read(name):
    return (ROOT / name).read_text()


def git_show(path):
    out = subprocess.run(
        ["git", "show", f"{BASELINE}:{path}"], capture_output=True, text=True, cwd=ROOT)
    return out.stdout


def test_v2_tokens_present():
    css = read("tokens-v2.css")
    for token in ("--el-dur-surface:", "--el-dur-flow:", "--el-dur-progress:",
                  "--el-ease-quiet:", "--el-stage-active:", "--el-stage-done:",
                  "--el-stage-running:", "--el-stage-stale:",
                  "--el-facts-paper:", "--el-facts-ink:",
                  "--el-measure:", "--el-font-serif:"):
        assert token in css, f"missing {token}"


def test_core_tokens_additive_only():
    """tokens.css may gain tokens but never lose or alter frozen core color
    tokens from the approved baseline snapshot."""
    import re
    base = read("tests/baseline/tokens.css")
    frozen = sorted(set(re.findall(
        r"[ \t]*--el-(?:bg|panel|line|ink|accent|ok|warn|fail|info|live|teal|"
        r"on-accent|mute|focus-ring|overlay|shadow)[-_0-9A-Za-z]*:[^;]*;", base)))
    now = read("tokens.css")
    lost = [line for line in frozen if line not in now]
    assert not lost, f"tokens.css lost/changed frozen core tokens: {lost}"


def test_old_theme_roster_superseded():
    """v0.3.0 replaces the 17-theme roster entirely."""
    themes = set(re.findall(r'\[data-theme="([a-z0-9-]+)"\]', read("themes.css")))
    old = {"polaroid", "cockpit", "console", "compact", "casebook",
           "agent-paper", "agent-pulse", "agent-history", "terminal",
           "swiss", "bespoke", "torque", "umami", "paper-desk",
           "dark-editorial", "atelier"}
    assert not (old & themes), f"old themes still shipped: {old & themes}"


def test_workflow_classes_complete():
    css = read("elements-workflow.css")
    for cls in (".el-stage-rail", ".el-stage-", ".el-ladder-step", ".el-progress-truth",
                ".el-pt-chunk", ".el-source-card", ".el-citation-rail",
                ".el-fact-grid", ".el-fact "):
        assert cls in css, f"missing {cls}"
    # no fake percentage: honest progress = stages + counts, no scaleX bar
    truth = css.split(".el-progress-truth")[1].split("@keyframes")[0] \
        if ".el-progress-truth" in css else ""
    assert "scaleX" not in truth and "width:" not in truth


def test_inspector_and_reader_sheets():
    insp = read("elements-inspector.css")
    for cls in (".el-inspector", ".el-inspector.is-open", ".el-inspector.is-docked",
                ".el-inspector-scrim"):
        assert cls in insp, f"missing {cls}"
    assert "@media (prefers-reduced-motion: reduce)" in insp
    reader = read("elements-reader.css")
    assert ".el-reader" in reader and "--el-measure" in reader


def test_assistant_sheet():
    css = read("elements-assistant.css")
    for cls in (".el-assistant-panel", ".el-msg--assistant", ".el-msg--user",
                ".el-msg.is-streaming", ".el-plan", ".el-assistant-stop",
                ".is-unsourced"):
        assert cls in css, f"missing {cls}"
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_all_new_sheets_have_reduced_motion_rules():
    for name in ("elements-workflow.css", "elements-inspector.css",
                 "elements-assistant.css"):
        css = read(name)
        assert "@media (prefers-reduced-motion: reduce)" in css, name


def test_workflow_js_clean():
    js = read("elements-workflow.js")
    assert "fetch(" not in js and "XMLHttpRequest" not in js
    out = subprocess.run(["node", "--check", "elements-workflow.js"],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr


def test_demos_exist_and_use_new_classes():
    demo = read("demo/workflows.html")
    reader = read("demo/reader.html")
    assistant = read("demo/assistant.html")
    assert 'class="el-stage-rail"' in demo and "el-fact-grid" in demo
    assert 'class="el-reader"' in reader
    assert 'class="el-assistant-panel"' in assistant
    assert "tokens-v2.css" in demo and "tokens-v2.css" in reader \
        and "tokens-v2.css" in assistant