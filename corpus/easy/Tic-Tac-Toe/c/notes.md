Python source: `python/solution.py`

- Move: the board is a value, as in Python. `Board` wraps the nine cells in a
  struct so it can be passed and returned by value; the predicates take a
  9-byte copy, and `play` writes the next board through a pointer, so `main`
  threads a value through the loop as Python's `board = play(board, pos)` does.
- Whose turn it is and who has won are derived from the cells on every call,
  never stored, as in Python.
- An empty cell is `'\0'`, so `Board board = {}` is the empty board, and
  `winner` returns `'\0'` for nobody.
- Python's `legal_moves` has no caller here, so `play` checks the same rule
  directly: on the board, game undecided, cell empty.
- Lines are read with `fgets` into a 64-byte buffer, and `strcspn` cuts the
  `\r\n`. `cell_of` parses with `strtol`, C's checked number reader: `end`
  shows whether anything followed the digits. Where Python hands any integer to
  `play`, `cell_of` also rejects a number outside 0-8, so it never narrows a
  huge `long` to an `int`; `9` gets `a cell 0-8, please` here, `illegal move: 9`
  in Python.
- No heap.
- Python contrasts and idioms: annotated in the reference above.
- O(1) per move: nine cells, eight lines.
