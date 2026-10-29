import textwrap

import pytest

import build_bundle as bb

PROGRAMS = len(list(bb.CORPUS.glob("*/*/meta.json")))


def src(text: str) -> str:
    return textwrap.dedent(text).lstrip("\n")


def joined(unit: dict) -> list[str]:
    return [line["text"] for line in unit["lines"]] + [""] * unit["gap"]


def step_texts(unit: dict) -> list[list[str]]:
    out: list[list[str]] = []
    for line in unit["lines"]:
        while len(out) <= line["step"]:
            out.append([])
        out[line["step"]].append(line["text"])
    return out


# --- units --------------------------------------------------------------------------

SAMPLE = src('''
    import sys
    from dataclasses import dataclass

    LIMIT = 6


    # The state.
    @dataclass(frozen=True)
    class State:
        """Immutable game state."""
        n: int

        def bump(self) -> "State":
            return State(self.n + 1)

        # Classmethod constructor.
        @classmethod
        def zero(cls) -> "State":
            return cls(0)


    def total(xs: list[int],
              start: int = 0) -> int:
        # running sum
        acc = start
        for x in xs:
            acc += x
        return acc


    if __name__ == "__main__":
        print(total([1, 2]))
''')


def test_top_level_units_and_round_trip():
    units = bb.python_units(SAMPLE)
    assert [u["id"] for u in units] == ["imports", "LIMIT", "State", "total", "__main__"]
    assert [u["kind"] for u in units] == ["imports", "assignment", "class", "function",
                                          "main-guard"]
    assert sum((joined(u) for u in units), []) == SAMPLE.split("\n")[:-1]


def test_comments_and_decorators_belong_to_the_unit_below():
    state = bb.python_units(SAMPLE)[2]
    assert state["lines"][0]["text"] == "# The state."
    assert state["lines"][1]["text"] == "@dataclass(frozen=True)"


def test_trailing_blanks_are_a_gap_not_lines():
    imports, limit = bb.python_units(SAMPLE)[:2]
    assert imports["lines"][-1]["text"] == "from dataclasses import dataclass"
    assert imports["gap"] == 1
    assert limit["gap"] == 2


def test_methods_are_children():
    state = bb.python_units(SAMPLE)[2]
    children = state["children"]
    assert [c["id"] for c in children] == ["State.bump", "State.zero"]
    assert children[1]["lines"][0]["text"].strip() == "# Classmethod constructor."
    assert children[1]["lines"][-1]["text"].strip() == "return cls(0)"
    assert children[0]["gap"] == 1


def test_docstring_is_the_fallback_cue():
    assert bb.python_units(SAMPLE)[2]["cue"] == "Immutable game state."
    assert bb.python_units(SAMPLE)[3]["cue"] == ""


def test_unsupported_top_level_statement_is_an_error():
    with pytest.raises(ValueError, match="unsupported"):
        bb.python_units("print('hi')\n")


# --- steps --------------------------------------------------------------------------

def test_multiline_statement_is_one_step_and_comments_join_the_next():
    total = bb.python_units(SAMPLE)[3]
    assert step_texts(total) == [
        ["def total(xs: list[int],", "          start: int = 0) -> int:"],
        ["    # running sum", "    acc = start"],
        ["    for x in xs:"],
        ["        acc += x"],
        ["    return acc"],
    ]


def test_signature_step():
    units = bb.python_units(SAMPLE)
    assert units[2]["signature"] == 1          # after the comment + decorator step
    assert units[3]["signature"] == 0
    assert units[0]["signature"] is None
    assert units[2]["children"][1]["signature"] == 1


def test_docstring_is_one_step():
    text = src('''
        def f():
            """One.

            Two.
            """
            return 1
    ''')
    assert [len(s) for s in step_texts(bb.python_units(text)[0])] == [1, 4, 1]


def test_trailing_comment_joins_the_last_step():
    text = "def f():\n    return 1\n    # done\n"
    assert step_texts(bb.python_units(text)[0]) == [["def f():"], ["    return 1", "    # done"]]


def test_indent_recorded():
    lines = bb.python_units(SAMPLE)[3]["lines"]
    assert [line["indent"] for line in lines] == [0, 10, 4, 4, 4, 8, 4]


# --- sections.toml --------------------------------------------------------------------

