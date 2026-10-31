## How it works

`step` stores the world as the set of live cells, each a `(row, column)` pair. It
counts neighbors by working outward from the live cells: for each live cell, it
adds one to the count of each of its eight neighbors, in a `Counter`. A cell that
could be live in the next generation has at least two live neighbors, so it is
always in the counts; a cell with no live neighbors is never looked at.

A counted cell is live in the next generation if its count is 3 (it is born, or it
survives), or if its count is 2 and it is live now (it survives). A live cell with
3 neighbors is covered by the first case. Finally `step` keeps only the cells
inside the grid, with `0 <= r < rows and 0 <= c < cols`. That check is the only
place `step` uses the grid's size.

Worked check, the blinker `{(2,1),(2,2),(2,3)}`: the counts give `(1,2)` and
`(3,2)` a 3, so they are born; `(2,2)` a 2, and it is live, so it survives; `(2,1)`
and `(2,3)` a 1, so they die. The result is `{(1,2),(2,2),(3,2)}`.

**Complexity.** `step` takes time and space $O(|live|)$, proportional to the
number of live cells. Printing a generation with `_render` takes
$O(rows \cdot cols)$, since it checks every cell of the grid.

## `main`

`main()` reads all of stdin with `sys.stdin.read()` and passes it to
`parse_input`. If that raises `ValueError`, `main` prints `error: <message>` and
stops. Otherwise it builds the set of live cells, one pair for each `#` in the
grid lines. Then, for each generation from 0 through `generations`, it calls
`step` (except for generation 0, which is the input itself), rebinds `live` to the
set `step` returns, and prints `gen <g>` and `_render(live, rows, cols)`. All the
reading and printing happens in `main`; `parse_input`, `step`, and `_render` only
take values and return them.

## Design choices

- **A set of live cells, not a grid of booleans.** On a bounded grid both work.
  A step over a 2-D list of booleans visits every cell and checks, at every cell,
  whether each neighbor is off the edge. The set looks only at live cells and
  their neighbors, and checks the edge once, at the end. When most cells are live,
  the 2-D list is faster, since it does about the same number of lookups without
  hashing. On a world with no edges only the set works, because a list needs a
  size. A third option is a NumPy array: the neighbor counts are the sum of eight
  shifted copies of the grid, padded with a border of dead cells. It is the
  fastest per cell when the grid is crowded, and it stores the world the way the
  2-D list does.
- **`parse_input` returns grid lines, not the set.** It checks the input against
  SPEC §2 and returns plain strings, so it doesn't depend on how the world is
  stored. `main` builds the set with one comprehension. Storing the world another
  way would change `step`, `_render`, and that comprehension, but not
  `parse_input`.
- **`step` returns a new set.** It never changes its argument, so a test can call
  it and compare the result with no setup, and `main` simply rebinds `live` each
  generation. After a call the caller holds both the old set and the new one, so
  it can notice when they are equal. From then on every generation is the same,
  and a program could stop calling `step`, though it would still print every frame
  SPEC §3 requires.
- **Reading input the usual Python way.** `parse_input` splits the text with
  `str.splitlines()` and reads the header with `map(int, header.split())`. So
  extra spaces, a `+5`, and `\r\n` line endings are all accepted; SPEC leaves those
  choices to each version. `int` also accepts digits from other scripts, such as
  Arabic-Indic `٥`, and refuses a string of more than 4,300 digits with a
  `ValueError`, so a header padded with that many zeros is reported as bad input.
  An empty input splits into no lines at all, so `or [""]` supplies an empty
  header, which then fails the three-number check with a clear message.

## Where this shows up again

Any simulation with a state and a step function has the same shape: a function
from one state to the next, and a loop around it that reads input and prints each
state. Keeping the step free of input and output is what lets the tests call it
directly.

A full-size Game of Life program works on an unbounded plane, and it can keep
this program's representation: delete the edge check and `step` works on any
integer coordinates. Most of such a program reads and writes patterns and handles
options: pattern file formats such as RLE and plaintext, rule strings such as
`B36/S23` (HighLife) that change the birth and survival counts, command-line
options, exit codes, and an early stop once a generation equals the one before
it. A C version of it needs a set of cells written by hand, such as a hash set,
since C's standard library has none.

Rule strings bring one subtlety. Under a rule where a live cell with no live
neighbors survives (written S0), an isolated live cell never appears in the
counts, because no live cell is next to it. This program's `step` decides which
cells are live by walking the counts, so under S0 it would lose such a cell; a
step for such rules decides survival by walking the live cells instead. This
program's B3/S23 rule never meets that case.
