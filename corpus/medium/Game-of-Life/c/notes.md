Python source: `python/solution.py`

- Representation: chosen differently from Python. The Python version keeps a set
  of live coordinates, because Python's `set` is built in and `step` then checks
  the grid's edges only once, at the end. C's standard library has no set, and
  the grid is at most 100 × 100, so this version stores one `bool` per cell: a
  dense grid of 10,000 bytes, with no hashing and no heap allocation.
- The step keeps Python's way of counting: each live cell adds one to its eight
  neighbors' counts, as `Counter` does. The counts array has a one-cell border,
  so a count that falls off the grid lands in the border and is never read. The
  border replaces Python's final `0 <= r < rows` check.
- The parser reads a line at a time with `fgets` into a buffer one grid row
  long, and the header with `sscanf("%d %d %d %c")`, where a fourth match means
  something follows the three numbers. `%d` skips any whitespace and takes a
  sign, as Python's `int` does after `split()`. A grid line keeps a `\r`, so
  `\r\n` input is bad input here. A header number too big for `int` is undefined
  behavior in `sscanf` (`strtol` would detect it); SPEC says nothing about it.
- `read_world` takes a `FILE *`, so it reads a pattern from any stream, not
  only stdin.
- Python contrasts and idioms: annotated in the reference above.
- O(rows · cols) per generation, whatever the population; Python's `step` is
  O(live cells), though printing a generation is O(rows · cols) in every version.
