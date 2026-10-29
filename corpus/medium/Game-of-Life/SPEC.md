# Game of Life — SPEC

The world every implementation simulates, in any language. The Python
implementation (`python/problem.md`) adds the API and its approach. Each
implementation is its language's natural program: how it reads the header and
line ends, how it labels a frame, and how it words an error are its own. The
world's rule, the pattern it reads, and the picture of each generation are fixed,
and §5 lists the output facts every implementation keeps.

## 1. The world

A bounded grid of `rows × cols` cells, each live or dead. Cells outside the grid
are permanently dead: no wrapping. One generation applies Conway's rule (B3/S23)
to every cell at once:

- a live cell with 2 or 3 live neighbors (of its 8) stays live;
- a dead cell with exactly 3 live neighbors becomes live;
- every other cell is dead in the next generation.

## 2. Input

The program reads one pattern from stdin and simulates it.

1. **Header:** a line holding three integers, `rows cols generations`, with
   `1 ≤ rows ≤ 100`, `1 ≤ cols ≤ 100`, and `0 ≤ generations ≤ 1000`.
2. **Grid:** exactly `rows` lines follow, each of exactly `cols` characters.
   `#` is a live cell and `.` is a dead one. Row 0 comes first; column 0 is the
   first character.
3. **Nothing else:** no lines may follow the grid, blank or not. The last line's
   newline is optional.

How the header's integers may be spaced or signed, and whether a `\r\n` line end
is accepted, are each implementation's choice.

## 3. Output

For each generation `g` from 0 through `generations`, the program writes a
**frame**: one label line naming `g`, then the grid after `g` generations, `rows`
lines of `cols` characters, `#` and `.`. Generation 0 is the input grid, so
`generations = 0` writes one frame.

## 4. Errors

Input that breaks §2 is answered with one line that says what was wrong, and
nothing else: an empty input, a header without three integers, a value out of
range, a grid line of the wrong length or with a character other than `#` or `.`,
too few lines, or an extra line. The exit status is 0 whenever stdin is well
formed UTF-8 text.

## 5. Fixed output

These are the only output facts every implementation keeps fixed:

- A run on good input writes `(generations + 1) × (rows + 1)` lines: the frames.
- A frame's label line holds numbers, and the first is `g`. Its grid lines are
  exactly the generation's cells, `#` and `.`.
- A run on bad input writes one line, containing the word `error` (any case).

## 6. A session (one implementation)

The Python implementation's shell prints this; other implementations may label
frames and word errors their own way.

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

## Scope

A full-size Life program adds an unbounded plane with 64-bit coordinates, RLE
and plaintext files, rule strings, options, and exit codes. Most of that is about
the shell rather than the step.
