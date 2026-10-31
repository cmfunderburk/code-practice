# Logo Interpreter — SPEC

This document specifies an interpreter for a small drawing language in the style
of Logo. A program in the language steers a *turtle*: a point on a grid that has a
heading and a pen. When the turtle moves with its pen down, it draws a line
segment. The user types one program per line, and can undo the most recent
commands.

There are three versions of the interpreter, in Python, C, and Rust, and each is
written the way a programmer in that language would usually write it. All three
must agree on the language, the history rule, and the drawing they print. They may
differ in what counts as whitespace, which spellings of a number they accept, how
far the turtle may travel, and how they word the state line and an error message.

The Python version's API is in `python/problem.md`. Each version has its own
tests, and all three also run the shared tests in `test_program.py`, which check
only the facts in §4.

## 1. The turtle and its language

The turtle moves on an integer grid. It starts at `(0, 0)`, heading **east**, with
its pen **down**. North increases y, and east increases x.

| Command | Effect |
| --- | --- |
| `FORWARD n` | Move `n` cells in the current heading. With the pen down, draw one segment from the old position to the new one. |
| `LEFT` / `RIGHT` | Turn 90° counterclockwise / clockwise: E → N → W → S → E for `LEFT`. |
| `PENUP` / `PENDOWN` | Lift / lower the pen. Moving with the pen up draws nothing. |
| `REPEAT n [ ... ]` | Run the bracketed commands `n` times. Blocks nest, and a block may be empty. |

**Words.** A line is split into words at whitespace, and `[` and `]` are always
words of their own, with or without spaces around them. Letters are
case-insensitive: `forward`, `Forward`, and `FORWARD` are the same.

**Numbers.** A count or distance is a decimal integer of at least 1. Plain digits
(`2`, `10000`) are numbers in every version. Whether a `+` sign, leading zeros, or
`_` between digits are also accepted depends on the version: each reads numbers
with its language's usual integer parser. `3.0`, `1e3`, `three`, `0`, and `-2` are
never valid counts.

**Programs.** In this grammar, `command*` means zero or more commands, and `|`
separates the choices:

```
program := command*
command := FORWARD number | LEFT | RIGHT | PENUP | PENDOWN
         | REPEAT number '[' program ']'
```

A line that doesn't fit is an error: an unknown command, a missing or invalid
number, a count or distance below 1, a `REPEAT` without `[`, a missing `]`, or an
unexpected `]`. Nothing on such a line runs, not even the commands before the
mistake.

How large a number may be, and how far the turtle may travel, depend on the
version. Python's integers have no size limit. The C and Rust versions keep
coordinates in 64-bit integers, and report a line that would overflow them as an
error.

**History.** Each **top-level** command of a program, meaning one that is not
inside a `REPEAT` block, is one history entry. A whole `REPEAT` is one entry,
however many commands its block runs, and so is a `REPEAT` with an empty block.
`UNDO` restores the turtle, pen, and drawing to what they were before the most
recent entry, and removes that entry.

## 2. Using the program

The program is used at a terminal, one line at a time, on stdin and stdout.
- A line whose only word is `UNDO`, in any case, undoes. `UNDO` is not part of the
  language: `UNDO UNDO` or `FORWARD 1 UNDO` is a program with an unknown command.
- Every other line is a program (§1). An empty line, or a line of only spaces, is
  a program with no commands: it runs and adds no history entry.
- After a line that succeeds, the program prints a **report**: a state line
  showing the turtle's position, heading, and pen, then the **drawing**, one line
  per segment, oldest first:

  ```
  <x1>,<y1> -> <x2>,<y2>
  ```

  The drawing is the program's output, and every version writes the same segment
  lines, so another program (one driving a plotter, say) could read the drawing
  from any version.
- A line that fails, a program error or an `UNDO` with no history left, is answered
  with one line saying what was wrong, and changes nothing: not the turtle, not the
  drawing, not the history.
- The session ends at end of input. There is no banner and no prompt.

The program exits with status 0 whenever its input is well-formed UTF-8 text.

## 3. A sample session (the Python version)

The Python version prints this. The C and Rust versions print the same lines for
this session, but each version may word its state line and its errors its own way.

```
> FORWARD 2 LEFT
x=2 y=0 heading=N pen=down segments=1
0,0 -> 2,0
> penup REPEAT 2 [ FORWARD 1 RIGHT ]
x=3 y=1 heading=S pen=up segments=1
0,0 -> 2,0
> FORWARD 0
error: counts and distances must be positive
> UNDO
x=2 y=0 heading=N pen=up segments=1
0,0 -> 2,0
> undo
x=2 y=0 heading=N pen=down segments=1
0,0 -> 2,0
>
x=2 y=0 heading=N pen=down segments=1
0,0 -> 2,0
> UNDO
x=2 y=0 heading=E pen=down segments=1
0,0 -> 2,0
> UNDO
x=0 y=0 heading=E pen=down segments=0
> UNDO
error: nothing to undo
```

(`> ` marks the user's lines, which a terminal echoes; the program prints no
prompt.) The first `UNDO` removes the whole `REPEAT`, the second removes `PENUP`,
and the empty line prints the report without adding history.

## 4. What the shared tests check

These are the only facts about the output that every version must share:
- Each input line is answered with either one error line or one report.
- An error line contains the word `error` (in any case). No report line does.
- A report is a state line followed by the drawing's segment lines, exactly
  `x1,y1 -> x2,y2`. The state line's first two integers are the turtle's x and y,
  and it is not itself a segment line.

The tests use only ASCII. They separate words with spaces and tabs, and write
numbers as plain digits up to 10000, apart from spellings that no version accepts
as a count, such as `0`, `-2`, or `3.0`.
