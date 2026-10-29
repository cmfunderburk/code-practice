## Board Predicates — worked example

**Intuition.** The board is a VALUE — an immutable tuple — and every rule is
a pure predicate over it. Nothing needs an object: whose turn it is falls out
of the piece counts, and `play` returns a new board, so histories, undo, and
sharing positions are free. This is the cleanest implementation of a rules
core: no state to corrupt, every function checkable in isolation.

Worked check: X at {0,2,3,5,7}, O at {1,4,6,8} — no row, column, or diagonal
is single-marked, no cell empty → `winner` None, `is_draw` True.

**Complexity.**
- Time: $O(1)$ per call (fixed 9 cells, 8 lines).
- Space: $O(1)$ per new board.

**Discussed, not drilled.** Deriving the mover from counts means the board
alone is the whole state — a game object instead *stores* the mover, a
representative example of state you must now keep consistent.

**The drilled composition root.** The board is a value, so `main()` threads it:
render, read a line, `board = play(board, pos)`. `_render` lives in the shell, since
presentation is not a rule. The shell turns the line into a number with `int()`,
because the core is handed cell indices, not lines; the core checks the *rules*
(a cell off the board, an occupied cell) and raises, and the shell prints the error
and keeps the old board by not rebinding.

## Shapes chosen and rejected

- **An immutable board with a derived mover (chosen)** over a **game object**.
  The object stores the board, the mover, and a cached winner, and `play` must
  update all three in the right order: mark the cell, then check the lines, then
  toggle the mover. Here the tuple is the whole state.
  `to_move` counts marks and `winner` scans the lines on every call, so nothing can
  disagree with the board.
- **A number in the shell, rules in the core.** The shell's only check is that
  `int()` can read the line; `play` rejects `9`, `-1`, and an occupied cell alike,
  through `legal_moves`. A shell that accepts exactly one ASCII digit 0–8 would
  make three languages print the same bytes, but SPEC doesn't pin which lines are
  invalid. `int()` also takes ` 4`, `+4`, and non-ASCII digits such as `٤`; those
  are this implementation's choice, and harmless, since each still names a cell or
  is refused by the core.
- **A rule check, not a hint.** `play` raises on an illegal move instead of
  returning the board unchanged. A silent no-op would make the shell print the same
  board again with no message, and a caller that forgot to compare boards would
  never know.
- **Bad lines are reported, not fatal.** A shell that calls `int(input(...))` and
  never catches `play`'s `ValueError` ends with a traceback on end of input, a line
  that isn't an integer, or an occupied cell. This shell catches `EOFError` and
  prints `game abandoned`, and the other two get one line each and another turn.

## Scales up to

A text editor that runs headless from a key script has its core forced into the
shape this program drills: a pure step, (state, key) → state, plus a pure render,
state → frame string, with the terminal I/O in the shell. Here `play` is the step
and `_render` the render. An editor's undo and redo stack is where a value core
pays off. When each step returns a new state, earlier states are still intact. This
program never keeps more than the current board, though; an editor has to decide
what to keep.
