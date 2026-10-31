## How it works

The board is a tuple of nine strings, one per cell: `"X"`, `"O"`, or `""` for an
empty cell. A tuple can't be changed, so every rule is a function that takes a
board and returns an answer, and nothing else is stored.

- `to_move` counts the marks: when there are as many `X`s as `O`s, it is `X`'s
  turn, and otherwise `O`'s.
- `winner` checks the eight lines in `_LINES` (three rows, three columns, two
  diagonals) and returns the mark that fills one, or `None`.
- `is_draw` is true when nobody has won and no cell is empty.
- `legal_moves` lists the empty cells, or none once somebody has won.
- `play` raises `ValueError("illegal move: <pos>")` unless `pos` is in
  `legal_moves`, and otherwise returns a new tuple with the mover's mark in that
  cell. The board it was given is unchanged.

Worked check: X in cells 0, 2, 3, 5, 7 and O in 1, 4, 6, 8 draws as

```
X O X
X O X
O X O
```

No row, column, or diagonal holds three of one mark, and no cell is empty, so
`winner` returns `None` and `is_draw` returns `True`.

**Complexity.** Time $O(1)$ per call: nine cells and eight lines. Space $O(1)$ for
each new board.

## `main`

`main()` starts from `EMPTY_BOARD` and loops while nobody has won and the game is
not a draw. Each turn it prints `_render(board)` and `X to move` or `O to move`,
then reads a line with `input()`. At end of input it prints `game abandoned` and
returns. It turns the line into a number with `int()`; if that fails, it prints
`a cell 0-8, please` and starts the turn again. It passes any number to `play`. If
`play` raises, `main` prints the message and keeps the old board; otherwise it
keeps the new one with `board = play(board, pos)`. When the game is over, it
prints the final board and `X wins!`, `O wins!`, or `draw`.

`_render` turns a board into three lines of text, with `.` for an empty cell. It
is separate from the rules because drawing the board is not part of the game:
the C and Rust versions draw it their own way.

## Design choices

- **Work out whose turn it is; don't store it.** The board alone decides whose
  turn it is and who has won, so `to_move` and `winner` compute those facts on
  every call. A game object that stored them beside the board would hold a second
  copy of each, and its `play` would have to update all three in the right order:
  mark the cell, then check the lines, then switch the player. Switch first, and
  the wrong mark goes in the cell; check first, and a winning move goes unnoticed
  until the other player has moved again.
- **`main` reads a number; `play` applies the rules.** `main`'s only check is that
  `int()` can read the line. `play` refuses `9`, `-1`, and an occupied cell in the
  same way, because none of them is in `legal_moves`, so the rule about which
  cells may be played is written once. `int()` also accepts ` 4 `, `+4`, and
  digits from other scripts such as Arabic-Indic `٤`. That does no harm: each one
  still names a cell or is refused by `play`.
- **An illegal move raises.** `play` raises `ValueError` instead of returning the
  board unchanged. If it quietly returned the same board, `main` would print the
  same position again with no message, and the player would not know why.
- **Bad lines are answered, not fatal.** A `main` that called `int(input())` and
  didn't catch exceptions would end with a traceback at end of input, on a line
  that isn't a number, and on an occupied cell. This `main` catches `EOFError` and
  prints `game abandoned`, and answers the other two with one line each, after
  which the same player moves again.

## Where this shows up again

A text editor that can be tested without a terminal is built the same way. A test
gives it a file and a script of keystrokes and checks the final screen, so its
core is best written as a step function, (state, key) → state, plus a render
function, state → screen text, with the terminal input and output in its `main`
loop. Here
`play` is the step and `_render` the render. Undo and redo are where returning a
new state helps most: when each step leaves the earlier state unchanged, undo can
go back to it. This program keeps only the current board. An editor has to
decide which earlier states to keep, since a whole copy of a large file after
every keystroke uses a lot of memory. Editors often keep a list of the edits
made, and how to reverse each one, instead.
