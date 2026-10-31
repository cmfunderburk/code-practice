# Logo Interpreter — Command Objects

Implement an interpreter for a small drawing language in the style of Logo. A
program steers a *turtle*: a point on a grid that has a heading and a pen. When
the turtle moves with its pen down, it draws a line segment. Source is
case-insensitive, and is made of these commands, separated by whitespace:

- `FORWARD n` moves the turtle `n` cells in its heading, where `n` is a positive
  integer;
- `LEFT` and `RIGHT` turn it exactly 90 degrees;
- `PENUP` and `PENDOWN` lift and lower the pen, which decides whether a move draws
  a segment;
- `REPEAT n [ ... ]` runs the commands in brackets `n` times, where `n` is
  positive. Blocks may nest inside each other to any depth, and may be empty.

The turtle starts at `(0, 0)`, heading east, with its pen down. Coordinates are
exact integers, and north increases y. A segment is a pair `(start, end)` of
points. A syntax error, an unknown command, or a distance or count below 1 raises
`ValueError`.

`parse(source)` turns source into a tuple of `Command` objects, and
`render(program)` turns such a tuple back into source: uppercase, with single
spaces between words. Parsing the rendered source must give back an equal
program.

`Logo.execute(source)` runs a program. Each top-level command, meaning one that is
not inside a `REPEAT` block, is one history entry, so a whole `REPEAT` is one
entry. `Logo.undo()` restores the drawing from before the most recent entry, and
raises `ValueError` when there is nothing to undo. Source that raises
`ValueError` changes neither the drawing nor the history.

Required functions and class:

```python
def parse(source: str) -> tuple[Command, ...]
def render(program: tuple[Command, ...]) -> str

class Logo:
    position: tuple[int, int]
    heading: str                 # "E", "N", "W", or "S"
    pen_down: bool
    segments: tuple[tuple[tuple[int, int], tuple[int, int]], ...]
    def execute(self, source: str) -> None
    def undo(self) -> None
```

## Examples

```text
FORWARD 2 LEFT FORWARD 3
  -> position (2, 3), heading N
  -> segments (((0, 0), (2, 0)), ((2, 0), (2, 3)))

REPEAT 4 [ FORWARD 2 LEFT ]
  -> returns to (0, 0), heading E, drawing a square
```

## Command Objects

Every parsed command is an immutable value with a pure method
`apply(drawing) -> drawing`: it returns a new drawing and changes nothing else.
When `Logo` applies a top-level command, it asks the command for an inverse, an
object whose `apply` restores the drawing from before, and pushes it onto the undo
stack. A `REPEAT` command applies its block by calling the same `apply` on each
command in it, so those commands never become history entries of their own.

Around `Command`, `Restore`, the parser and renderer, and `Logo` sit the imports,
`VECTORS`, `HEADINGS`, `Drawing`, `_is_undo`, `_report`, and `main()`. `main()`
reads one line at a time with `input()` until end of input. A line whose only
word is `UNDO`, in any case, calls `undo`; every other line, an empty one
included, goes to `execute`. After each success it prints `_report`'s state line
and then the drawing, one `x1,y1 -> x2,y2` line per segment. A `ValueError`
prints as `error: <message>`, and the session continues. The full behavior is in
`SPEC.md`.
