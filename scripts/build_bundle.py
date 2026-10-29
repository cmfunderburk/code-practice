"""Build the app's content bundle from the corpus.

    uv run python scripts/build_bundle.py [--corpus DIR] [--out FILE]

The server runs this at startup; the app imports the result (src/generated/bundle.json).
The corpus defaults to the repo's corpus/, or $CODE_PRACTICE_CORPUS when set.

Each program's Python, Rust and C solutions are split into drill units, and each unit into
reveal steps (corpus/README.md). Where the program has a `python/sections.toml`, its grouping
and cues win, and the ports borrow its cues by name."""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import io
import json
import os
import re
import tokenize
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = Path(os.environ.get("CODE_PRACTICE_CORPUS") or ROOT / "corpus")
OUT = ROOT / "src" / "generated" / "bundle.json"
TIERS = ("easy", "medium", "hard")


# --- units ----------------------------------------------------------------------------

def _unit_key(node: ast.stmt) -> str:
    """A top-level unit's name, which is what sections.toml lists as its symbol."""
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "imports"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.TypeAlias):
        return node.name.id
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Tuple) \
            and all(isinstance(e, ast.Name) for e in node.targets[0].elts):
        return node.targets[0].elts[0].id  # WIDTH, HEIGHT = 7, 5 is the unit WIDTH
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    if isinstance(node, ast.If) and "__name__" in ast.unparse(node.test):
        return "__main__"
    raise ValueError(f"line {node.lineno}: unsupported top-level statement "
                     f"{ast.unparse(node).splitlines()[0]!r}")


def _start(node: ast.stmt, lines: list[str], floor: int) -> int:
    """0-based first line of a unit: its decorators, and the comments directly above it."""
    decorators = getattr(node, "decorator_list", [])
    start = min([node.lineno] + [d.lineno for d in decorators]) - 1
    while start > floor and lines[start - 1].lstrip().startswith("#"):
        start -= 1
    return start


@dataclass(frozen=True)
class Span:
    key: str
    start: int            # 0-based, inclusive
    end: int              # 0-based, exclusive: the next unit's start, or the end of the body
    nodes: tuple[ast.stmt, ...]


def top_units(tree: ast.Module, lines: list[str]) -> list[Span]:
    """Consecutive imports are one unit; every other top-level statement is its own."""
    found: list[tuple[str, int, list[ast.stmt]]] = []
    for node in tree.body:
        key = _unit_key(node)
        if key == "imports" and found and found[-1][0] == "imports":
            found[-1][2].append(node)
            continue
        found.append((key, _start(node, lines, 0), [node]))
    return [Span(key, start, found[i + 1][1] if i + 1 < len(found) else len(lines), tuple(nodes))
            for i, (key, start, nodes) in enumerate(found)]


def method_units(cls: ast.ClassDef, lines: list[str]) -> list[Span]:
    """A class's methods, each from its decorators/comments to the next method or the end of
    the class. Class-level fields before the first method are not a child unit."""
    defs = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    floor = cls.lineno  # comments can't climb above the class header
    starts = [_start(d, lines, floor) for d in defs]
    out = []
    for i, d in enumerate(defs):
        end = starts[i + 1] if i + 1 < len(defs) else cls.end_lineno
        out.append(Span(d.name, starts[i], end, (d,)))
    return out


# --- steps ----------------------------------------------------------------------------

def logical_lines(text: str) -> list[tuple[int, int]]:
    """(first, last) 0-based physical lines of every logical line, in order."""
    out = []
    first = None
    skip = {tokenize.NL, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT,
            tokenize.ENCODING, tokenize.ENDMARKER}
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.NEWLINE:
            if first is not None:
                out.append((first, tok.start[0] - 1))
            first = None
        elif tok.type not in skip and first is None:
            first = tok.start[0] - 1
    return out


