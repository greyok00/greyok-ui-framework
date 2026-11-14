#!/usr/bin/env python3
"""tools/minify.py — strip comments from Python, CSS, and JS source.

- Python: tokenize-based comment+docstring strip (same approach as the
  other repos' tools/minify_source.py).
- CSS:   removes /* ... */ block comments outside quoted strings.
- JS:    removes // and /* ... */ comments outside string / template /
         regex literals (a small lexical state machine; `/` is treated as
         a regex opener only in positions where division is impossible).

Run: python3 tools/minify.py [path...]   # default: all tracked sources
"""
import ast
import io
import subprocess
import sys
import tokenize
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

_KEEP_PREFIXES = ("#!", "# noqa", "# type:", "# type ignore",
                  "# pragma:", "# fmt:", "# pylint:")

# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------
def _line_offsets(src: str):
    offsets = {1: 0}
    line = 1
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == "\r":
            line += 1
            if i + 1 < n and src[i + 1] == "\n":
                i += 1
            offsets[line] = i + 1
        elif c == "\n":
            line += 1
            offsets[line] = i + 1
        i += 1
    return offsets


def _byte_line_offsets(data: bytes):
    offsets = {1: 0}
    line = 1
    i = 0
    n = len(data)
    while i < n:
        c = data[i]
        if c == 0x0D:
            line += 1
            if i + 1 < n and data[i + 1] == 0x0A:
                i += 1
            offsets[line] = i + 1
        elif c == 0x0A:
            line += 1
            offsets[line] = i + 1
        i += 1
    return offsets


def _extend_left(src: str, start: int) -> int:
    i = start
    while i > 0 and src[i - 1] in " \t":
        i -= 1
    return i


def minify_python(src: str) -> str:
    offsets = _line_offsets(src)
    spans = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type != tokenize.COMMENT:
                continue
            sl, sc = tok.start
            el, ec = tok.end
            text = src[offsets[sl] + sc: offsets[el] + ec]
            if text.startswith(_KEEP_PREFIXES):
                continue
            if text != tok.string:
                tok_text = tok.string
                if tok_text.startswith(_KEEP_PREFIXES):
                    continue
                idx = src.find(tok_text, offsets[sl] + sc)
                if idx == -1:
                    continue
                end = src.find("\n", idx)
                if end == -1:
                    end = len(src)
                spans.append((_extend_left(src, idx), end))
                continue
            spans.append((_extend_left(src, offsets[sl] + sc), offsets[el] + ec))
    except (tokenize.TokenError, IndentationError):
        pass
    for start, end in sorted(spans, reverse=True):
        src = src[:start] + src[end:]
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src
    data = src.encode("utf-8")
    line_byte_offsets = _byte_line_offsets(data)
    doc_spans = []

    def visit(node):
        body = getattr(node, "body", None)
        if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            d = body[0]
            start = line_byte_offsets[d.lineno] + d.col_offset
            end = line_byte_offsets[d.end_lineno] + d.end_col_offset
            is_fc = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.ClassDef))
            replace_pass = is_fc and len(body) == 1
            if not replace_pass:
                while (start > 0 and data[start - 1] in (0x20, 0x09)
                       and start - 1 >= line_byte_offsets[d.lineno]):
                    start -= 1
            doc_spans.append((start, end, replace_pass))
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    for start, end, replace_pass in sorted(doc_spans, reverse=True):
        if replace_pass:
            data = data[:start] + b"pass" + data[end:]
        else:
            data = data[:start] + data[end:]
    return data.decode("utf-8")


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
def strip_css(src: str) -> str:
    out = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c in "'\"":
            q = c
            out.append(c)
            i += 1
            while i < n:
                out.append(src[i])
                if src[i] == "\\":
                    i += 1
                    if i < n:
                        out.append(src[i])
                elif src[i] == q:
                    i += 1
                    break
                i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            end = src.find("*/", i + 2)
            if end == -1:
                i = n
            else:
                if "\n" in src[i + 2:end]:
                    out.append("\n")
                i = end + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------
def _regex_ok(src: str, i: int) -> bool:
    j = i - 1
    while j >= 0 and src[j] in " \t\n\r":
        j -= 1
    if j < 0:
        return True
    prev = src[j]
    if prev in "([{=,:;!&|?+-*/%<>^~":
        return True
    if prev.isalnum() or prev in "_$)]}":
        return False
    return True


def strip_js(src: str) -> str:
    out = []
    i = 0
    n = len(src)
    state = "code"
    quote_char = ""
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state == "code":
            if c == "`":
                state = "template"
                out.append(c)
                i += 1
            elif c in "'\"":
                state = "sq" if c == "'" else "dq"
                quote_char = c
                out.append(c)
                i += 1
            elif c == "/" and nxt == "/":
                end = src.find("\n", i)
                if end == -1:
                    i = n
                else:
                    out.append("\n")
                    i = end + 1
            elif c == "/" and nxt == "*":
                end = src.find("*/", i + 2)
                if end == -1:
                    i = n
                else:
                    if "\n" in src[i + 2:end]:
                        out.append("\n")
                    i = end + 2
            elif c == "/" and _regex_ok(src, i):
                out.append(c)
                i += 1
                in_class = False
                while i < n:
                    r = src[i]
                    out.append(r)
                    i += 1
                    if r == "\\":
                        if i < n:
                            out.append(src[i])
                            i += 1
                    elif r == "[":
                        in_class = True
                    elif r == "]":
                        in_class = False
                    elif r == "/" and not in_class:
                        break
            else:
                out.append(c)
                i += 1
        elif state in ("sq", "dq"):
            out.append(c)
            i += 1
            if c == "\\":
                if i < n:
                    out.append(src[i])
                    i += 1
            elif c == quote_char:
                state = "code"
        elif state == "template":
            out.append(c)
            i += 1
            if c == "\\":
                if i < n:
                    out.append(src[i])
                    i += 1
            elif c == "`":
                state = "code"
    return "".join(out)


# ---------------------------------------------------------------------------
def minify_file(path: Path) -> bool:
    try:
        src = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    ext = path.suffix
    if ext == ".py":
        out = minify_python(src)
    elif ext == ".css":
        out = strip_css(src)
    elif ext == ".js":
        out = strip_js(src)
    else:
        return False
    if out != src:
        path.write_text(out, encoding="utf-8")
        return True
    return False


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        paths = [Path(a) for a in argv]
    else:
        r = subprocess.run(
            ["git", "ls-files", "*.py", "*.css", "*.js"], cwd=REPO,
            capture_output=True, text=True)
        paths = [REPO / p for p in r.stdout.splitlines() if p]
    changed = 0
    for p in paths:
        if not p.exists() or p.resolve() == Path(__file__).resolve():
            continue
        if minify_file(p):
            changed += 1
            try:
                label = p.relative_to(REPO)
            except ValueError:
                label = p
            print(f"  minified {label}")
    print(f"\n{changed} file(s) minified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
