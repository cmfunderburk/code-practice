Python source: `python/solution.py`

- Parse the whole line, then evaluate, as in Python. `tokenize` makes a
  `Vec<Token>`, the recursive-descent `Parser` builds a tree, and `evaluate`
  walks it. Each grammar rule is one method, and the loops in `term` and `expr`
  make the binary operators group from the left.
- The tree is an enum whose children are in `Box`es, the usual way to write a
  tree in Rust. Python's tagged tuples become enum variants, and `match` must
  cover every one.
- `Value` is an enum, `Int(i64)` or `Float(f64)`, for Python's `int | float`.
  Integer arithmetic uses `checked_add`, `checked_sub`, `checked_mul`, and
  `checked_neg`, so a result too big for `i64` is reported as
  `error: integer overflow` instead of panicking (in a debug build) or wrapping
  around (in a release build). Python's integers would simply grow. A literal
  too big for `i64` is `error: number too large`.
- Every stage returns `Result<_, String>`, and `?` passes an error up the way
  Python's `raise` does.
- `main` reads with `io::stdin().lines()`, which removes a `\r\n` line ending
  as well as `\n`, and stops at the first empty line with `take_while`. It
  prints each value with `{}`: an `f64` prints as the shortest text that reads
  back as the same number, like Python, but `8/2` prints `4`, not `4.0`, and a
  very large or very small float is written out in full, never in exponent
  notation.
- Python contrasts and idioms: annotated in the reference above.
- O(len) per line, with recursion as deep as the tree: as deep as the
  parentheses nest, or as long as a run of operators at one level.
