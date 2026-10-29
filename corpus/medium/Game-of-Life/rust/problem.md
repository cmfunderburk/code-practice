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

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
type Cell = (usize, usize);

struct World {
    rows: usize,
    cols: usize,
    generations: usize,
    live: HashSet<Cell>,
}

fn step(live: &HashSet<Cell>, rows: usize, cols: usize) -> HashSet<Cell>
fn parse_input(text: &str) -> Result<World, String>
```

Differences from the Python implementation:
- Coordinates are `usize`, so a neighbor off the top or left edge can't be
  formed at all.
- `parse_input` returns the live set inside a `World`, where Python's returns
  grid lines.
