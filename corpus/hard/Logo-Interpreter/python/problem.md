# Logo Interpreter — Command Objects

Implement a tiny orthogonal Logo interpreter. Source is case-insensitive and
contains these whitespace-separated commands:

- `FORWARD n` moves a positive integer distance;
- `LEFT` and `RIGHT` turn exactly 90 degrees;
- `PENUP` and `PENDOWN` control whether movement emits a line segment;
- `REPEAT n [ ... ]` repeats a nonnegative-depth nested command block `n`
  times, where `n` is positive.

The turtle starts at `(0, 0)`, heading east, with its pen down. Coordinates
are exact integers; north increases y. A segment is `(start, end)`. Invalid
syntax, unknown commands, and nonpositive distances/counts raise `ValueError`.

Parsing produces a real command representation and `render(parse(source))`
emits canonical uppercase source with single spaces. Parsing that canonical
source must reproduce an equal program.

`Logo.execute(source)` executes each TOP-LEVEL command as one history entry.
In particular, a whole `REPEAT` is atomic. `Logo.undo()` restores the drawing
from before the most recent top-level command; underflow raises `ValueError`.
Rejected source changes neither drawing nor history.

Required surface:

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

Represent every parsed command as an immutable value with a pure
`apply(drawing) -> drawing` operation. When the engine applies a top-level
command, ask it for an inverse restoration value and push that value onto the
undo stack. Nested repeat commands compose the same pure operation without
leaking their children into top-level history.

Around the commands, the parser/renderer, and the `Logo` engine sits the REPL:
`_is_undo`, `_report`, and `main()`. The shell reads one line at a time with
`input()` until end of input. A line whose
only word is `UNDO`, in any case, calls `undo`; every other line, an empty one
included, goes to `execute`. After each success it prints `_report`'s state line
and then the drawing, one `x1,y1 -> x2,y2` line per segment, and a `ValueError`
prints as `error: <message>` with the session continuing. The interpreter itself is
`SPEC.md`.