def steps_for(start: int, end: int, logical: list[tuple[int, int]]) -> list[int]:
    """The reveal step of each line in [start, end). A logical line is one step; blank and
    comment-only lines join the step after them, or the last step at the end of the unit."""
    first_of = {a: b for a, b in logical}
    steps: list[int | None] = []
    step = -1
    i = start
    while i < end:
        if i in first_of:
            step += 1
            last = min(first_of[i], end - 1)
            steps.extend([step] * (last - i + 1))
            i = last + 1
        else:
            steps.append(None)  # resolved below
            i += 1
    nxt = max(step, 0)
    for j in range(len(steps) - 1, -1, -1):
        if steps[j] is None:
            steps[j] = nxt
        else:
            nxt = steps[j]
    return steps  # type: ignore[return-value]


# --- Rust and C -----------------------------------------------------------------------

PORT_EXT = {"rust": "rs", "c": "c"}
_OPENS, _CLOSES = "([{", ")]}"
_RUST_CHAR = re.compile(r"b?'(?:\\(?:u\{[0-9a-fA-F]+\}|x[0-9a-fA-F]{2}|.)|[^\\'\n])'")
_C_CHAR = re.compile(r"'(?:\\.|[^\\'\n])+'")
_RAW_STRING = re.compile(r"b?r(#*)\"")
_CLOSERS = re.compile(r"[)\]}]+[;,]?")
_IDENT = re.compile(r"[A-Za-z_]\w*")


@dataclass(frozen=True)
class ScanLine:
    code: str            # the line without comments, string and char contents blanked
    open_before: str     # brackets open at the start of the line, outermost first
    open_after: str
    in_string: bool      # the line starts inside a string


def scan_braces(lines: list[str], lang: str) -> list[ScanLine]:
    """Bracket nesting line by line, ignoring brackets in strings, chars and comments."""
    out = []
    stack: list[str] = []
    string: str | None = None   # the closing quote (with a raw string's #s) while in a string
    raw = False
    comment = 0                 # block comment depth (Rust's nest)
    for line in lines:
        before, in_string = "".join(stack), string is not None
        code: list[str] = []
        i = 0
        while i < len(line):
            ch = line[i]
            if comment:
                if line.startswith("*/", i):
                    comment, i = comment - 1, i + 2
                elif lang == "rust" and line.startswith("/*", i):
                    comment, i = comment + 1, i + 2
                else:
                    i += 1
                continue
            if string is not None:
                if ch == "\\" and not raw:
                    i += 2
                elif line.startswith(string, i):
                    code.append('"')
                    string, i = None, i + len(string)
                else:
                    i += 1
                continue
            if line.startswith("//", i):
                break
            if line.startswith("/*", i):
                comment, i = 1, i + 2
                continue
            word_before = i > 0 and (line[i - 1].isalnum() or line[i - 1] == "_")
            m = _RAW_STRING.match(line, i) if lang == "rust" and not word_before else None
            if m:
                code.append('"')
                string, raw, i = '"' + m.group(1), True, m.end()
                continue
            if ch == '"':
                code.append('"')
                string, raw, i = '"', False, i + 1
                continue
            if ch == "'":
                m = (_RUST_CHAR if lang == "rust" else _C_CHAR).match(line, i)
                if m:  # otherwise a Rust lifetime or loop label
                    code.append("''")
                    i = m.end()
                    continue
            if ch in _OPENS:
                stack.append(ch)
            elif ch in _CLOSES and stack:
                stack.pop()
            code.append(ch)
            i += 1
        out.append(ScanLine("".join(code).strip(), before, "".join(stack), in_string))
    return out


def brace_logical(lines: list[str], scan: list[ScanLine]) -> list[tuple[int, int]]:
    """(first, last) lines of each step. A line continues the step before it while a ( or [
    or a string is open across it; a line of closing brackets alone joins the step before it,
    so no tap reveals just a `}`. Blank and comment-only lines are left between steps."""
    out: list[tuple[int, int]] = []
    for i, line in enumerate(scan):
        if out and (line.in_string or line.open_before[-1:] in ("(", "[")):
            out[-1] = (out[-1][0], i)
            continue
        if not line.code:
            continue
        if out and _CLOSERS.fullmatch(line.code) \
                and all(lines[j].strip() for j in range(out[-1][1] + 1, i)):
            out[-1] = (out[-1][0], i)
            continue
        out.append((i, i))
    return out


