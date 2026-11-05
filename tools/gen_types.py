#!/usr/bin/env python3
"""tools/gen_types.py — regenerate typescript/elements.d.ts element surface.

Deterministic: inventory classes -> interfaces + typed tag inference from the
markup corpus (demo/ + demo/sites/). Dataset hooks are read straight out of the
runtime JS (dataset.* camel keys), so declarations can never list a hook the
framework stopped using. Legacy demo-harness interfaces (workflow/reader/
assistant surfaces that predate the v0.4 inventory) are preserved verbatim.

Run: python3 tools/gen_types.py
Exit 0 when the file covers the full inventory; tests/ re-checks coverage.
"""
import re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DTD = ROOT / "typescript" / "elements.d.ts"
JS = ROOT / "elements.js"
WORKFLOW = ROOT / "elements-workflow.js"

TAG_FOR = {  # deterministic overrides where markup inference is ambiguous/absent
    "el-kbd": "kbd", "el-table": "table", "el-def-list": "dl",
    "el-task-list": "ul", "el-stepper": "ol", "el-dropdown": "select",
    "el-slider": "input", "el-radio": "input", "el-search": "input",
    "el-textarea": "textarea", "el-prompt": "textarea",
    "el-breadcrumb": "nav", "el-bottom-bar": "nav", "el-anchor-nav": "nav",
}
EXT_FOR = {  # which element interface each tag extends
    "kbd": "HTMLKbdElement", "table": "HTMLTableElement", "dl": "HTMLDListElement",
    "ul": "HTMLUListElement", "ol": "HTMLOListElement", "select": "HTMLSelectElement",
    "input": "HTMLInputElement", "textarea": "HTMLTextAreaElement", "nav": "HTMLNavElement",
    "button": "HTMLButtonElement", "span": "HTMLSpanElement", "div": "HTMLDivElement",
    "p": "HTMLParagraphElement", "a": "HTMLAnchorElement", "img": "HTMLImageElement",
    "form": "HTMLFormElement", "canvas": "HTMLCanvasElement", "pre": "HTMLPreElement",
    "dialog": "HTMLDialogElement", "li": "HTMLLIElement", "button": "HTMLButtonElement",
    "article": "HTMLElement", "aside": "HTMLElement", "figure": "HTMLElement",
    "header": "HTMLElement", "footer": "HTMLElement", "section": "HTMLElement",
    "main": "HTMLElement", "svg": "Element",
}
HTML_ELT = "HTMLElement"


def inventory_classes() -> list:
    text = (ROOT / "docs" / "INVENTORY.md").read_text().split("## Files (v0.4 target)")[0]
    seen, out = set(), []
    for c in sorted(set(re.findall(r"\.el-[a-z0-9-]+", text))):
        if c not in seen:
            seen.add(c); out.append(c)
    return [c[1:] for c in out]  # strip the leading dot


def infer_tags(classes) -> dict:
    classeset = set(classes)
    counts = {c: Counter() for c in classes}
    pages = list((ROOT / "demo").glob("*.html")) + list((ROOT / "demo" / "sites").glob("*/*.html"))
    for page in pages:
        for tag, attr in re.findall(r"<(\w+)[^>]*?class=\"([^\"]*)\"", page.read_text()):
            for cls in attr.split():
                if cls in classeset:
                    counts[cls][tag] += 1
    return {c: (TAG_FOR.get(c) or (counts[c].most_common(1)[0][0] if counts[c] else "span"))
            for c in classes}


def iface_name(cls) -> str:
    return "".join(p.capitalize() for p in cls.split("-"))


