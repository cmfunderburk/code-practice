## Table Render — worked example

**Intuition.** The program's real lesson is the BOUNDARY: numerals are
text, ints are the representation you compute on, and `to_roman` /
`from_roman` are the renderer and parser facing each other across it. The
render side is one descending value→symbol table with the subtractive pairs
as first-class rows, then a greedy walk — `divmod` off each value, append
`symbol * count`. The table IS the algorithm; get its 13 rows right and the
code is three lines.

Worked check: 1990 → M (990 left) → CM (90) → XC (0) → `"MCMXC"`.

**Complexity.**
- Time: $O(1)$ — 13 table rows, at most 15 output symbols; Space: $O(1)$.

**Discussed, not drilled.** `from_roman` assumes canonical input — real
validation (rejecting `"IIII"` or `"IXIX"`) is a parsing drill for another
day; the cheap version is the round-trip check `to_roman(from_roman(s)) == s`,
which the shell applies to every numeral line. SPEC §1 states a genuinely
different formulation: per-decimal-digit positional tables.

**The shell.** `main()` is a line-by-line two-way dispatcher read with
`input()`. It trims the line and folds it to uppercase, since a person at a
terminal who types ` mcmxc ` means `MCMXC`. ASCII digits render through
`to_roman`, whose `out of range` error it prints. Numeral letters parse
through `from_roman`, but only after `_canonical` renders the parse back and
compares it with the line. Every refusal is one `error: <message>` line. Each
direction is the other's oracle — run the program and feed it its own output.

## Shapes chosen and rejected

- **One descending table with the subtractive pairs as rows (chosen)** over
  a **greedy parse** as the half that defines canonical form. Both are halves
  of one boundary. Rendering puts all thirteen rules in data, so the code is a
  three-line walk; parsing puts the subtractive rule in one symbol of lookahead
  and can't tell canonical input from junk.
- **The round-trip law as the validator.** `from_roman` alone accepts any
  string of numeral letters: `IIII` is 4, `IM` is 999, `MMMM` is 4000. A
  canonical-form regex would be a second statement of the grammar, kept in
  sync with the table by hand. Rendering the parse back and comparing reuses
  the table, so one definition of "canonical" serves both directions. The
  check catches `to_roman`'s `ValueError` too, because a run of fifteen `M`s
  parses to 15000, which has no numeral.
- **Python's own reading of a line.** The shell strips the line and
  upper-cases it. A shell that did only that and trusted `str.isdigit` would
  print 0 for an empty line, 4000 for `MMMM`, `XLII` for `٤٢` (Arabic-Indic
  digits), and crash with a traceback on `0` or `hello`. The bugs there are the
  missing canonical check, the empty line, and the uncaught errors, not the
  trimming.
  A strict reader, nothing stripped or folded, one to four digits, one to
  fifteen letters, read as bytes, would let one exact transcript match Python,
  C, and Rust alike, at the cost of each language's own reading. So the shell
  trims and folds, keeps `isascii()` beside `isdigit()` so only ASCII digits
  are a number, and checks every numeral by the round trip. Numbers have
  no length cap: Python's `int` takes any size, and anything past 3999 is out
  of range (past 4,300 digits `int` itself refuses, with a `ValueError` the
  shell reports the same way).
- **Refusals say `error`.** Every refused line prints `error: <message>`, the
  convention all three implementations share, and the only fact about a
  refusal SPEC §4 fixes. The numerals themselves are the program's data and
  the same in every implementation.

## Scales up to

A Lisp interpreter is built on **parser / renderer separation (reader and
printer)**. Its reader turns text into data and its printer turns data back
into text, as `from_roman` and `to_roman` do here, at the size of a language:
integers, booleans, strings, symbols, and nested lists. A key-value store's
persistence makes the round trip load-bearing. When its append-only log is
stored in the wire protocol (RESP, say), the log format is the wire format,
and replay at startup parses what the renderer wrote. A renderer and parser
that disagree there lose data, not just a validation check.
