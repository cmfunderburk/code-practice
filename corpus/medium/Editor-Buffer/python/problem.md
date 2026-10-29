# Editor Buffer — Command Objects

A text buffer with positional editing and unlimited undo/redo — the core
of every editor. `insert(pos, s)` inserts at `pos` (`0 <= pos <=
len(text)`, so inserting at the end is legal); `delete(pos, n)` removes
exactly `n >= 1` characters (`pos + n <= len(text)`). `undo()` and
`redo()` restore buffer states; **any successful edit clears the redo
stack**, and undo/redo do not themselves count as edits. Illegal calls
raise `ValueError` and change nothing: out-of-range edits must leave both
history stacks untouched, and undo/redo with nothing to undo/redo refuse
rather than no-op.

## Examples

```
EditorBuffer()          text ""
.insert(0, "hello")     text "hello"
.insert(5, " world")    text "hello world"
.delete(0, 6)           text "world"
.undo()                 text "hello world"
.undo()                 text "hello"
.redo()                 text "hello world"
.insert(0, "big ")      text "big hello world"; redo() now raises
```

Constraints: positions and counts are ints; the buffer is plain text.

## Command Objects

Reify every edit as a value that knows how to apply itself and how to
produce its inverse:

```python
@dataclass(frozen=True)
class Insert:
    pos: int
    text: str
    def apply(self, text: str) -> str
    def invert(self) -> "Delete"

@dataclass(frozen=True)
class Delete:
    pos: int
    text: str                      # the REMOVED text, captured at creation
    def apply(self, text: str) -> str
    def invert(self) -> Insert

class EditorBuffer:
    def __init__(self, text: str = "") -> None
    @property
    def text(self) -> str
    def insert(self, pos: int, s: str) -> None
    def delete(self, pos: int, n: int) -> None
    def undo(self) -> None
    def redo(self) -> None
```

The buffer keeps two stacks of commands: undo pops and applies the
inverse; redo pops and re-applies. `delete` must capture the removed text
when it builds the `Delete` — that is what makes the inverse exist.

The surrounding program — imports, `HELP`, the input helpers (`_number`,
`_command`), and the `main()` shell — wraps the buffer. The shell reads one
command per line with `input()`, with no prompt, until `q` or end of input.
`_command` parses it (`i <pos> <text>`, `d <pos> <n>`, `u`, `r`, `p`, `q`,
numbers as ASCII digits), and a line it rejects gets the `HELP` line. The shell calls the buffer's methods, prints the
buffer's `ValueError` as is, and prints the text between `"` for `p`. Positions
count characters (code points), as Python's `str` does. The editor itself is
`SPEC.md`.
