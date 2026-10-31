## How it works

The program is an interpreter: it reads a line of source, turns it into commands,
and runs them against a drawing.

A `Drawing` is a frozen dataclass holding everything the user can see: the
turtle's position, its heading (an index into `HEADINGS`, `"ENWS"`), whether the
pen is down, and the tuple of segments drawn so far. Because it is frozen, no code
changes a drawing; each command builds a new one.

A `Command` is also a frozen value: an `op` name and its argument, which is a
distance for `forward`, a `(count, body)` pair for `repeat`, and `None` for the
rest. `Command.apply(drawing)` returns the drawing after the command. A `repeat`
runs its body `count` times, passing the result of each child's `apply` to the
next.

`parse` turns a line into a tuple of commands. It puts spaces around the
brackets, converts the line to uppercase, splits it into words, and passes the
words to `_parse`, which calls itself for each `REPEAT` block. `render` turns a
parsed program back into text, in uppercase with single spaces, and parsing that
text gives back an equal program.

`Logo` holds the current drawing and an undo stack. `execute` parses the whole
line first. Then, for each top-level command, it keeps the drawing as `before`,
applies the command, and pushes `command.inverse(before)`, a `Restore` holding
`before`. `undo` pops the latest `Restore` and applies it, which puts the saved
drawing back. `REPEAT 4 [ FORWARD 2 LEFT ]` is one top-level command, so it is one
undo entry, although its `apply` runs eight child commands.

Worked check: `FORWARD 2 LEFT FORWARD 3` takes the turtle from (0, 0) heading E
to (2, 0) heading E, then (2, 0) heading N, then (2, 3) heading N. Three top-level
commands push three `Restore`s. One undo removes the last segment but keeps the
heading N that `LEFT` set.

**Complexity.** Parsing and rendering take time proportional to the number of
words, $O(t)$. Running a line takes time proportional to the number of commands it
runs once every `REPEAT` is expanded, $O(e)$, plus $O(s)$ for each segment drawn,
because `segments += ...` copies the tuple: drawing s segments one at a time costs
$O(s^2)$ in all. `undo` is $O(1)$: one pop and one assignment. Each saved drawing
has its own copy of the segments tuple (the segment pairs inside are shared), so h
entries over s segments hold up to $O(h \cdot s)$ tuple slots. At the sizes this
program is used for, neither cost is noticeable.

## `main`

`main()` reads one line at a time with `input()` until end of input. `UNDO` is not
part of the Logo language, so `main` handles it: `_is_undo` checks whether the
line's only word is `UNDO`, in any case, and if so `main` calls `logo.undo()`.
Every other line, an empty one included, goes to `logo.execute`. After either call
succeeds, `main` prints `_report(logo)`: the state line, then one `x1,y1 -> x2,y2`
line per segment. A `ValueError` from either call prints as one line,
`error: <message>`, and because `execute` parses the whole line before applying
anything, a rejected line changes nothing.

## Design choices

- **Saving the drawing, not replaying.** Each top-level command pushes a
  `Restore` holding the drawing from before it, so undo is one pop and one
  assignment. Another design keeps the parsed commands as the history, and undoes
  by applying all but the last again from an empty drawing. It stores less, but
  every undo redoes the whole session. Either design can keep a whole `REPEAT` as
  one entry.
- **A saved drawing, not a computed inverse.** `Command.inverse` returns
  `Restore(before)` for every command. An inverse computed from the command alone,
  such as `PENDOWN` for `PENUP`, would be wrong after `PENUP PENUP`, where undoing
  the second `PENUP` must leave the pen up. For a very large drawing, an inverse
  could save only what a command can change: the position, heading, pen, and how
  many segments there were. The C and Rust versions do this.
- **Commands that apply themselves.** Each `Command` has its own `apply`, so a
  `REPEAT` runs its block by calling `apply` on the commands in it. Another design
  stores commands as plain tuples and looks up a handler function for each op in
  a dictionary. Here the behavior lives in `apply`'s branches; in either design,
  `_parse` names the commands.
- **Parse everything, then apply.** `execute` calls `parse` on the whole line
  before the first `apply`, so `FORWARD 1 SPIN` moves nothing. Applying while
  parsing would leave the turtle moved by a line that is then reported as an
  error.
- **Quarter turns only.** `LEFT` and `RIGHT` turn by exactly 90°, so every
  coordinate stays an integer, and the drawing can be printed and compared
  exactly. Turns by any angle would need floating-point coordinates, with rules
  for rounding and printing them.
- **A drawing every version prints the same way.** The segment lines,
  `x1,y1 -> x2,y2` oldest first, are the program's output, so the Python, C, and
  Rust versions all write them the same way. Printing `logo.segments` as a Python
  tuple would give a format the other two languages don't naturally produce. The
  state line above the segments is each version's own wording.
- **End of input ends the session; an empty line is an empty program.** `main`
  catches `EOFError` from `input()` and returns, so a session piped from a file
  ends with exit status 0, not a traceback. `parse("")` is already a valid empty
  program, so `main` runs an empty line like any other and prints the report.
- **Python's own words and numbers.** `parse` splits with `str.upper` and
  `str.split`, so tabs, `\r`, and Unicode spaces all separate words. `_positive`
  reads numbers with `int`, so `+3`, `007`, and `1_000` are numbers. SPEC lets each
  version read these its own way.
- **Python's limits.** Coordinates never overflow, but Python refuses to convert
  an integer of more than 4,300 digits to or from a string. For a longer literal,
  `int()` raises `ValueError`, which `main` reports as an error line. But two
  `FORWARD`s of 4,300 nines move the turtle to an x of 4,301 digits, and then
  `str()` raises inside `_report`, which `main` calls in the `else` branch of its
  `try`, outside the `except`, so the program stops with a traceback. About a
  thousand nested `REPEAT`s exceed Python's recursion limit in `_parse`, a
  `RecursionError` that `main` doesn't catch either. Both break SPEC §2's rule
  that the exit status is 0. The C and Rust versions have different limits: their
  64-bit coordinates can overflow, which they report as an error line, and they
  handle a thousand nested `REPEAT`s.

## Where this shows up again

Most interpreters have the stages this program has: a tokenizer (the split in
`parse`), a parser (`_parse`), an evaluator (`Command.apply` and `Logo.execute`),
and a read-eval-print loop (`main`). `render`, the parser in reverse, is what an
interpreter calls its *printer*. Two larger examples:

- A Lisp interpreter has the same stages for a real language. Its reader turns
  nested parenthesized lists into data, as `_parse` turns nested `REPEAT` blocks
  into commands, and its printer turns values back into text. It adds names,
  environments, closures, and tail calls. One written in several languages may
  keep integers in signed 64 bits and make overflow an error, so that every
  version agrees, as the C and Rust versions here do with coordinates.
- A text editor's undo and redo keep a history of edits as `Logo` keeps a history
  of commands.
