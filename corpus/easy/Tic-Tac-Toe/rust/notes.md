Python source: `python/solution.py`

- Move: the board is a value and the rules are functions over it, as in Python.
  `Board` is `[Option<Mark>; 9]`, nine bytes, and `Copy`: every function takes
  it by value, so `play` marks its own copy and returns it in `Ok`, and `main`
  rebinds `board = next` as Python does. Nothing is allocated, where Python's
  `play` slices a new tuple.
- `Mark` is an enum, so a cell can't hold anything but `X`, `O`, or empty;
  Python's cells are strings, with `""` for empty.
- `play` checks that the game is undecided and the cell is empty, so it needs no
  `legal_moves` list. `board.get(pos)` is `None` past the end, so a number off
  the board is illegal too.
- `io::stdin().lines()` yields `io::Result<String>`, without the newline; a line
  that isn't UTF-8 is an `Err`, and the shell stops there, as at end of input. A
  move is `line.trim().parse::<usize>()`, the Rust Book's own idiom: as with
  Python's `int()`, any number reaches `play`, and `9` is `illegal move: 9`. A
  negative number fails to parse, since `usize` has no sign.
- Python contrasts and idioms: annotated in the reference above.
- O(1) per move: nine cells, eight lines.
