# Editor Buffer — Command Objects

A text buffer that you edit by position, with unlimited undo and redo: the core of
every text editor. `insert(pos, s)` inserts `s` at `pos`, where `0 <= pos <=
len(text)`, so inserting at the end is legal. `delete(pos, n)` removes exactly `n`
characters, where `n >= 1` and `pos + n <= len(text)`. `undo()` reverses the most
recent edit that hasn't been undone, and `redo()` reapplies the most recently
undone edit. **Every successful edit clears the redo history**, and undo and redo
are not edits themselves. A call that breaks these rules raises `ValueError` and
changes nothing: an out-of-range edit leaves both histories as they were, and an
undo or redo with nothing to undo or redo raises instead of doing nothing.

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

Record every edit as a *command object*: a small value that holds what the edit
did, knows how to apply itself to a text, and can produce its inverse, the edit
that reverses it.

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
    text: str                      # the REMOVED text, saved when the Delete is built
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

The buffer keeps two stacks of commands, one for undo and one for redo. `undo`
pops a command, applies its inverse, and pushes the command on the redo stack;
`redo` pops a command, applies it again, and pushes it back on the undo stack.
`delete` must save the text it removes in the `Delete` it builds, because the
inverse, an insert, needs that text and the buffer is about to lose it.

Around the buffer sit the import, `HELP`, the input helpers (`_number` and
`_command`), and `main()`. `main()` reads one command per line with `input()`,
with no prompt, until `q` or end of input. `_command` parses each line
(`i <pos> <text>`, `d <pos> <n>`, `u`, `r`, `p`, `q`, with numbers written in
ASCII digits), and a line it can't parse gets the `HELP` line. `main()` calls the
buffer's methods, prints the buffer's `ValueError` message as it is, and prints
the text between `"` for `p`. Positions count characters (Unicode code points), as
Python's `str` does. The full behavior is in `SPEC.md`.