def test_sections_group_units_and_supply_cues():
    sections = [
        {"symbols": ["imports"], "cue": "Deps."},
        {"symbols": ["LIMIT", "State"], "cue": "Data."},
        {"name": "main", "symbols": ["total", "__main__"], "cue": "Run."},
    ]
    units = bb.python_units(SAMPLE, sections)
    assert [(u["id"], u["name"], u["cue"]) for u in units] == [
        ("imports", "imports", "Deps."),
        ("LIMIT", "LIMIT + State", "Data."),
        ("total", "main", "Run."),
    ]
    assert [c["id"] for c in units[1]["children"]] == ["State.bump", "State.zero"]
    assert units[1]["signature"] is None
    assert sum((joined(u) for u in units), []) == SAMPLE.split("\n")[:-1]


def test_sections_must_cover_every_unit_in_order():
    with pytest.raises(ValueError, match="every top-level unit"):
        bb.python_units(SAMPLE, [{"symbols": ["imports", "LIMIT"]}])


# --- Rust and C -------------------------------------------------------------------------

RUST = src("""
    //! Demo: whole program.

    use std::io::{self, BufRead};

    use demo::Game;

    const NAMES: [&str; 2] = [
        "a {",
        "b",
    ];

    #[derive(Clone, Copy)]
    struct Pos<'a> {
        name: &'a str,
    }

    // A trait.
    trait Choose {
        fn choose(&mut self) -> usize;
    }

    impl<'a> Choose for Pos<'a> {
        fn choose(&mut self) -> usize {
            0
        }

        // Second.
        fn other(&self) -> char {
            '}'
        }
    }

    mod demo {
        pub struct Game;
    }

    fn main() {
        let s = r#"not a { brace"#; /* nor } this */
        println!(
            "{}",
            s
        );
        match s.len() {
            0 => {
                return;
            }
            _ => {}
        }
    }
""")


def test_rust_items_and_round_trip():
    units = bb.port_units(RUST, "rust", {})
    assert [(u["id"], u["kind"]) for u in units] == [
        ("imports", "imports"), ("NAMES", "assignment"), ("Pos", "type"), ("Choose", "type"),
        ("impl Choose for Pos<'a>", "impl"), ("demo", "module"), ("main", "function")]
    assert sum((joined(u) for u in units), []) == RUST.split("\n")[:-1]
    assert units[0]["lines"][0]["text"] == "//! Demo: whole program."   # the file header


def test_rust_attributes_and_comments_belong_to_the_item():
    units = bb.port_units(RUST, "rust", {})
    assert units[2]["lines"][0]["text"] == "#[derive(Clone, Copy)]"
    assert units[2]["signature"] == 1
    assert units[3]["lines"][0]["text"] == "// A trait."
    assert units[1]["signature"] is None


def test_impl_and_mod_blocks_have_children():
    units = bb.port_units(RUST, "rust", {})
    impl, mod = units[4], units[5]
    assert [c["id"] for c in impl["children"]] == ["Pos::choose", "Pos::other"]
    assert [c["kind"] for c in impl["children"]] == ["method", "method"]
    assert impl["children"][1]["lines"][0]["text"] == "    // Second."
    assert [c["id"] for c in mod["children"]] == ["demo::Game"]


def test_brace_steps_continue_open_parens_and_fold_closers():
    main = bb.port_units(RUST, "rust", {})[-1]
    assert step_texts(main) == [
        ["fn main() {"],
        ['    let s = r#"not a { brace"#; /* nor } this */'],
        ["    println!(", '        "{}",', "        s", "    );"],
        ["    match s.len() {"],
        ["        0 => {"],
        ["            return;", "        }"],
        ["        _ => {}", "    }", "}"],
    ]
    names = bb.port_units(RUST, "rust", {})[1]
    assert len(step_texts(names)) == 1     # a bracketed literal is one step


def test_chars_and_lifetimes_dont_unbalance():
    impl = bb.port_units(RUST, "rust", {})[4]
    other = impl["children"][1]
    assert [x["text"] for x in other["lines"][-2:]] == ["        '}'", "    }"]


C = src("""
    // Demo: whole program.

    #include <stdio.h>
    #include <string.h>

    constexpr int SIZE = 3;
    static const char *const NAMES[] = {"a", "}"};

    typedef enum { RED, GREEN } Color;
    typedef void Command(int arg);

    typedef struct {
        int x;
    } Point;

    struct Node {
        int value;
    };

    static int add(int a, int b);

    static int add(int a,
                   int b) {
        return a + b;
    }

    int main(void) {
        printf("%c\\n", '{');
        return 0;
    }
""")


