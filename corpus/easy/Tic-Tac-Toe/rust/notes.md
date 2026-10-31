Python source: `python/solution.py`

- The board is passed by value and the rules are functions over it, as in
  Python. `Board` is `[Option<Mark>; 9]`, nine bytes, and `Copy`: every function
  takes it by value, so `play` marks its own copy and returns it in `Ok`, and
  `main` keeps it with `board = next`, as Python's `board = play(board, pos)`
  does. Nothing is allocated, where Python's `play` slices a new tuple.
- `Mark` is an enum, so a cell can hold nothing but `X`, `O`, or `None` for
  empty; Python's cells are strings, with `""` for empty.
- `play` checks that nobody has won and the cell is empty, so it needs no
  `legal_moves` list. `board.get(pos)` is `None` past the end, so a number off
  the board is illegal too.
- `io::stdin().lines()` yields `io::Result<String>`, without the newline. A line
  that isn't UTF-8 is an `Err`, and `main` stops there, as at end of input. A
  move is `line.trim().parse::<usize>()`, the Rust Book's own idiom: spaces
  around the number are ignored, and as with Python's `int()`, any number
  reaches `play`, so `9` is `illegal move: 9`. A negative number fails to parse,
  since `usize` has no sign, and gets `a cell 0-8, please`.
- Python contrasts and idioms: annotated in the reference above.
- O(1) per move: nine cells, eight lines.
