## Sparse Set — worked example

**Intuition.** Represent only what exists: the set of live coordinates. One
`Counter` pass over each live cell's 8 neighbors produces every cell that
COULD change (a cell with zero live neighbors can't be born), so work scales
with the population, not the grid. Births are cells counted exactly 3;
survivors are live cells counted 2 (a live cell counted 3 is already a
birth). The representation IS the insight, and it generalizes to unbounded
Life where a dense grid can't follow.

Worked check (blinker): the Counter over neighbors of {(2,1),(2,2),(2,3)}
gives (1,2) and (3,2) count 3 (born), (2,2) count 2 and live (survives),
(2,1)/(2,3) count 1 (die).

**Complexity.**
- Time: $O(|live|)$ per step. Space: $O(|live|)$.

**Discussed, not drilled.** The bounds clip is the only place the grid size
appears — delete it and this same function runs unbounded Life.

**The drilled composition root.** `main()` turns the validated grid lines into
a live-cell set, passes the bounded dimensions to both rendering and stepping,
and threads each returned set. Bad input becomes one `error:` line on stdout.
The representation shapes initialization, integration, and rendering, not only
the rule function.

## Shapes chosen and rejected

- **Sparse set (chosen)** over a **dense grid**. On a bounded board both work.
  The dense grid allocates `rows × cols` per step and clips the neighbor ranges
  at every cell. The set touches only live cells and their neighbors, and the
  bounds appear once, as a clip. That is preference here and necessity on an
  unbounded plane.
- **Vectorized**: `numpy` neighbor sums over shifted slices of a zero-padded
  board, so the padding is the dead border. It is the fastest per cell on a
  crowded board, and it is a crossover variant: it borrows the dense
  representation and hands the loop to the library.
- **Shared parser, drilled shell.** `parse_input` validates SPEC §2 and
  returns plain grid lines, so the representation is chosen in the drilled
  `main()`, not in the parser. It reads the way Python reads: `splitlines()`,
  then `map(int, header.split())`, so extra spaces, a `+5`, or a `\r\n` line end
  are accepted, as SPEC leaves them to each implementation. Splitting on `"\n"`
  only, checking every header field for ASCII digits, and decoding stdin's bytes
  in `main()` would match C byte for byte, but SPEC doesn't ask for that.
- **Python's limits are Python's.** `int()` refuses a field of more than 4,300
  digits (a `ValueError`, so a zero-padded header that long is reported as bad
  input). C's `sscanf("%d")` has the opposite problem: a header number too big
  for `int` is undefined behavior. Neither is in SPEC.

## Scales up to

A full-size Life program is this program grown up: the same sparse set and
scatter-count step on an **unbounded** plane with 64-bit coordinates. Delete the
bounds clip here and `step` is that program's step. Nearly all the rest of it is
the shell this toy's SPEC leaves out: RLE and plaintext readers and writers,
`B/S` rule strings, options validated after collection, exit codes, and a
fixed-point early exit that a pure step makes legal. Rule strings bring one
subtlety. Under S0 an isolated live cell survives, but it is never counted, so a
step that decides survival by iterating the count table loses it. This program's
B3/S23 rule never meets that case.
