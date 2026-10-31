Python source: `python/solution.py`

- Parse the whole line, then evaluate, as in Python. `tokenize` and the
  recursive-descent parser build a tree, and `evaluate` walks it. Each grammar
  rule is one function, and the loops in `parse_term` and `parse_expr` make the
  binary operators group from the left.
- The tree lives in one array per line. Nodes refer to their children by index
  rather than by pointer, so the whole tree is freed with one `free`. A line of
  `len` bytes has at most `len` tokens and at most one node per token, so both
  arrays are sized before parsing and never grow.
- Python's `int | float` becomes a tagged union, `Value`: a `bool` that says
  which member of the union holds the number. Integer arithmetic goes through
  C23's `ckd_add`, `ckd_sub`, and `ckd_mul`, so a result too big for `int64_t`
  is reported as `error: integer overflow` instead of being undefined behavior.
  Python's integers would simply grow. A literal too big for `int64_t` is
  `error: number too large`.
- `main` reads lines of any length with `getchar`, growing the buffer as it
  goes, and stops at end of input or an empty line. It removes only the `\n`, so
  a line ending in `\r\n` keeps its `\r` and is refused as an unknown character,
  as in Python.
- Floats print with `%.15g`: 15 significant digits, trailing zeros dropped, so
  `1/3` prints `0.333333333333333` and `8/2` prints `4`. This is not Python's
  shortest text, and SPEC §4 doesn't require it to be.
- Python contrasts and idioms: annotated in the reference above.
- O(len) per line, with recursion as deep as the tree: as deep as the
  parentheses nest, or as long as a run of operators at one level.