def dataset_hook_lines() -> str:
    rx = re.compile(r"dataset\.[a-z][a-zA-Z]*")
    keys = sorted(set(rx.findall(JS.read_text()) + rx.findall(WORKFLOW.read_text())))
    docs = {
        "dialogOpen": "button/hotkey opening the dialog whose id is the value",
        "dialogClose": "closes the containing dialog",
        "drawerOpen": "opens the drawer whose id is the value",
        "drawerClose": "closes the containing drawer",
        "commandOpen": "opens the command palette",
        "command": "palette command id; commandItem marks a results row",
        "menu": "pop-menu trigger; menuKeepOpen avoids auto-close",
        "menuKeepOpen": "menu trigger keeps the menu open for multi-select",
        "modalOpen": "non-dialog overlay opener",
        "modalClose": "closes the containing overlay",
        "toast": "click pushes a toast; toastVariant + toastDuration adjust it",
        "tipPlacement": "tooltip/popover side",
        "scrim": "pairs an overlay with a scrim element id",
        "target": "generic target id (drag/drop, detail panes)",
        "targetList": "drop zone UL id",
        "group": "row-select peer group",
        "exclusive": "accordion auto-closes siblings",
        "draggable": "row is draggable; dragLabel is the payload",
        "for": "datepicker trigger id",
        "copy": "copies the target element or own text",
        "chart": "charts.js host (span/div, SVG filled in)",
        "animateTo": "scroll/animate target id",
        "collapseAfter": "auto-collapsed after N chars",
        "dir": "carousel pager direction (prev|next)",
        "value": "gauge/rating value 0..1",
        "pageSize": "task-board pagination",
        "pageSource": "source provenance id",
        "state": "workflow stage state",
        "recent": "palette recents payload",
        "recentStore": "localStorage key for palette recents",
        "commandItem": "marks a command-palette results row",
        "label": "display label override",
        "action": "tile action id",
        "dialogScrim": "pairs a dialog with a scrim element id",
        "toastDuration": "toast display duration override (ms)",
        "toastVariant": "toast variant class",
        "animateDuration": "view/scroll animation duration override (ms)",
        "shadowTop": "scroll shadow top element id",
        "shadowBot": "scroll shadow bottom element id",
    }
    lines = []
    for k in keys:
        # Undocumented hooks fall back to a data-kebab-case name derived from
        # the camelCase dataset key.
        fallback = "data-" + re.sub(r"(?<!^)(?=[A-Z])", "-", k).lower()
        lines.append(f'    /** {docs.get(k, fallback)}. */')
        lines.append(f'    {k}?: string;')
    return "\n".join(lines)


def main() -> int:
    classes = inventory_classes()
    tags = infer_tags(classes)
    inv_ifaces = [iface_name(c) for c in classes]
    src = DTD.read_text()

    # existing interfaces = the legacy set we must preserve (tagmap references them)
    existing = dict(re.findall(r"interface (El\w+) extends (\w+)", src))
    legacy = {n: ext for n, ext in existing.items()
              if n not in inv_ifaces or re.match(r"ElDatePicker|ElSelect|ElStage|ElReader|ElAssistant|ElInspector|ElLadder|ElProgressTruth|ElSourceCard|ElCitationRail|ElFactGrid", n)}

    lines = src.splitlines(keepends=True)
    i_disp = next(i for i, l in enumerate(lines)
                  if "── Display ──" in l or "GENERATED by tools/gen_types.py" in l)
    i_ns_close = next(i for i, l in enumerate(lines) if i > i_disp and l.rstrip() == "}")

    gen = []
    for c, iface in zip(classes, inv_ifaces):
        tag = tags[c]
        gen.append(f"  interface {iface} extends {EXT_FOR.get(tag, HTML_ELT)} {{}}")
    legacy_lines = [f"  interface {n} extends {e} {{}}" for n, e in sorted(legacy.items())
                    if n not in inv_ifaces]
    lines[i_disp:i_ns_close] = [
        f"  // ── Element interfaces — GENERATED by tools/gen_types.py from docs/INVENTORY.md "
        f"({len(classes)} classes, tag inferred from the markup corpus) ──\n\n",
        "\n".join(gen) + "\n\n",
        "  // ── Legacy demo-harness surfaces kept (predate the v0.4 inventory) ──\n\n",
        ("\n".join(legacy_lines) + "\n") if legacy_lines else "",
        "\n",
    ]
    DTD.write_text("".join(lines))

    dtd = DTD.read_text()
    m = re.search(r"interface HTMLOrSVGElement \{.*?\n\}\n", dtd, flags=re.S)
    assert m, "HTMLOrSVGElement block drifted"
    dtd = dtd.replace(m.group(0),
                      "interface HTMLOrSVGElement {\n" + dataset_hook_lines() + "\n}\n", 1)
    DTD.write_text(dtd)

    # guards: full inventory coverage + no name collisions between gen and legacy
    final = DTD.read_text()
    dupes = [n for n in inv_ifaces if final.count(f"interface {n} extends") > 1]
    missing = [c for c, n in zip(classes, inv_ifaces) if f"interface {n} extends" not in final]
    if dupes or missing:
        print("gen_types: ✗ dupes:", dupes, "missing:", missing, file=sys.stderr)
        return 1
    print(f"gen_types: OK {len(classes)} inventory interfaces (+{len(legacy_lines)} legacy) regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())