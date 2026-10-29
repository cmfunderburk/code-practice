Python source: `python/solution.py`

- Move: command objects, as in Python, but stored flat. A parsed line is one
  growable array of 24-byte `Command`s in preorder; a `REPEAT` records its
  `span`, the size of its body with nested blocks, so the body is the next
  `span` entries and the parse builds no pointers.
- Undo is a memento, as Python's `Restore(before)` is. The snapshot is a
  32-byte `Turtle`: position, heading, pen, and the segment count. Segments
  are only ever appended, so each earlier drawing is a prefix of the current
  one, and restoring the count drops what the undone command drew. One
  snapshot per top-level command; undo copies no segments.
- The `Logo` (72 bytes) owns two growable arrays, the 32-byte segments and the
  snapshots; the token and program arrays are reused from line to line.
  Everything is freed at exit.
- The parser returns `false` up the recursion where Python raises, leaving the
  message and the token it blames in the `Parser`. Nothing runs until the
  whole line parses.
- Words are C's: `tokenize` splits at `isspace` and makes each bracket a token,
  keeping pointers into the line, and `is` compares through `toupper`. Numbers
  are `strtoll`'s: a sign and leading zeros are fine, `1_000` is an error (Python's
  `int` accepts it), and a value past `int64_t` sets `errno`.
- Coordinates are `int64_t`, and `apply` moves with `ckd_mul` and `ckd_add`.
  When a move would overflow, `apply` returns `false` up through `run`, and
  `logo_execute` puts back the line's first snapshot, so the failing line
  changes nothing, as a syntax error doesn't. Python's integers never overflow.
- `read_line` grows a buffer with `getchar`, so a long `REPEAT` line arrives
  whole; a fixed `fgets` buffer would cut it into two programs. It
  NUL-terminates the line, which `strtoll` needs.
- Python contrasts and idioms: annotated in the reference above.
- O(tokens) to parse a line, O(commands run) to execute it, and O(segments) to
  print the drawing after each line, as in Python.
