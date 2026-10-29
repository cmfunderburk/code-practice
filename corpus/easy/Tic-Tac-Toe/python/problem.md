# Tic-Tac-Toe — Board Predicates

The Tic-Tac-Toe rules core (no AI, no I/O). A board has 9 cells indexed 0–8
row-major; `"X"` always moves first and turns alternate. A player wins by
filling any row, column, or diagonal; a full board with no winner is a draw.
Illegal moves — occupied cell, out-of-range index, or any move after the game
is decided — raise `ValueError`.

## Examples

```
X plays 0, O plays 4, X plays 1, O plays 5, X plays 2  ->  X wins (top row)
0 1 2 / 3 4 5 / 6 7 8 with X at {0,2,3,5,7} O at {1,4,6,8} -> draw
```

Constraints: positions are ints 0–8.

## Board Predicates

The board is an immutable `tuple[str, ...]` of 9 cells (`"X"`, `"O"`, or
`""`), and the rules are pure functions over it:
`to_move(board) -> str` (derived from the piece counts),
`winner(board) -> str | None`, `is_draw(board) -> bool`,
`legal_moves(board) -> tuple[int, ...]` (empty once the game is decided), and
`play(board, pos) -> tuple[str, ...]` returning a NEW board and raising
`ValueError` on illegal moves. `EMPTY_BOARD` is the starting board.

`_render` draws the board, and the value-threading `main()` is the composition
root, called under the module guard. `main()` starts from `EMPTY_BOARD`. While
the game is undecided, it prints the rendered board and `<mover> to move`, then
reads a line with `input()`; at end of input it prints `game abandoned` and
returns. A line `int()` can't read gets `a cell 0-8, please`; any number goes to
`play`, whose `ValueError` (a marked cell, or one off the board) is printed as
is. Otherwise it retains the new value with `board = play(board, pos)`. When the
game is decided, it renders the final board and prints either the winner or
`draw`. The game itself is `SPEC.md`.