@dataclass(frozen=True)
class Item:
    key: str
    kind: str
    start: int            # 0-based: its attributes and the comments directly above it
    header: int           # its first line of code past the attributes
    end: int              # 0-based, exclusive: past its last line
    signature: bool       # whether its header is a signature worth giving
    prefix: str = ""      # children's name prefix (impl and mod blocks)


def _flat(code: str) -> str:
    """`code` with everything inside brackets removed, keeping the brackets."""
    out, depth = [], 0
    for ch in code:
        if ch in _OPENS:
            if depth == 0:
                out.append(ch)
            depth += 1
        elif ch in _CLOSES:
            depth -= 1
            if depth == 0:
                out.append(ch)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def _strip_generics(text: str) -> str:
    out, depth = [], 0
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def _rust_item(head: str, flat: str) -> tuple[str, str, bool, str]:
    """(key, kind, signature, children's prefix) of a Rust item from its header line."""
    text = re.sub(r"^pub(\([^)]*\))?\s+", "", head)
    text = re.sub(r"^((const|async|unsafe|extern\s+\"[^\"]*\")\s+)+(?=fn\b)", "", text)
    if text.startswith("use "):
        return "imports", "imports", False, ""
    if m := re.match(r"fn\s+(\w+)", text):
        return m.group(1), "function", True, ""
    if m := re.match(r"(struct|enum|union|trait|type)\s+(\w+)", text):
        return m.group(2), "type", m.group(1) != "type", ""
    if m := re.match(r"(const|static)\s+(mut\s+)?(\w+)", text):
        return m.group(3), "assignment", False, ""
    if m := re.match(r"mod\s+(\w+)", text):
        return m.group(1), "module", True, m.group(1) + "::"
    if m := re.match(r"macro_rules!\s*(\w+)", text):
        return m.group(1), "function", True, ""
    if text.startswith("impl"):
        rest = text[4:].lstrip()
        if rest.startswith("<"):  # the impl's own generics
            depth, j = 0, 0
            for j, ch in enumerate(rest):
                depth += (ch == "<") - (ch == ">")
                if depth == 0:
                    break
            rest = rest[j + 1:]
        rest = re.split(r"\s*(\{|\bwhere\b)", rest, maxsplit=1)[0].strip()
        target = rest.split(" for ", 1)[-1]
        return f"impl {rest}", "impl", True, _strip_generics(target).strip() + "::"
    raise ValueError(f"unsupported top-level Rust item {head!r}")


def _c_item(head: str, flat: str) -> tuple[str, str, bool, str]:
    """(key, kind, signature, prefix) of a C declaration, from its header line and the whole
    declaration with bracket contents removed."""
    if re.match(r"#\s*include\b", head):
        return "imports", "imports", False, ""
    if m := re.match(r"#\s*define\s+(\w+)", head):
        return m.group(1), "assignment", False, ""
    if flat.startswith("typedef"):
        call = re.search(r"(?:\(\s*\*\s*)?(\w+)\s*\)?\s*\(", flat)
        if call:
            return call.group(1), "type", False, ""
        return _IDENT.findall(flat.rstrip(";"))[-1], "type", False, ""
    if m := re.match(r"((static|inline|extern)\s+)*(struct|enum|union)\s+(\w+)\s*\{\s*\}\s*;$", flat):
        return m.group(4), "type", True, ""
    eq = flat.find("=")
    call = flat.find("(")
    if call >= 0 and (eq < 0 or call < eq):
        name = _IDENT.findall(flat[:call])[-1]
        if flat.endswith(";"):  # a forward declaration: the definition keeps the name
            return f"{name} (declaration)", "function", False, ""
        return name, "function", True, ""
    stop = min(j for j in (flat.find("["), eq, flat.find(";"), len(flat)) if j >= 0)
    return _IDENT.findall(flat[:stop])[-1], "assignment", False, ""


