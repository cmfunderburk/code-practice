## AST Eval — worked example

**Intuition.** The parser-renderer boundary, second home (after Roman
Numerals): text goes through a real representation before anything is
computed. Three pure stages — `tokenize` flattens characters to tokens,
`parse` builds the tagged-tuple AST by recursive descent (one helper per
precedence level, each returning `(node, next_pos)`), `evaluate` folds the
tree with `match`/`case`. This is the natural implementation because the
representation is what makes the program a *program*: each stage is
independently testable, and the AST is the seam where a pretty-printer,
simplifier, or compiler would attach without touching the parser.

Worked check: `"2+3*4"` → tokens `["2", "+", "3", "*", "4"]` → `_term`
binds the `*` first → `("+", ("num", 2), ("*", ("num", 3), ("num", 4)))` →
14.

**Complexity.**
- Time: $O(n)$ over tokens; Space: $O(n)$ tree + $O(d)$ recursion depth.

**Discussed, not drilled.** `eval()` IS this program — one call replaces
all three functions, which is exactly why it is banned from the solution. A
renderer (`to_infix`, enabling the `parse(render(t)) == t` round-trip) is
rejected: a calculator never prints its AST, and bolting one on would break
the move-is-the-lesson rule.

**The shell.** A REPL over stdin: one expression per line read with `input()`,
results printed as Python prints them, `ValueError` and `ZeroDivisionError`
reported as `error:` lines, an empty line or end of input ends it. `calculate` still *raises* `ZeroDivisionError`, as its API
contract says. It is the shell that turns it into output, because one bad line
shouldn't end a session.

## Shapes chosen and rejected

- **AST evaluation (chosen)** over **single-pass evaluation**, where each grammar
  level returns a value instead of a node. Single-pass is shorter and allocates no
  tree, but nothing exists between text and number, so nothing else can attach.
  The tree is where a printer, simplifier, or compiler would plug in, and where
  `parse` can be tested without evaluating anything.
- **Parse everything, then evaluate.** `calculate` builds the whole tree before
  `evaluate` runs, so `1+(2` reports a parse error and computes nothing. A
  single-pass evaluator interleaves the two; here that is harmless only because
  arithmetic has no effects.
- **Python's own printing.** `evaluate` returns Python numbers, and the shell
  prints them with `print`: integers exactly, floats as the shortest text that
  reads back to the same float (`3.5`, `0.3333333333333333`, `4.0` for `8/2`).
  A `_format` helper that rounds floats to six places, so Python, C, and Rust
  print the same bytes, is rejected: C's `printf` can't reproduce Python's
  `repr`, and matching it would bend the implementation toward a byte format.
  Each language prints a number its own way, and SPEC §4 fixes values, not text.
- **Python's limits are Python's.** Integers never overflow, but `int()` refuses
  a literal of more than 4,300 digits (a `ValueError`, so the shell reports it)
  and a few thousand nested parentheses exceed the recursion limit (a
  `RecursionError`, which the shell does not catch). A port has the opposite
  limits: fixed-width integers that overflow, and a C stack that can be far
  deeper. Neither is part of the calculator's spec.
- **ASCII-only tokens.** `tokenize` tests `" \t"` and `"0123456789"`, not
  `str.isspace` and `str.isdigit`. Those accept Unicode spaces and digits, so
  `int("٣")` would quietly read as 3, which no calculator user means.

## Scales up to

A Lisp interpreter is this program grown into a language:
- `tokenize` and `parse` become a reader that keeps source locations for error
  messages, and a printer renders values back to text.
- "Parse everything, then evaluate" becomes a rule over whole batches: reading
  finishes before evaluation begins, so malformed source can't partially execute.
- `evaluate`'s `match` over tagged tuples becomes an evaluator with special forms,
  lexical environments, closures, and tail calls, plus a dispatch table of
  primitives.
- Lisp values can outlive the line that made them, so they need collection,
  which this calculator never needs.
