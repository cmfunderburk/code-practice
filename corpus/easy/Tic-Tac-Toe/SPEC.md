# Tic-Tac-Toe — SPEC

The game every implementation plays, in any language. The Python implementation
(`python/problem.md`) adds the API and its approach. Each implementation is its
language's natural program for this game: how it draws the board, words its
output, and reads a move is its own. Only the output facts in §4 are fixed.

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
- A move is a cell number, 0 to 8. The cell numbers are the game's own, so a line
  of moves plays the same game in every implementation.
- Before each move the players can see the board and whose turn it is.
- A line that is not a cell number, a number off the board, and a cell already
  marked are each answered. None costs the player the turn.
- When the game ends, the program shows the final board, names the winner or the
  draw, and stops reading.
- If input ends first, the program stops.

How an implementation treats spaces or a sign around the number is its own choice. The
exit status is 0 whenever input is well formed UTF-8 text.

## 3. A session (one implementation)

The Python implementation's shell prints this; other implementations may draw the
board and word their answers their own way.

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

## 4. Fixed output

These are the only output facts every implementation keeps fixed:
- When the game ends, the last line names the outcome: it contains `X wins`,
  `O wins`, or the word `draw` (any case). No earlier line contains `wins` or
  `draw`.
- Every line is answered: a line that is not a legal move produces at least one
  line of output.