def brace_items(lines: list[str], scan: list[ScanLine], logical: list[tuple[int, int]],
                lo: int, hi: int, lang: str) -> list[Item]:
    """The items whose statements start in [lo, hi) at the nesting depth of line `lo`, each
    from its attributes and directly-above comments to its last line."""
    depth = len(scan[lo].open_before) if lo < len(scan) else 0
    items: list[Item] = []
    attrs: int | None = None  # first line of pending attributes
    k = 0
    while k < len(logical):
        first, last = logical[k]
        if first < lo or first >= hi or len(scan[first].open_before) != depth:
            k += 1
            continue
        while len(scan[last].open_after) > depth:  # the statement runs to where it closes
            k += 1
            last = logical[k][1]
        k += 1
        head = scan[first].code
        if lang == "rust" and head.startswith("#"):
            attrs = first if attrs is None else attrs
            continue
        start = first if attrs is None else attrs
        attrs = None
        floor = items[-1].end if items else lo
        while start > floor and lines[start - 1].strip() and not scan[start - 1].code:
            start -= 1
        flat = _flat(" ".join(scan[j].code for j in range(first, last + 1)))
        key, kind, sig, prefix = (_rust_item if lang == "rust" else _c_item)(head, flat)
        items.append(Item(key, kind, start, first, last + 1, sig, prefix))
    return items


