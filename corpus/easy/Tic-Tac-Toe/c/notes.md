Python source: `python/solution.py`

- The board is passed by value, as in Python. C can pass and return a struct by
  value but not a bare array, so `Board` is a struct holding the nine cells.
  Each function that takes a board gets its own 9-byte copy, and `play` writes
  the next board through a pointer, so `main` keeps the new board as Python's
  `board = play(board, pos)` does.
- `to_move` and `winner` work out whose turn it is and who has won from the
  cells on every call. Nothing else is stored, as in Python.
- An empty cell is `'\0'`, so `Board board = {}` is the empty board, and
  `winner` returns `'\0'` when nobody has won.
- Nothing else in this program needs a list of the legal moves, so there is no
  `legal_moves`: `play` checks the same conditions directly (the cell is on the
  board, nobody has won, and the cell is empty).
- `main` reads each line with `fgets` into a 64-byte buffer, and `strcspn` cuts
  off the `\n` or `\r\n`. `cell_of` reads the number with `strtol`, whose end
  pointer shows whether anything followed the digits. `strtol` skips spaces
  before the number and accepts a sign, so ` 4` and `+4` are cell 4, but `4 `
  (with a trailing space) is refused. Where Python passes any integer to `play`,
  `cell_of` also refuses a number outside 0 to 8, so a huge `long` is never
  converted to an `int`. So `9` gets `a cell 0-8, please` here, and
  `illegal move: 9` in Python. A line too long for the buffer arrives in pieces,
  and each piece is answered as not a cell.
- No heap.
- Python contrasts and idioms: annotated in the reference above.
- O(1) per move: nine cells, eight lines.
