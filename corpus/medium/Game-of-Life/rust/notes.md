Python source: `python/solution.py`

- Representation: the same as Python's. Rust's standard library has `HashSet`
  and `HashMap`, so live cells stay a set and the step counts neighbors the way
  Python's `Counter` does. The C version, whose standard library has no set,
  stores a dense grid instead.
- Coordinates are `usize`, so a neighbor above row 0 or left of column 0 can't
  exist. `checked_add_signed` returns `None` for it, and the final filter checks
  only the bottom and right edges.
- `parse_input` reads like Python's: `lines()` (which also strips a `\r\n`),
  `split_whitespace()` and `parse` for the header, then the row checks, and
  returns a `Result` whose `Err` is the message. Unlike Python's `int`,
  `parse::<usize>()` refuses a minus sign, so a header of `1 1 -0` is bad input
  here.
- Python contrasts and idioms: annotated in the reference above.
- O(live cells) per generation for the step, plus O(rows · cols) to print.
