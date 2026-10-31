# Game of Life

Read a pattern from stdin and print it for every generation from 0 through
`generations` under Conway's rule (B3/S23) on a bounded grid: cells outside are
dead, with no wrapping.

- **Input:** a header of three integers, `rows cols generations` (1–100, 1–100,
  0–1000), then exactly `rows` lines of exactly `cols` characters, `#` live and
  `.` dead, and nothing after them.
- **Output:** for each generation, a label line naming it, then the grid as
  `rows` lines of `#` and `.`.
- **Errors:** bad input is answered with one line containing `error`, and
  nothing else.

The world and its pattern are the program's `SPEC.md`. Labels, wording, and how
you read the header are yours.

## A session

Input:
```text
5 5 1
.....
.....
.###.
.....
.....
```
Output:
```text
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
```

## C contract

A whole program, `int main(void)`, with this core above it:

```c
typedef struct {
    int rows, cols;
    bool live[MAX_SIDE][MAX_SIDE];
} World;

static void step(World *world);
static bool read_world(FILE *in, World *world, int *generations);
```

`step` advances the world one generation in place. `read_world` reads one
pattern from `in` and returns `false` for bad input.

Differences from the Python version:
- The world is a dense grid of `bool`, not a set of live cells: C's standard
  library has no set type, and the grid is at most 100 × 100.
- `step` updates the grid in place instead of returning a new one.
