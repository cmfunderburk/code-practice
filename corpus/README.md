# The corpus

The programs the app drills. `scripts/build_bundle.py` reads this directory and writes
`src/generated/bundle.json`, which the app imports. The server runs it at startup, so
restart the server (or run `bun run bundle`) after changing anything here. Set
`CODE_PRACTICE_CORPUS` to build from a corpus somewhere else.

## Layout

```
corpus/<tier>/<Program>/          tier: easy, medium or hard
  meta.json                       {"tags": ["game-logic"], "pattern": "functional-core"}
  SPEC.md                         the program's contract, shared by every language
  DEFENSE.md                      oral-defense questions with folded answers
  test_program.py                 smoke suite: SPEC's fixed output, run in every language
  python/
    solution.py                   the reference implementation, drilled as is
    sections.toml                 drill units: grouping and cues
    problem.md                    the Python implementation's API and approach
    notes.md                      why it is shaped this way, what was rejected
    test_solution.py              core tests
  rust/  and  c/
    solution.rs / solution.c      the port, drilled as is
    annotated_solution.*          the port plus comment lines, shown in the read view
    problem.md  notes.md          the port's own contract and notes
    test_solution.rs / .c         core tests
    Cargo.toml  Cargo.lock        (Rust) so `cargo run` works in the directory
```

- **The program's name** is its directory name, with hyphens shown as spaces (`Game-of-Life` is
  "Game of Life"). Its **pattern** is the architectural idea the Python implementation
  demonstrates. It is shown beside the title and is part of each implementation's id.
- **Every file but `python/solution.py` and `meta.json` is optional.** If a document is
  missing, its tab is hidden. If a port directory has no `solution.*`, that language is
  absent. If a port has no `annotated_solution.*`, the read view shows its `solution.*`.
- **Renaming a program, or a unit within it, starts its drill history fresh.** Progress is keyed
  by program, pattern, language and unit name. Editing a unit's code keeps its history but marks
  it *changed*.

## Units

A **unit** is what one drill covers: you see its cue, recall the code, and reveal it.

**Python** is split with `ast`:

- all imports form one unit, `imports`;
- each top-level `def`, `class` and named assignment is a unit, in file order (a tuple
  assignment `WIDTH, HEIGHT = 7, 5` is the unit `WIDTH`);
- the `if __name__ == "__main__":` guard is a unit, `__main__`;
- comments and decorators directly above a unit belong to it;
- a class's methods are its **children**. You can drill the whole class or one method.

Any other top-level statement is an error, and so is text before the first unit.

**Rust and C** are split by bracket matching that understands strings, chars, lifetimes and
comments. Each top-level item is a unit: `fn`, `struct`, `enum`, `trait`, `type`, `static` and
`const` in Rust, and functions, typedefs and globals in C. A run of `use` or `#include` lines is
one unit. Items inside `impl` and `mod` blocks become children (`Game::new`). A C forward
declaration is its own unit, `name (declaration)`.

### `sections.toml`

`sections.toml` lists every top-level Python unit in file order, grouped into drill units, each
with a **cue**: the one or two sentences you recall the code from.

```toml
title = "Hangman"            # informational

[[section]]
symbols = ["imports"]
cue = "What the program needs: a random source to pick the word, ..."

[[section]]
name = "main"                # optional; the default joins the symbols with " + "
symbols = ["main", "__main__"]
cue = "Composition root: ..."
```

- The symbols must be exactly the file's top-level units, in order. The build fails and shows
  both lists if they differ.
- The ports **borrow** the Python cues by name, ignoring underscores but not case, so the Rust
  `require_live` takes the cue of `_require_live`. An `impl` block takes its type's cue.
- Without a `sections.toml`, each top-level unit is its own drill unit, cued by the first
  paragraph of its docstring. The tests expect every program to have one.

### Reveal steps

A **step** is what one tap reveals:

- A **Python** step is one logical line. A statement that continues over several lines (open
  brackets, backslash) is one step.
- A **Rust or C** step is one line, continued while a `(` or `[` or a string is open. A line
  that holds only closing brackets (`}`, `};`, `});`) reveals with the step before it.
- In every language, blank lines and comment-only lines reveal with the line after them, and a
  unit's trailing blank lines are dropped.

## Documents

The documents are Markdown, rendered by `src/markdown/`. It supports:

- headings, paragraphs, fenced code, nested lists, block quotes, pipe tables and rules;
- inline code, bold, italic, strikethrough and `==highlight==`;
- Obsidian callouts: `> [!answer]- Title` is folded until tapped.

Links show only their text, because the app has nothing to open.

- **`SPEC.md`** is what the program does, in terms every language can meet: rules, input,
  output, and a sample session. Its fixed-output section names the only output facts every
  implementation keeps. Everything else is each implementation's own wording.
- **`python/problem.md`** gives the Python API (signatures, types, what raises) and how
  `main()` runs the program. **`python/notes.md`** gives the intuition, complexity, the shapes
  chosen and rejected, and what the design grows into at scale.
- **`DEFENSE.md`** holds questions to answer aloud, grouped as lifecycle, trade-offs,
  adversarial, scale and across languages, each with a folded answer that cites `SPEC.md`, the
  notes or the code. It opens with a committee prompt for rehearsing the questions with an LLM.
- **A port's `problem.md`** gives its contract (types and signatures in that language) and how
  it differs from the Python version. **Its `notes.md`** gives the language-specific moves.
  **`annotated_solution.*`** must be `solution.*` with comment lines added and nothing else
  changed. The build fails if any line of `solution.*` is missing from it.

## Tests

```bash
uv run pytest corpus                        # every program, every language
uv run pytest corpus/easy/Hangman           # one program
uv run pytest corpus -k "python"            # the smoke suite in one language, plus Python's tests
```

Rust needs `cargo`, and C needs a `cc` that supports `-std=c23` (a recent GCC or Clang). A
missing toolchain skips its language. Builds go to `.build/` at the repo root. `bun run verify`
runs these tests along with the app's.

- **Core tests** check one implementation's API directly. The Python tests (`python/test_solution.py`)
  get the module as the `sub` fixture, freshly imported for each test. `rust/test_solution.rs`
  is compiled as a child module of the solution (`use super::*;`), so it reaches private
  items. `c/test_solution.c` includes `solution.c`, renaming its `main`, and is built with
  UBSan.
- **The smoke suite** (`test_program.py`) runs the whole program on stdin through the
  `run_program` fixture, once per language. It checks only what SPEC's fixed-output section
  fixes, because all other wording is each implementation's own.

The fixtures and the build steps live in `corpus/conftest.py`.

`.claude/skills/add-program/` walks an agent through writing a new program in this format.
