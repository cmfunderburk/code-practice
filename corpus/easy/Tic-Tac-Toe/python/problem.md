# Tic-Tac-Toe — Board Predicates

The rules of Tic-Tac-Toe, written as functions over a board, and a `main` that
lets two people play at one terminal (there is no computer player). A board has
9 cells numbered 0 to 8, row by row. `"X"` always moves first, and the turns
alternate. A player wins by filling any row, column, or diagonal; a full board
with no winner is a draw. An illegal move (an occupied cell, a number outside
0 to 8, or any move after the game is won) raises `ValueError`.

## Examples

```
X plays 0, O plays 4, X plays 1, O plays 5, X plays 2  ->  X wins (top row)
0 1 2 / 3 4 5 / 6 7 8 with X at {0,2,3,5,7} O at {1,4,6,8} -> draw
```

Constraints: positions are ints 0–8.

## Board Predicates

The board is a tuple of 9 cells (`"X"`, `"O"`, or `""`), and the rules are
functions that take a board and change nothing: `to_move(board) -> str` (worked
out from the number of marks), `winner(board) -> str | None`,
`is_draw(board) -> bool`, `legal_moves(board) -> tuple[int, ...]` (empty once
someone has won), and `play(board, pos) -> tuple[str, ...]`, which returns a NEW
board and raises `ValueError` on an illegal move. `EMPTY_BOARD` is the starting
board.

`_render` turns a board into text, and `main()` runs the game, called under
`if __name__ == "__main__":`. `main()` starts from `EMPTY_BOARD`. While the game
is not over, it prints the rendered board and `<mover> to move`, then reads a
line with `input()`; at end of input it prints `game abandoned` and returns. A
line `int()` can't read gets `a cell 0-8, please`; any number goes to `play`,
whose `ValueError` (a marked cell, or one off the board) is printed as it is.
Otherwise `main` keeps the new board with `board = play(board, pos)`. When the
game is over, it prints the final board and then the winner (`X wins!` or
`O wins!`) or `draw`. The full behavior is in `SPEC.md`.
