# Game of Life — Sparse Set

Conway's Game of Life on a **bounded** grid of `rows × cols` cells. Cells outside
the grid are always dead, and the grid does not wrap around. A cell's neighbors
are the eight cells touching it, diagonals included. In one generation every cell
changes at once: a live cell with 2 or 3 live neighbors stays live, a dead cell
with exactly 3 live neighbors becomes live, and every other cell is dead. `step`
computes one generation and returns a new board, leaving the board it was given
unchanged.

## Examples

A cell is a `(row, column)` pair, and a board is the set of its live cells.

```
Blinker (5x5):          {(2,1),(2,2),(2,3)} -> {(1,2),(2,2),(3,2)}
Block (4x4):            {(1,1),(1,2),(2,1),(2,2)} -> unchanged
Lone corner cell (3x3): {(0,0)} -> set()
```

A **blinker** is a line of three live cells. The middle cell has two live
neighbors and survives, the end cells have one and die, and the two dead cells
beside the middle have three and are born, so the line flips between horizontal
and vertical every generation. A **block** is a 2 × 2 square: each of its cells
has three live neighbors and no dead cell has three, so it never changes. A lone
cell has no live neighbors and dies.

Constraints: `rows, cols >= 1`.

## Sparse Set

The board is the set of live coordinates. In
`step(live: set[tuple[int, int]], rows: int, cols: int)
-> set[tuple[int, int]]`, one `Counter` pass over the neighbors of every live cell
gives each candidate cell its number of live neighbors; the cells the rule makes
live are kept, and only those inside the grid. Only live cells and their neighbors
are ever looked at.

Around `step` sit `parse_input`, `_render`, and `main()`. `main()` reads all of
stdin with `sys.stdin.read()` and passes it to `parse_input`. If that raises
`ValueError`, it prints `error: <message>` and stops. Otherwise it builds the set
of live cells from the grid lines and prints generations 0 through `generations`,
each as `gen <g>` followed by `_render(live, rows, cols)`, rebinding `live` to the
set `step` returns before every generation after 0. The world and its pattern
format are in `SPEC.md`.
