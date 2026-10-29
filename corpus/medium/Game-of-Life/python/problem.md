# Game of Life — Sparse Set

One generation of Conway's Game of Life on a **bounded** grid: cells outside
the grid are permanently dead (no wrapping). A live cell survives with 2 or 3
live neighbors (of its 8); a dead cell becomes live with exactly 3; everything
else dies/stays dead. Return a NEW board — never mutate the input.

## Examples

```
Blinker (5x5): live {(2,1),(2,2),(2,3)} -> {(1,2),(2,2),(3,2)}
Block: {(1,1),(1,2),(2,1),(2,2)} is a still life
Lone corner cell (0,0) dies
```

Constraints: `rows, cols >= 1`.

## Sparse Set

The board is the SET of live coordinates. In
`step(live: set[tuple[int, int]], rows: int, cols: int)
-> set[tuple[int, int]]`, one `Counter` pass over the neighbors of live cells
gives every candidate's live-neighbor count; then the birth/survival rule
applies and the result is clipped to the grid. Only live cells and their
neighbors are ever touched.

`main()` is the composition root. It reads all of stdin with `sys.stdin.read()`
and hands it to `parse_input`. If that raises `ValueError`, it prints
`error: <message>` and stops. Otherwise it builds the live-cell set from the grid
lines and writes frames 0 through `generations` as `gen <g>` followed by
`_render(live, rows, cols)`, retaining each value `step` returns. The world and
its pattern format are `SPEC.md`.
