"""tests/test_gen_types.py — the d.ts element surface stays in sync with reality.

gen_types.py is deterministic; these tests re-derive its inputs and assert the
committed file still covers them, without rewriting the repo file.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_types import inventory_classes, iface_name, infer_tags, dataset_hook_lines, EXT_FOR  # noqa: E402


def test_dts_covers_every_inventory_class():
    classes = inventory_classes()
    text = (ROOT / "typescript" / "elements.d.ts").read_text()
    missing = [c for c in classes if f"interface {iface_name(c)} extends" not in text]
    assert not missing, f".d.ts missing inventory interfaces: {missing}"


def test_dts_has_no_duplicate_interfaces():
    text = (ROOT / "typescript" / "elements.d.ts").read_text()
    names = re.findall(r"interface (El\w+) extends", text)
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert not dupes, f"duplicate interface declarations: {dupes}"


def test_dataset_block_matches_runtime_js():
    text = (ROOT / "typescript" / "elements.d.ts").read_text()
    m = re.search(r"interface HTMLOrSVGElement \{(.*?)\n\}", text, flags=re.S)
    assert m, "HTMLOrSVGElement block absent"
    declared = set(re.findall(r"/\*\* [^*]+ \*/\n    ([a-zA-Z]+)\?: string;", m.group(1)))
    wanted = set(dataset_hook_lines().split("\n") and
                 [k for k in re.findall(r"    ([a-zA-Z]+)\?: string;", dataset_hook_lines())])
    assert declared == wanted, f"dataset hooks out of sync: +{wanted - declared} -{declared - wanted}"


def test_inferred_tags_are_sane():
    classes = inventory_classes()
    tags = infer_tags(classes)
    bad = {c: t for c, t in tags.items() if t not in EXT_FOR and t != "span"}
    assert not bad, f"unknown inferred tags: {bad}"