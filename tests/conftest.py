"""Vendor-mirror collection rules (not vendored — local only).

Upstream ships a 447 MB qa/ render corpus that VENDOR.md deliberately
excludes from the mirror, yet vendored test_v3.py asserts qa/shot.py
exists. tests/test_p1.py enforces that exclusion on this mirror and
would fail the moment qa/ reappeared here, so the two contracts cannot
both pass in the mirror. Skip only when the corpus is truly absent, the
same way test_p1 skips upstream-absent cross-checks; the test runs for
real wherever the corpus is present (upstream worktree or a restored
local wall)."""
from pathlib import Path

import pytest

MIRROR = Path(__file__).resolve().parents[1]


def pytest_collection_modifyitems(config, items):
    if (MIRROR / 'qa' / 'shot.py').exists():
        return
    skip = pytest.mark.skip(
        'vendor mirror: the qa/ render corpus is deliberately excluded '
        '(VENDOR.md), and qa/shot.py is part of it')
    for item in items:
        if (item.name == 'test_harness_and_shot_exists'
                and item.location[0].endswith('test_v3.py')):
            item.add_marker(skip)
