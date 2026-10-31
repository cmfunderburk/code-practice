# Tic-Tac-Toe — SPEC

This document specifies a program that lets two people play Tic-Tac-Toe at one
terminal. There are three versions of it, in Python, C, and Rust, and each is
written the way a programmer in that language would usually write it. All three
play the same game (§1) and number the cells the same way, so the same sequence
of moves plays the same game in every version. They may differ in how they draw
the board, how they word their messages, and how they read a line.

The Python version's API is in `python/problem.md`. Each version has its own
tests, and all three also run the shared tests in `test_program.py`, which check
only the facts in §4.

## 1. The game

Two players share one input stream and take turns marking cells of a 3×3 board.
- The cells are numbered 0 to 8, row by row: 0 1 2 on top, 6 7 8 at the bottom.
- `X` moves first, and the turns alternate.
- A player who fills a row, a column, or a diagonal with their mark **wins**.
- A full board with no winner is a **draw**.
- Marking a cell that is already marked, or naming no cell, is rejected and costs
  nothing: the same player moves again.

## 2. Playing

Two people play at one terminal, one move per line, on stdin and stdout.
- A move is a cell number, 0 to 8, numbered as in §1. Every version uses these
  numbers, so a list of moves plays the same game in every version.
- Before each move the players can see the board and whose turn it is.
- A line that is not a cell number, a number off the board, and a cell already
  marked are each answered. None costs the player the turn.
- When the game ends, the program shows the final board, names the winner or the
  draw, and stops reading.
- If input ends first, the program stops.

Each version decides for itself how to read a line with spaces or a sign around
the number, such as ` 4 ` or `+4`, and whether a number off the board gets the
same answer as a line that is not a number. The program exits with status 0
whenever its input is well-formed UTF-8 text.

## 3. A sample session (the Python version)

The Python version prints this. For these four lines the C and Rust versions
print exactly the same, but they answer some other lines differently. For
example, the Python and Rust versions answer `9` with `illegal move: 9`, while
the C version answers it with `a cell 0-8, please`.

```
. . .
. . .
. . .
X to move
> 4
. . .
. X .
. . .
O to move
> 4
illegal move: 4
. . .
. X .
. . .
O to move
> x
a cell 0-8, please
. . .
. X .
. . .
O to move
> 0
O . .
. X .
. . .
X to move
```

(`> ` marks the players' lines, which a terminal echoes; the program prints no
prompt.)

## 4. What the shared tests check

These are the only facts about the output that every version must share:
- When the game ends, the last line names the outcome: it contains `X wins`,
  `O wins`, or the word `draw` (any case). No earlier line contains `wins` or
  `draw`.
- Every line is answered: a line that is not a legal move produces at least one
  line of output.

