# Logo Interpreter — SPEC

The interpreter every implementation builds, in any language. The Python version
(`python/problem.md`) adds the API and its design. Each implementation is its
language's natural program for this interpreter: what counts as whitespace,
which spellings of a number it reads, how far its turtle may travel, how it words
the state line and an error are its own. The language, the history rule, and the
drawing it prints are fixed, and all of them keep the fixed output of §4.

## 1. The turtle and its language

A turtle moves on an integer grid. It starts at `(0, 0)`, heading **east**, with its
pen **down**. North increases y, and east increases x.

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
(`2`, `10000`) are numbers in every implementation; whether a `+` sign, leading
zeros, or `_` digit separators are also accepted is the implementation's, as its
language's integer parser decides. `3.0`, `1e3`, `three`, `0`, and `-2` are never valid counts.

**Programs.**

```
program := command*
command := FORWARD number | LEFT | RIGHT | PENUP | PENDOWN
         | REPEAT number '[' program ']'
```

A line that doesn't fit is an error: an unknown command, a missing or invalid
number, a count or distance below 1, a `REPEAT` without `[`, a missing `]`, or an
unexpected `]`. Nothing on such a line runs, not even the commands before the
mistake.

How large a number may be, and how far the turtle may travel, are the
implementation's: Python's integers are unbounded, and a port may use 64-bit
coordinates and report a line that would overflow them as an error.

**History.** Each **top-level** command of a program is one history entry. A whole
`REPEAT` is one entry, however many commands its block runs, including a `REPEAT`
with an empty block. `UNDO` restores the turtle, pen, and drawing to what they were
before the most recent entry and removes that entry.

## 2. Playing

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

  The drawing is the program's output data, as a frame's grid is Game of Life's:
  every implementation writes the same segment lines, so a plotter could read any of them.
- A line that fails, a program error or an `UNDO` with no history left, is answered
  with one line saying what was wrong, and changes nothing: not the turtle, not the
  drawing, not the history.
- The session ends at end of input. There is no banner and no prompt.

The exit status is 0 whenever input is well formed UTF-8 text.

## 3. A session (one implementation)

The Python version's shell prints this; other implementations may word the state
line and the errors their own way.

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

## 4. Fixed output

These are the only output facts every implementation keeps fixed:
- Each input line is answered with either one error line or one report.
- An error line contains the word `error` (any case). No report line does.
- A report is a state line followed by the drawing's segment lines, exactly
  `x1,y1 -> x2,y2`. The state line's first two integers are the turtle's x and y,
  and it is not itself a segment line.

They hold for input written with single spaces between words, numbers as plain
digits up to 10000, and only ASCII.