def test_c_items_and_round_trip():
    units = bb.port_units(C, "c", {})
    assert [(u["id"], u["kind"]) for u in units] == [
        ("imports", "imports"), ("SIZE", "assignment"), ("NAMES", "assignment"),
        ("Color", "type"), ("Command", "type"), ("Point", "type"), ("Node", "type"),
        ("add (declaration)", "function"), ("add", "function"), ("main", "function")]
    assert sum((joined(u) for u in units), []) == C.split("\n")[:-1]
    assert step_texts(units[8])[0] == ["static int add(int a,", "               int b) {"]
    assert units[5]["signature"] is None and units[8]["signature"] == 0


def test_ports_borrow_python_cues_by_name():
    cues = bb.python_cues([{"symbols": ["imports"], "cue": "Deps."},
                           {"symbols": ["_add"], "cue": "Adds."},
                           {"symbols": ["point"], "cue": "Not the type."}])
    units = {u["id"]: u for u in bb.port_units(C, "c", cues)}
    assert units["imports"]["cue"] == "Deps."
    assert units["add"]["cue"] == "Adds."
    assert units["Point"]["cue"] == ""


def test_read_starts_skip_added_comments():
    units = bb.port_units(C, "c", {})
    read = C.replace("static int add", "// Added note.\nstatic int add")
    starts = bb.read_starts(units, C, read)
    lines = read.split("\n")
    assert lines[starts["add"]] == "// Added note."
    assert lines[starts["main"]] == "int main(void) {"
    assert starts["imports"] == 0


# --- the real corpus ------------------------------------------------------------------

@pytest.fixture(scope="module")
def bundle():
    return bb.build(bb.CORPUS)


def test_corpus_python_rust_and_c_per_problem(bundle):
    assert len(bundle["programs"]) == PROGRAMS
    for prog in bundle["programs"]:
        assert [i["lang"] for i in prog["impls"]] == ["python", "rust", "c"], prog["id"]
        assert prog["docs"]["spec"] and prog["docs"]["defense"], prog["id"]
        for impl in prog["impls"]:
            assert impl["docs"]["problem"] and impl["docs"]["notes"], impl["id"]


def drill_source(prog: dict, impl: dict) -> str:
    if impl["lang"] == "python":
        return impl["readSource"]
    path = (bb.CORPUS / prog["tier"] / prog["id"] / impl["lang"]
            / f"solution.{bb.PORT_EXT[impl['lang']]}")
    return path.read_text()


def test_corpus_round_trip(bundle):
    for prog in bundle["programs"]:
        for impl in prog["impls"]:
            text = drill_source(prog, impl)
            got = sum((joined(u) for u in impl["units"]), [])
            assert got == text.split("\n")[:-1], impl["id"]
            for unit in impl["units"]:
                for child in unit.get("children", []):
                    body = "\n".join(line["text"] for line in child["lines"])
                    assert body in "\n".join(line["text"] for line in unit["lines"]), child["id"]


def test_corpus_ids_unique_and_steps_dense(bundle):
    for prog in bundle["programs"]:
        for impl in prog["impls"]:
            flat = [u for unit in impl["units"] for u in [unit, *unit.get("children", [])]]
            ids = [u["id"] for u in flat]
            assert len(ids) == len(set(ids)), impl["id"]
            for u in flat:
                steps = [line["step"] for line in u["lines"]]
                assert steps == sorted(steps) and steps[0] == 0, u["id"]
                assert set(steps) == set(range(steps[-1] + 1)), u["id"]


def test_corpus_python_units_follow_sections(bundle):
    """Every program has a sections.toml, and every Python unit is one of its sections, cued."""
    for prog in bundle["programs"]:
        sections = bb.read_sections(bb.CORPUS / prog["tier"] / prog["id"])
        assert sections is not None, prog["id"]
        impl = prog["impls"][0]
        names = [sec.get("name") or " + ".join(sec["symbols"]) for sec in sections]
        assert [u["name"] for u in impl["units"]] == names, prog["id"]
        assert all(u["cue"] for u in impl["units"]), prog["id"]


def test_corpus_read_starts_point_at_each_unit(bundle):
    for prog in bundle["programs"]:
        for impl in prog["impls"]:
            read = impl["readSource"].split("\n")
            for unit in impl["units"]:
                for u in [unit, *unit.get("children", [])]:
                    at = impl["readStarts"][u["id"]]
                    first = next(x["text"] for x in u["lines"] if x["text"].strip())
                    # the unit's first line, or annotation comments directly above it
                    while read[at] != first:
                        assert read[at].lstrip().startswith(("//", "/*", "*")) or at == 0 \
                            or not read[at].strip(), (impl["id"], u["id"])
                        at += 1
