"""tests/test_elements_js.py — behavior tests for elements.js via tests/dom_harness.cjs.

The stub DOM in the harness boots the real elements.js against a fixture tree
(a datepicker with an INPUT owner, a code block holding escaped markup), so
these assert what the picker builds and stores, not how the source reads.

datepicker-iso needs a fixed zone to be deterministic: under a UTC+ zone the
old toISOString() write shifted every picked date one day back.
"""
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "dom_harness.cjs"

SCENARIOS = [
    "datepicker-alignment",
    "datepicker-iso",
    "codeblock-no-live-markup",
]


def run_scenario(name, env=None):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run(
        ["node", str(HARNESS), name], capture_output=True, text=True,
        cwd=ROOT, env=e, timeout=60)


@pytest.mark.parametrize("name", SCENARIOS)
def test_dom_harness_scenario(name):
    env = {"TZ": "Europe/Berlin"} if name == "datepicker-iso" else None
    out = run_scenario(name, env)
    assert out.returncode == 0, f"{name} failed:\n{out.stdout}\n{out.stderr}"
