Python source: `python/solution.py`

- Move: parse everything, then evaluate, as in Python. `tokenize` makes a
  `Vec<Token>`, the recursive-descent `Parser` builds a tree, and `evaluate`
  walks it. One grammar rule is one method, and the loops in `term` and
  `expr` make the binary operators left-associative.
- The tree is an enum with boxed children, Rust's usual tree. Python's tagged
  tuples become variants that `match` checks exhaustively.
- `Value` is an enum, `Int(i64)` or `Float(f64)`, Python's `int | float`.
  Integer arithmetic uses `checked_add`, `checked_sub`, `checked_mul`, and
  `checked_neg`, so a result too big for `i64` reports an error instead of
  panicking, where Python's integers would simply grow.
- The shell reads with `io::stdin().lines()`, stops at the first empty line
  with `take_while`, and prints each value with `Display`.
- Every stage returns `Result<_, String>`, and `?` passes an error up the way
  Python's `raise` does.
- Python contrasts and idioms: annotated in the reference above.
- O(len) per line, with recursion as deep as the parentheses nest.
