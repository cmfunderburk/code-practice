# Game of Life — SPEC

This document specifies a program that simulates Conway's Game of Life on a
bounded grid. There are three versions of it, in Python, C, and Rust, and each is
written the way a programmer in that language would usually write it. All three
must agree on the rule (§1), the patterns they accept (§2), and the grids they
print (§3). They may differ in how they read the header line and line endings, in
how they label each generation, and in how they word an error message.

The Python version's API is in `python/problem.md`. Each version has its own tests,
and all three also run the shared tests in `test_program.py`, which check only
the facts in §5.

## 1. The world

The world is a grid of `rows × cols` cells, each live or dead. A cell's
**neighbors** are the eight cells touching it, diagonals included. Cells outside
the grid are always dead: the grid does not wrap around from one edge to the
opposite edge.

One generation applies Conway's rule, often written B3/S23 (a cell is born with 3
live neighbors and survives with 2 or 3), to every cell at once:

- a live cell with 2 or 3 live neighbors stays live;
- a dead cell with exactly 3 live neighbors becomes live;
- every other cell is dead in the next generation.

"At once" means that every cell's next state is computed from the current
generation; no cell sees a neighbor's new state.

Three small patterns appear in the examples and the tests:

- A **blinker** is a line of three live cells. The middle cell has two live
  neighbors and survives, the two end cells have one and die, and the two dead
  cells beside the middle have three and are born. So the line flips between
  horizontal and vertical every generation.
- A **block** is a 2 × 2 square of live cells. Each of its cells has three live
  neighbors, and no dead cell has three, so it never changes. A pattern that never
  changes is called a **still life**.
- A **glider** is a five-cell pattern that returns to its own shape every four
  generations, moved one cell diagonally. On a bounded grid it can't leave: a
  glider that starts in the top-left corner of an 8 × 8 grid, moving down and to
  the right, turns into a block in the bottom-right corner.

## 2. Input

The program reads one pattern from stdin and simulates it.

1. **Header:** a line holding three integers, `rows cols generations`, with
   `1 ≤ rows ≤ 100`, `1 ≤ cols ≤ 100`, and `0 ≤ generations ≤ 1000`.
2. **Grid:** exactly `rows` lines follow, each of exactly `cols` characters.
   `#` is a live cell and `.` is a dead one. Row 0 comes first; column 0 is the
   first character.
3. **Nothing else:** no lines may follow the grid, blank or not. The last line's
   newline is optional.

Each version decides for itself how to read a header with extra spaces or a sign
(such as `5  5 +2`), and whether to accept `\r\n` line endings.

## 3. Output

For each generation `g` from 0 through `generations`, the program writes a
**frame**: one label line naming `g`, then the grid after `g` generations, `rows`
lines of `cols` characters, `#` and `.`. Generation 0 is the input grid, so
`generations = 0` writes one frame.

## 4. Errors

Input that breaks §2 is answered with one line that says what was wrong, and
nothing else. That covers an empty input, a header without exactly three
integers, a value out of range, a grid line of the wrong length or with a
character other than `#` or `.`, too few grid lines, and an extra line. The
program exits with status 0 whenever stdin is well-formed UTF-8 text.

## 5. What the shared tests check

These are the only facts about the output that every version must share.

- A run on good input writes `(generations + 1) × (rows + 1)` lines: the frames.
- In each frame, the label line contains numbers, and the first is `g`. The grid
  lines are exactly that generation's cells, `#` and `.`.
- A run on bad input writes one line, containing the word `error` (in any case).

## 6. A sample session (the Python version)

The input is a blinker lying horizontally in the middle of a 5 × 5 grid, run for
two generations. All three versions print these frames with the same `gen g`
labels. Their error messages differ: for a 3 × 3 grid whose middle line is `.x.`,
the Python version prints `error: row 1 must be 3 of '#' or '.': '.x.'`, and the
C version prints `error: expected a rows cols generations header and a grid of #
and .`.

Input:

```
5 5 2
.....
.....
.###.
.....
.....
```

Output:

```
gen 0
.....
.....
.###.
.....
.....
gen 1
.....
..#..
..#..
..#..
.....
gen 2
.....
.....
.###.
.....
.....
```