def _dedupe(keys: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for key in keys:
        seen[key] = seen.get(key, 0) + 1
        out.append(key if seen[key] == 1 else f"{key} #{seen[key]}")
    return out


def _norm(name: str) -> str:
    return name.replace("_", "")


def port_units(text: str, lang: str, cues: dict[str, str]) -> list[dict]:
    """Drill units of a Rust or C source: `use`/`#include` lines as one `imports` unit, then
    each top-level item; `impl` and `mod` blocks have their items as children. `cues` maps
    a normalized name (`_norm`) to a cue borrowed from the Python program."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    scan = scan_braces(lines, lang)
    logical = brace_logical(lines, scan)
    items = brace_items(lines, scan, logical, 0, len(lines), lang)
    merged: list[Item] = []
    for item in items:
        if item.kind == "imports" and merged and merged[-1].kind == "imports":
            merged[-1] = Item("imports", "imports", merged[-1].start, merged[-1].header,
                              item.end, False)
        else:
            merged.append(item)
    units = []
    for i, (item, uid) in enumerate(zip(merged, _dedupe([m.key for m in merged]))):
        start = 0 if i == 0 else item.start  # a file header comment opens the first unit
        end = merged[i + 1].start if i + 1 < len(merged) else len(lines)
        cue_key = item.prefix.removesuffix("::") if item.kind == "impl" else item.key
        unit = make_unit(uid, uid, item.kind, start, end, item.header if item.signature else None,
                         cues.get(_norm(cue_key), ""), lines, logical)
        if item.prefix:
            inner = brace_items(lines, scan, logical, item.header + 1, item.end - 1, lang)
            names = _dedupe([item.prefix + c.key for c in inner])
            unit["children"] = [
                make_unit(name, name, "method" if item.kind == "impl" and c.kind == "function"
                          else c.kind, c.start,
                          inner[j + 1].start if j + 1 < len(inner) else item.end - 1,
                          c.header if c.signature else None, "", lines, logical)
                for j, (c, name) in enumerate(zip(inner, names))]
            if not unit["children"]:
                del unit["children"]
        units.append(unit)
    return units


# --- bundle ---------------------------------------------------------------------------

def _hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _docstring_cue(nodes: tuple[ast.stmt, ...]) -> str:
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node)
            if doc:
                return doc.split("\n\n", 1)[0].replace("\n", " ").strip()
    return ""


def _py_header(nodes: tuple[ast.stmt, ...]) -> int | None:
    """0-based line of the def/class header a unit opens with, if it does."""
    head = nodes[0]
    if isinstance(head, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return head.lineno - 1
    return None


def make_unit(uid: str, name: str, kind: str, span_start: int, span_end: int,
              header: int | None, cue: str, lines: list[str],
              logical: list[tuple[int, int]]) -> dict:
    """`header`: the 0-based line whose step is the unit's signature, or None."""
    end = span_end
    while end > span_start and not lines[end - 1].strip():
        end -= 1
    steps = steps_for(span_start, end, logical)
    body = lines[span_start:end]
    return {
        "id": uid,
        "name": name,
        "kind": kind,
        "cue": cue,
        "signature": None if header is None else steps[header - span_start],
        "hash": _hash("\n".join(body)),
        "gap": span_end - end,
        "lines": [{"text": t, "indent": _indent(t), "step": s} for t, s in zip(body, steps)],
    }


def _kind(nodes: tuple[ast.stmt, ...]) -> str:
    head = nodes[0]
    if isinstance(head, (ast.Import, ast.ImportFrom)):
        return "imports"
    if isinstance(head, ast.ClassDef):
        return "class"
    if isinstance(head, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "function"
    if isinstance(head, ast.If):
        return "main-guard"
    return "assignment"


def group_spans(spans: list[Span], sections: list[dict] | None) -> list[tuple[str, str, Span]]:
    """(id, name, span) per drill unit: one per top-level unit, or sections.toml's sections."""
    if sections is None:
        return [(s.key, s.key, s) for s in spans]
    keys = [s.key for s in spans]
    listed = [sym for sec in sections for sym in sec.get("symbols", [])]
    if listed != keys:
        raise ValueError("sections.toml symbols must list every top-level unit in order:\n"
                         f"  file:   {', '.join(keys)}\n  listed: {', '.join(listed)}")
    out = []
    i = 0
    for sec in sections:
        group = spans[i:i + len(sec["symbols"])]
        nodes = tuple(n for s in group for n in s.nodes)
        name = sec.get("name") or " + ".join(sec["symbols"])
        out.append((group[0].key, name, Span(group[0].key, group[0].start, group[-1].end, nodes)))
        i += len(group)
    return out


def python_units(text: str, sections: list[dict] | None = None) -> list[dict]:
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    tree = ast.parse(text)
    logical = logical_lines(text)
    spans = top_units(tree, lines)
    if spans and spans[0].start:
        raise ValueError("text before the first unit is not supported")
    cues = {}
    if sections is not None:
        cues = {sec["symbols"][0]: sec.get("cue", "").strip() for sec in sections}
    units = []
    for uid, name, span in group_spans(spans, sections):
        unit = make_unit(uid, name, _kind(span.nodes), span.start, span.end,
                         _py_header(span.nodes), cues.get(uid, "") or _docstring_cue(span.nodes),
                         lines, logical)
        children = []
        for node in span.nodes:
            if isinstance(node, ast.ClassDef):
                for m in method_units(node, lines):
                    children.append(make_unit(f"{node.name}.{m.key}", f"{node.name}.{m.key}",
                                              "method", m.start, m.end, _py_header(m.nodes),
                                              _docstring_cue(m.nodes), lines, logical))
        if children:
            unit["children"] = children
        units.append(unit)
    return units


def _read(path: Path) -> str:
    return path.read_text() if path.is_file() else ""


def read_sections(prog: Path) -> list[dict] | None:
    path = prog / "python" / "sections.toml"
    if not path.is_file():
        return None
    return tomllib.loads(path.read_text())["section"]


def unit_starts(units: list[dict]) -> dict[str, int]:
    """0-based line in the drill source where each unit starts, children included."""
    starts: dict[str, int] = {}
    line = 0
    for unit in units:
        starts[unit["id"]] = line
        texts = [x["text"] for x in unit["lines"]]
        at = 0
        for child in unit.get("children", []):
            run = [x["text"] for x in child["lines"]]
            while texts[at:at + len(run)] != run:
                at += 1
            starts[child["id"]] = line + at
            at += len(run)
        line += len(unit["lines"]) + unit["gap"]
    return starts


def read_starts(units: list[dict], drill: str, read: str) -> dict[str, int]:
    """Where each unit starts in the read source: the annotated solution is the drill source
    with comment lines added, so each unit's lines are found there, and the annotation
    comments directly above a unit start it."""
    starts = unit_starts(units)
    if drill == read:
        return starts
    a, b = drill.split("\n"), read.split("\n")
    where: dict[int, int] = {}
    for block in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for j in range(block.size):
            where[block.a + j] = block.b + j
    missing = [a[i] for i in range(len(a)) if i not in where and a[i].strip()]
    if missing:
        raise ValueError(f"read source lacks drill lines, e.g. {missing[0]!r}")
    mapped = set(where.values())
    out = {}
    for uid, line in starts.items():
        at = where[line]
        while at > 0 and at - 1 not in mapped and b[at - 1].lstrip().startswith(("//", "/*", "*")):
            at -= 1
        out[uid] = 0 if line == 0 else at
    return out


def python_cues(sections: list[dict] | None) -> dict[str, str]:
    """The Python program's cues by normalized symbol name, for its ports to borrow."""
    return {_norm(sym): sec.get("cue", "").strip()
            for sec in sections or [] for sym in sec.get("symbols", [])}


def make_impl(prog: Path, pattern: str, lang: str, units: list[dict], drill: str,
              read: str) -> dict:
    ldir = prog / lang
    return {
        "id": f"{prog.name}/{pattern}/{lang}",
        "variant": pattern,
        "lang": lang,
        "docs": {"problem": _read(ldir / "problem.md"), "notes": _read(ldir / "notes.md")},
        "readSource": read,
        "readStarts": read_starts(units, drill, read),
        "units": units,
    }


def build(corpus: Path) -> dict:
    programs = []
    for tier in TIERS:
        tier_dir = corpus / tier
        if not tier_dir.is_dir():
            continue
        for prob in sorted(tier_dir.iterdir()):
            meta_path = prob / "meta.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text())
            pattern = meta["pattern"]
            sections = read_sections(prob)
            text = (prob / "python" / "solution.py").read_text()
            impls = [make_impl(prob, pattern, "python", python_units(text, sections), text, text)]
            cues = python_cues(sections)
            for lang, ext in PORT_EXT.items():
                source = prob / lang / f"solution.{ext}"
                if not source.is_file():
                    continue
                drill = source.read_text()
                annotated = prob / lang / f"annotated_solution.{ext}"
                read = annotated.read_text() if annotated.is_file() else drill
                impls.append(make_impl(prob, pattern, lang, port_units(drill, lang, cues),
                                       drill, read))
            programs.append({
                "id": prob.name,
                "title": prob.name.replace("-", " "),
                "tier": tier,
                "tags": meta.get("tags", []),
                "docs": {"spec": _read(prob / "SPEC.md"), "defense": _read(prob / "DEFENSE.md")},
                "impls": impls,
            })
    body = json.dumps(programs, sort_keys=True)
    return {"version": _hash(body), "programs": programs}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    bundle = build(args.corpus.expanduser())
    text = json.dumps(bundle, separators=(",", ":")) + "\n"
    impls = sum(len(p["impls"]) for p in bundle["programs"])
    # Rewriting an unchanged bundle would make watching dev servers rebuild for nothing.
    unchanged = args.out.is_file() and args.out.read_text() == text
    if not unchanged:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(f"build_bundle: {len(bundle['programs'])} programs, {impls} impls -> {args.out} "
          f"(version {bundle['version']}{', unchanged' if unchanged else ''})")


if __name__ == "__main__":
    main()
