## Command Objects — worked example

**Intuition.** This is the natural capstone implementation because all
four layers have values at their boundaries: source becomes a command tree,
commands transform an immutable drawing, rendering walks the same tree in the
opposite direction, and history stores explicit inverse restoration commands.
`REPEAT 4 [ FORWARD 2 LEFT ]` is one value and therefore one undo entry even
though its pure `apply` operation composes eight child applications.

Worked check: `FORWARD 2 LEFT FORWARD 3` transforms `(0, 0, E)` first to
`(2, 0, E)`, then `(2, 0, N)`, then `(2, 3, N)`. Three top-level commands mean
three restoration values. One undo removes the final segment but preserves
the northward heading established by the second command.

**Complexity.** Parsing and rendering are $O(t)$ in tokens. Execution is
$O(e)$ in expanded primitive commands, plus $O(s)$ for each drawn segment,
because `segments += ...` copies the tuple: drawing s segments costs $O(s^2)$.
Undo is $O(1)$ because the inverse is a saved immutable drawing. Each saved
drawing holds its own copy of the segments tuple (the segment pairs inside are
shared), so h top-level entries over s segments hold up to $O(h \cdot s)$ tuple
slots. Both costs are invisible at this program's sizes.

**Discussed, not drilled.** Saving a drawing snapshot is deliberately simple;
for a huge canvas, an inverse command could retain only the changed position,
heading, pen bit, and segment suffix. A replay version makes the opposite tradeoff:
commands stay plain tagged data and undo recomputes by replay. Arbitrary-angle
trigonometry is excluded because floating formatting would distract from the
parser/history/composition lesson.

**The shell.** `main()` reads one source line at a time with `input()` until end of
input and handles `UNDO` as a REPL control rather than Logo syntax: a line whose only
word is `UNDO` calls `undo`, and every other line, an empty one included, goes to
`execute`. After each success `_report` prints the state line and the drawing; a
`ValueError` from either call prints as one `error:` line, and because `execute`
parses the whole line before applying anything, a rejected line changes nothing.

## Shapes chosen and rejected

- **Inverse restoration values (chosen)** over **replay**. Here each top-level
  command pushes a `Restore` holding the drawing from before it, so undo is one pop
  and one assignment. A replay version keeps the parsed commands themselves as
  history and undoes by replaying all but the last from the empty drawing, which
  costs time proportional to the whole session on every undo and every execute.
  Both keep a whole `REPEAT` as one entry.
- **Commands with behavior** over tagged tuples and a handler table. Each
  `Command` applies itself, so `REPEAT` composes its block by calling the same
  `apply` on its children. A handler-table version selects behavior through a public
  `HANDLERS` table that a caller can replace at run time; here behavior lives in
  `apply`'s branches, and the parser names the verbs in both designs.
- **Parse everything, then apply.** `execute` calls `parse` on the whole line before
  the first `apply`, so `FORWARD 1 SPIN` moves nothing. Applying while parsing would
  leave the turtle half-moved by a line that is then reported as an error.
- **A drawing every implementation prints the same way.** Printing
  `logo.position` and `logo.segments` as Python tuples would give a format no other
  language prints. The segment lines, `x1,y1 -> x2,y2` oldest first, are the
  program's output data, so they stay fixed across implementations, as Game of
  Life's grids do; the state line above them is this implementation's wording.
- **End of input ends the session; an empty line is an empty program.** A shell
  that calls `input()` without catching `EOFError` ends a piped session in a
  traceback with exit status 1. Here `EOFError` ends the loop, and `parse("")` is
  already a valid empty program, so the shell runs it like any other line and
  prints the state.
- **Python's own words and numbers.** The core tokenizes with `str.upper` and
  `str.split` and reads numbers with `int`, so whitespace is Python's (tabs,
  `\r`, and Unicode spaces too), and `+3`, `007`, and `1_000` are numbers. SPEC
  leaves both to each implementation. Spelling out Python's nine ASCII separators
  and `int`'s underscore grammar, and putting non-ASCII input outside the spec, so
  that C and Rust print the same bytes, would bend the ports toward Python's
  library.
- **Python's limits are Python's.** Coordinates never overflow, but `int()` refuses
  a literal of more than 4,300 digits (a `ValueError`, so the shell reports it), and
  `str()` refuses to print an integer that long. Two `FORWARD`s of 4,300 nines
  therefore move the turtle and then crash `_report` with a traceback, outside the
  `try`. About a thousand nested `REPEAT`s exceed the recursion limit in `_parse`
  (a `RecursionError`, also uncaught). A port has the opposite limits: 64-bit
  coordinates that overflow, and a deeper stack. None of this is in SPEC.

## Scales up to

A Lisp interpreter is this program's pipeline at full size: tokenizer, reader,
data representation, evaluator, and REPL, with *parser / renderer separation
(reader and printer)* and a *dispatch table (special forms, primitives)* among its
moves. A `REPEAT` block is a nested form the reader must match brackets for, as
Lisp's lists are. A Lisp built in several languages may pin integers as signed
64-bit, with overflow an error, so that all of them agree; this SPEC leaves the
range to each implementation, and the C and Rust ports make that same choice. The
undo half reappears in a text editor, whose undo and redo are *the command-history
move* drilled here, in a whole program; Editor Buffer
(`corpus/medium/Editor-Buffer`) is a small one.
