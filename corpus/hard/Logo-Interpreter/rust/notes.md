Python source: `python/solution.py`

- Move: command objects, as in Python. The parser builds a tree of `Command`
  values (`Forward`, `Turn`, `Pen`, `Repeat` holding its block), and `run`
  performs one against the turtle and the drawing. The whole line parses before
  anything runs, so a line with a mistake changes nothing.
- History records how to restore the state, one entry per top-level command,
  as Python's `Restore` values do. Python's entry holds the whole previous
  `Drawing`. Here an entry is the previous `Turtle`, which is `Copy`, plus the
  number of segments: commands only ever append segments, so `truncate` to that
  number restores the drawing. An entry is a few machine words, not a copy of
  the drawing.
- LEFT and RIGHT become `Turn(1)` and `Turn(3)`, quarter turns counterclockwise,
  and PENUP and PENDOWN become `Pen(bool)`, so `run` has four arms.
- Words and numbers are Rust's: brackets get spaces around them, as in Python,
  then `split_whitespace` and `to_ascii_uppercase`; numbers are
  `parse::<i64>`, which takes `+3` and `007` but not Python's `1_000`.
- Coordinates are `i64`. `run` returns `Option<()>` and moves with
  `checked_mul` and `checked_add`, so an overflow is `None` passed up with `?`.
  `execute` then restores the line's first undo entry and returns an error, so
  the failing line changes nothing. Unchecked, a debug build would panic.
- `io::stdin().lines()` reads each line without its `\n` or `\r\n`; a line that
  isn't UTF-8 is an `Err`, and `map_while(Result::ok)` stops there.
- The report is built as one `String` and printed with one `print!`.
- Python contrasts and idioms: annotated in the reference above.
- O(T) to parse a line of T tokens, O(C) to run C commands, and O(S) to print
  S segments; an undo is O(1) plus the print.
