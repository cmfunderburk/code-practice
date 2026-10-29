Python source: `python/solution.py`

- Move: parse everything, then evaluate, as in Python. `tokenize` and the
  recursive-descent parser build a tree; `evaluate` walks it. One grammar rule
  is one function, and the loops in `parse_term` and `parse_expr` make the
  binary operators left-associative.
- The tree lives in one array per line. Nodes refer to their children by index
  rather than pointer, so the whole tree is freed with one `free`. A line of
  `len` bytes has at most `len` tokens and at most one node per token, so both
  arrays are sized before parsing and never grow.
- Python's `int | float` becomes a tagged union, `Value`. Integer arithmetic
  goes through C23's `ckd_add`, `ckd_sub`, and `ckd_mul`, so a result too big for
  `int64_t` reports an error instead of overflowing, where Python's integers
  would simply grow.
- Floats print with `%.15g`: 15 significant digits, trailing zeros dropped. It
  is not Python's shortest round-trip text, and doesn't need to be.
- Python contrasts and idioms: annotated in the reference above.
- O(len) per line, with recursion as deep as the parentheses nest.
