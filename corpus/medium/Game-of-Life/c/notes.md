Python source: `python/solution.py`

- Move: representation choice, made differently. Python keeps a set of
  live coordinates because a set is free and the step stays bounds-free until
  one final clip. C has no set, and the grid is at most 100 × 100, so a dense
  `bool` grid is the natural representation: 10 KB, no hashing, no heap.
- The step keeps Python's scatter: each live cell adds one to its eight
  neighbors' counts, as `Counter` does. The counts array has a one-cell border,
  so a count that falls off the grid lands in the border and is never read. The
  border replaces Python's final `0 <= r < rows` clip.
- The parser reads a line at a time with `fgets` into a buffer one grid row
  long, and the header with `sscanf("%d %d %d %c")`, where a fourth match means
  junk after the three numbers. `%d` takes any spacing and a sign, as Python's
  `int` does; a grid line keeps a `\r`, so `\r\n` input is bad input here. A
  header number too big for `int` is undefined behavior in `sscanf` (`strtol`
  would catch it), a C fact SPEC doesn't cover.
- `read_world` takes a `FILE *`, so it reads a pattern from any stream, not
  only stdin.
- Python contrasts and idioms: annotated in the reference above.
- O(rows · cols) per generation, whatever the population; Python's set is
  O(live cells).
