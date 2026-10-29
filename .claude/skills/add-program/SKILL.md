---
name: add-program
description: Add a new program to this repo's corpus (corpus/<tier>/<Program>/), with its Python reference implementation, sections.toml cues, Rust and C ports, and SPEC, DEFENSE, problem and notes documents. Use when the user wants a new program to read and drill, or wants to port an existing corpus program to a language it lacks.
---

# Add a program to the corpus

The format is defined in `corpus/README.md`. Read it first, and read one existing program
end to end before you write anything. `corpus/easy/Hangman` is the smallest. Read
`corpus/medium/Editor-Buffer` too if the new program has classes. The bar is set by those
programs, not by this skill.

## 1. Agree on the program

Before you write any code, settle these with the user:

- **The program.** A small, complete, terminal program with a real design decision in it. It
  should be 40 to 160 lines of Python. A game, a parser, an interpreter, a simulation or a tool
  all work. An algorithm exercise does not, because the corpus studies architecture: how state,
  rules and I/O are arranged.
- **The pattern.** The architectural idea the Python implementation will demonstrate, in
  kebab-case: `functional-core`, `table-render`, `command-objects`, `verb-dispatch` and so on.
  Name the alternative it is chosen over, because the notes and DEFENSE are built on that
  contrast.
- **The tier.** Choose easy, medium or hard by comparing with the existing programs of that tier.
- **The languages.** Python is required. Rust and C are expected unless the user says otherwise.

If the idea comes from a book or website, write the program from the idea. Don't copy its code,
text, word lists or messages.

## 2. Write `SPEC.md` first

`SPEC.md` is the contract every language meets:

- the rules;
- how the program is played or used on stdin and stdout;
- a sample session;
- a **fixed output** section naming the only output facts every implementation must keep.
  Everything else is each implementation's own wording.

Write it in the voice of the existing specs: short sections, exact rules, and no API.

## 3. Write the Python implementation

Write `python/solution.py` as the reference implementation of the pattern:

- Use top-level units only: imports, constants, classes and functions, plus a `main()` and the
  `if __name__ == "__main__":` guard. Each unit should be recallable from one cue. If a unit
  needs a paragraph to cue it, split it.
- Comments explain *why*, sparingly. Docstrings are fine.
- Run it and play it. Check every rule in `SPEC.md` by hand, or with a throwaway script outside
  the corpus.

Then write `python/sections.toml`:

- List every top-level unit in order. Group units only when they are recalled together, such as
  `main` and `__main__`.
- Write one cue per section, in the existing style. Start with the unit's role ("Derived view:",
  "Transition:", "Composition root:"), then give the facts needed to write the code without
  dictating it: names, messages and edge cases.

Then write `python/problem.md` and `python/notes.md`, following Hangman's. `problem.md` gives the
rules in brief, examples, the API with signatures, and what `main()` does. `notes.md` covers:

- **Intuition**;
- **Complexity**;
- **Discussed, not drilled**;
- **Shapes chosen and rejected**, where each bullet is a design alternative and why it lost,
  written in the present tense;
- **Scales up to**: the larger kind of system this idea grows into.

## 4. Write the ports

For each port, write `rust/solution.rs` or `c/solution.c`:

- Write the natural program in that language, with the same architecture as the Python version.
  Don't transliterate it.
- Rust: std only, unless a crate is the ordinary choice (`rand`). Say so in the port's
  `problem.md`.
- C: C23, with `static` functions and no allocation unless the design needs it.
- Name items so the Python cues carry over. `_require_live` gives its cue to `require_live`.
  `corpus/README.md` explains the borrowing.
- Compile and run each port, and play the sample session from `SPEC.md`.

Then write `annotated_solution.*`, which is the same file with comment lines added. They explain
the language-specific moves and contrast them with the Python version. Don't change any existing
line.

Write the port's `problem.md`: the contract in that language's types, then "Differences from the
Python version". Write its `notes.md` as bullets of language-specific moves, ending with the
complexity. The first line is `Python source: \`python/solution.py\``.

## 5. Write `DEFENSE.md` last

It needs everything above. Copy the structure of an existing `DEFENSE.md`:

- the intro and the committee prompt, with this program's attachment paths;
- questions grouped as **Lifecycle** (trace an input through the code), **Trade-offs** (why this
  shape over the rejected ones), **Adversarial** (bad input, end of input, edge cases),
  **Scale** (what the idea grows into) and **Across languages** (how the ports meet the same
  design);
- each question followed by a folded `> [!answer]-` callout. The callout leads with the decisive
  point and cites `SPEC.md`, the notes or the code by section.

Every claim must be true of the code as written. Check each one against the source.

## 6. Write the tests

Write the tests alongside the code. They are how you check that the program meets `SPEC.md`,
and that each port meets its contract. The tests section of `corpus/README.md` explains how
they run. Copy the shape of an existing program's tests.

- **`test_program.py`**, the smoke suite, checks only the fixed-output facts in `SPEC.md`,
  through the `run_program` fixture, so it runs unchanged against all three languages. Where
  expected output is computed, compute it with a small, independent oracle in the test file
  (a plain replay of SPEC's rules), never by calling an implementation.
- **`python/test_solution.py`** tests the API from `python/problem.md` through the `sub`
  fixture: the rules, every refusal, and `main()` with `sys.stdin` and `random` monkeypatched.
- **`rust/test_solution.rs`** starts with `use super::*;`, and
  **`c/test_solution.c`** wraps `#include "solution.c"` in `#define main <program>_main` and
  `#undef main`. Each tests its port's core API with plain `assert`s.
- **Rust ports** need `rust/Cargo.toml` with `[[bin]] path = "solution.rs"`, plus a
  `Cargo.lock` (`cargo generate-lockfile`).

Run `uv run pytest corpus/<tier>/<Program>` until it passes in every language.

## 7. Check

```bash
bun run bundle     # fails loudly on a sections.toml mismatch or a bad annotated file
bun run verify     # typecheck, app tests, bundle tests, and every program's tests
```

Then run `bun run dev`, open the program in the app, and check three things:

- the read view;
- every document tab;
- a whole-program drill in each language, to confirm the cues read well and the step boundaries
  feel right.
