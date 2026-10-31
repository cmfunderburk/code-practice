## How it works

The calculator turns a line of text into a number in three stages, and none of
them reads input or prints:

1. `tokenize` splits the text into tokens: runs of digits, operators, and
   parentheses. It skips spaces and tabs and raises `ValueError` for any other
   character.
2. `parse` builds an abstract syntax tree (AST) from the tokens. It is a
   recursive-descent parser: one helper per grammar rule (`_expr`, `_term`,
   `_factor`), each taking a position in the token list and returning the node it
   built with the position after it. The nodes are tagged tuples: `("num", 7)`,
   `("neg", node)`, and `(op, left, right)`.
3. `evaluate` computes the tree's value. Its `match`/`case` recognises each
   node's shape and calls itself on the children.

`calculate` is `evaluate(parse(tokenize(text)))`.

Worked check: `"2+3*4"` → tokens `["2", "+", "3", "*", "4"]`. `_expr` asks `_term`
for its first operand, which is `2`, sees `+`, and asks `_term` again. That second
`_term` reads `3`, sees `*`, reads `4`, and returns `("*", ("num", 3), ("num", 4))`.
So the tree is `("+", ("num", 2), ("*", ("num", 3), ("num", 4)))`, and `evaluate`
gives 14. The `*` ends up lower in the tree because `_term`, the helper for the
level below `+`, built it.

**Complexity.** Time $O(n)$ for $n$ tokens. Space $O(n)$ for the tree, plus
recursion as deep as the tree. Nested parentheses make the tree deep, and so does a
long run of operators at one level: `1+1+1+1` is a tree of three `+` nodes, each
the left child of the next.

**How the tests check it.** Python's `eval` computes the same values with the same
precedence, so the tests compare `calculate` with `eval` on 200 random
expressions, requiring the same value and the same type (`int` or `float`). They
also check the exact tuples `parse` returns, and call `evaluate` on trees built by
hand.

## `main`

`main()` reads one expression per line with `input()`, and stops at end of input or
at an empty line. It prints each value with `print`, so integers print exactly and
floats as Python prints them. `calculate` raises `ValueError` for a malformed line
and `ZeroDivisionError` for division by zero; `main` catches both and prints
`error: <message>`, so one bad line doesn't end the session.

## Design choices

- **A tree, rather than computing while parsing.** A shorter calculator has
  `_expr`, `_term`, and `_factor` return numbers instead of nodes: `_term` reads
  `3`, sees `*`, reads `4`, and returns 12. That version builds no tree, but it
  also has nothing to show between text and number. With a tree, `parse` can be
  tested without evaluating anything, and another function could use the same tree
  (to print it, simplify it, or compile it) without touching the parser. Parsing
  also finishes before evaluation starts, so `1/0+(2` is reported as
  `error: expected )`, while a calculator that computes as it parses reaches `1/0`
  first and reports division by zero. In exchange, the tree takes one tuple per
  node, and `evaluate` adds a second recursive pass (see the last item).
- **No `eval`.** Python's `eval` would replace all three stages with one call,
  which is why the solution doesn't use it, and why the tests can use it as the
  reference.
- **Python's own printing.** `main` prints numbers with `print`: integers exactly,
  and floats as the shortest text that reads back as the same float (`3.5`,
  `0.3333333333333333`, and `4.0` for `8/2`). The C version's `printf` can't
  produce that text, so the three versions could print the same text only if all
  of them rounded every float to a fixed number of places. SPEC §4 compares values
  to nine significant digits instead, so each version prints a number the usual
  way for its language.
- **Python's limits.** Integers never overflow. But `int()` refuses a literal of
  more than 4,300 digits with a `ValueError`, which `main` prints as an `error:`
  line. And recursion is limited to 1,000 Python calls by default. Each pair of
  parentheses takes three calls (`_factor`, `_expr`, `_term`), so about 330 nested
  pairs raise `RecursionError` in `parse`. `parse` reads `1+1+...+1` with a loop,
  but the tree it builds leans left, one level per `+`, so a sum of about 1,000
  ones raises `RecursionError` in `evaluate`. `main` doesn't catch
  `RecursionError`, so either line ends the program with a traceback and exit
  status 1. The C and Rust versions have the opposite limits: 64-bit integers that
  overflow, and recursion limited only by the size of the stack, which holds
  thousands of nested parentheses before the program crashes.
- **ASCII-only tokens.** `tokenize` tests characters against `" \t"` and
  `"0123456789"`, not with `str.isspace` and `str.isdigit`. Those two accept
  Unicode spaces and digits from other scripts, so `٣` (Arabic-Indic 3) would read
  as 3, which no user of a calculator means.

## Where this shows up again

A language interpreter is this program grown larger. A Lisp interpreter, for
example, has the same stages:

- `tokenize` and `parse` become a *reader*, which turns source text into nested
  lists and remembers where each came from (line and column) so that error
  messages can point at it. A *printer* turns values back into text.
- "Parse everything, then evaluate" becomes a rule over whole batches of input:
  reading finishes before evaluation begins, so malformed source never runs
  halfway.
- `evaluate`'s `match` becomes an evaluator with special forms (such as `if` and
  `define`, which decide which of their parts run), variables looked up in
  environments, functions that remember the variables around them, and a table of
  built-in functions.
- Lisp values can outlive the line that made them, so an interpreter written in C
  or Rust needs a garbage collector. This calculator forgets everything after each
  line.
- A careful reader refuses nesting past a fixed depth (a couple of hundred lists,
  say) with a syntax error, so a deeply nested input can't exhaust the stack: the
  problem this calculator has with a few hundred nested parentheses.
