Python source: `python/solution.py`

- Move: command objects, as in Python, but stored in one flat array. A parsed
  line is one growable array of 24-byte `Command`s in preorder, each `REPEAT` just
  before its body. A `REPEAT` records its `span`, the number of entries in its
  body including nested blocks, so its body is the next `span` entries and the
  parse builds no pointers.
- An undo entry saves the state from before a command, as Python's
  `Restore(before)` does, but it is smaller: a 32-byte `Turtle` holding the
  position, heading, pen, and the segment count. Segments are only ever added at
  the end, so each earlier drawing is the first part of the current one, and
  putting back the count drops what the undone command drew. There is one entry
  per top-level command, and undo copies no segments.
- The `Logo` (72 bytes) owns two growable arrays, the 32-byte segments and the
  undo entries; the token and program arrays are reused from line to line.
  Everything is freed at exit.
- The parser returns `false` up the recursion where Python raises, leaving the
  message and the token it blames in the `Parser`. Nothing runs until the whole
  line parses.
- Words are C's: `tokenize` splits at `isspace` and makes each bracket a token,
  keeping pointers into the line, and `is` compares through `toupper`. Numbers are
  `strtoll`'s: a sign and leading zeros are fine, `1_000` is an error (Python's
  `int` accepts it), and a value too large for `int64_t` sets `errno`.
- Coordinates are `int64_t`, and `apply` moves with `ckd_mul` and `ckd_add`. When
  a move would overflow, `apply` returns `false` up through `run`, and
  `logo_execute` puts back the first undo entry pushed for the line, so the
  failing line changes nothing, just as a line with a syntax error changes
  nothing. Python's integers never overflow.
- `read_line` grows a buffer with `getchar`, so a long `REPEAT` line arrives
  whole; a fixed `fgets` buffer would cut it into two programs. It ends the line
  with a NUL byte, which `strtoll` needs.
- Python contrasts and idioms: annotated in the reference above.
- O(tokens) to parse a line, O(commands run) to execute it, and O(segments) to
  print the drawing after each line, as in Python.
