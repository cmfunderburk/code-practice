# Game of Life — oral defense

Seven questions about the design of the Game of Life program, for practising
explaining it aloud. Answer each question with its answer closed, then open the
answer to check yourself. Each answer starts with the main point and names the file
that settles it: `SPEC.md`, `python/solution.py`, or `python/notes.md`.

Question 7 compares the Python version with the C and Rust versions, which are in
`c/` and `rust/`.

> [!note]- Examiner prompt
> Paste this into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached (for question 7, attach the C and Rust
> `solution` files too):
>
> *You are examining a student on a small Game of Life program, specified in
> SPEC.md and implemented in solution.py. Ask the questions from DEFENSE.md one at a
> time, in order. After each answer, ask follow-up questions about anything vague:
> ask for the specific function, input, or line of SPEC. Don't accept "it's
> cleaner" or "it's faster" without the reason. Keep a list of claims that
> contradict SPEC.md or the code, and read it back at the end. Don't show the
> answers unless the student gives up.*

## Following the input through the program

### 1. Trace the sample session from stdin to the last line printed

The input is SPEC §6's: the header `5 5 2`, then a 5 × 5 grid whose middle row is
`.###.`. Those three live cells are a *blinker*: a line of three live cells that
flips between horizontal and vertical every generation.

Name each function the input passes through, in order. For each one, say what it
receives and what it returns. Then say which lines of the program read input or
print output.

> [!answer]-
> **Only `main` reads or prints; `parse_input`, `step`, and `_render` take values
> and return values.**
> 1. `main` reads all of stdin as one string with `sys.stdin.read()`.
> 2. `parse_input` receives that string. It splits it into lines, checks the
>    header and the grid, and returns `(5, 5, 2, grid)`, where `grid` is the list
>    of five strings `[".....", ".....", ".###.", ".....", "....."]`. On bad input
>    it raises `ValueError` instead, and `main` prints `error: <message>` and
>    returns.
> 3. `main` builds the set of live cells from the grid lines, one `(row, column)`
>    pair for each `#`: `{(2, 1), (2, 2), (2, 3)}`.
> 4. For generation 0, `main` prints `gen 0` and then `_render(live, 5, 5)`, which
>    returns the five rows joined by newlines. For generation 1, `main` first calls
>    `step(live, 5, 5)`, which returns the vertical blinker
>    `{(1, 2), (2, 2), (3, 2)}`, and rebinds `live` to it. Generation 2 steps
>    again, back to the horizontal line.
>
> The only input and output are `sys.stdin.read()` and the two `print` calls in
> `main`'s loop (plus the `print` of an error). (`python/solution.py`; SPEC
> §2, §3, §6.)

## Design choices

### 2. A set of live cells or a grid of booleans

`step` stores the world as a set of `(row, column)` pairs, one for each live cell.
Another way to store it is a 2-D list: `rows` lists of `cols` booleans, one entry
for every cell, live or dead. Both work on a bounded grid.

Compare how much work one call to `step` does with each representation on a
100 × 100 grid, first with 5 live cells and then with 5,000. Then look at
`_render`: does the choice change how much work the whole program does per
generation? When would you choose the 2-D list?

> [!answer]-
> **With the set, `step`'s work grows with the number of live cells; with the 2-D
> list, it grows with the number of cells in the grid.**
> - `step`'s `Counter` adds one to a count for each of the eight neighbors of each
>   live cell: 40 additions for 5 live cells, 40,000 for 5,000. It then checks each
>   counted cell against the rule. A cell with no live neighbors is never looked
>   at. The grid's size is used once, in the check
>   `0 <= r < rows and 0 <= c < cols`.
> - A step over a 2-D list visits all 10,000 cells and looks at each one's eight
>   neighbors, about 80,000 lookups, whether 5 cells are live or 5,000. It also has
>   to check, at every cell, whether a neighbor is off the edge.
> - `_render` checks `(r, c) in live` for every one of the `rows × cols` cells, so
>   printing a generation already takes work proportional to the whole grid. On
>   these small grids, the set makes `step` cheap but not the whole program.
>
> Choose the 2-D list when most cells are live, since it then does about the same
> number of lookups without any hashing; or when you need to look up a cell by
> position often; or in a language with no set type, as the C version does
> (question 7). Choose the set when the world has no edges, because a list needs a
> size and a set doesn't (question 6). (`python/solution.py`;
> `python/notes.md` §Design choices.)

### 3. What `parse_input` returns

`parse_input` checks the header and the grid, and returns the grid as a list of
strings such as `[".....", ".###.", "....."]`. `main` then turns those strings into
the set of live cells. A different design would have `parse_input` return the set
itself. The Rust version does that: its `parse_input` returns a `World` struct
that holds `rows`, `cols`, `generations`, and the set.

Suppose you changed `step` to work on a 2-D list of booleans instead of a set.
Which functions would you have to change under each design? What does the Rust
design save?

> [!answer]-
> **Returning strings keeps `parse_input` independent of how the world is
> stored.** In the Python version, switching to a 2-D list changes `step`,
> `_render`, and the one comprehension in `main` that builds the set. `parse_input`
> and its checks stay exactly as they are. If `parse_input` returned the set, it
> would have to change too, and the code that checks the input would be mixed with
> the code that builds the world.
>
> The Rust design saves a step in `main`: `parse_input` adds each row's live cells
> to the set in the same loop that checks the row, so `main` has nothing to
> convert and unpacks one value. For a program that only ever stores the world one
> way, either design works. (`python/solution.py`; `parse_input` in
> `rust/solution.rs`.)

### 4. `step` returns a new set

`step` never changes the set it is given. It builds a new set and returns it, and
`main` rebinds `live` to the result. The other common design updates the world in
place, as the C version's `step` does.

(a) How does returning a new set make `step` easier to test? Name the test in
`python/test_solution.py` that depends on it.

(b) A still life, such as the *block* (a 2 × 2 square of live cells), never
changes. Suppose someone runs a still life for the maximum of 1000 generations.
Once `step` returns a set equal to the one it was given, what could `main` stop
doing, and what must it keep doing to meet SPEC §3? Why is it easy to notice that
moment when `step` returns a new set, and harder when it updates the world in
place?

> [!answer]-
> **After a call, both the old set and the new one exist, so a test or `main` can
> compare them.**
>
> (a) A test can call `step` on a set it builds and compare the result with the
> expected set, with nothing to set up or reset between tests. It can also check
> that the argument was left alone: `test_step_leaves_its_input_unchanged` passes
> the blinker to `step` and then asserts that the set it passed is unchanged.
>
> (b) `step`'s result depends only on its arguments. So if `step(live, rows, cols)
> == live`, every later generation is the same set too. From then on `main` could
> stop calling `step`, and could even render the grid once and reuse the string.
> But SPEC §3 still requires a frame for every generation from 0 through
> `generations`, so `main` must keep printing `gen g` and the grid, 1001 frames in
> all. (The Python version doesn't take this shortcut; the design allows it.)
>
> With a new set, noticing the moment is one comparison, `new == live`. With an
> in-place update, the old state is gone after the call, so `main` would have to
> copy the whole world before every step, or `step` would have to report whether
> any cell changed. (`python/solution.py`; `python/notes.md` §Design
> choices; SPEC §3.)

## Unusual input

### 5. What the Python version does with unusual input

SPEC §2 fixes the header's three numbers and the grid, but leaves each version to
decide how to read a header with extra spaces or a sign, and whether to accept
Windows-style `\r\n` line endings.

Here are five inputs. Each is SPEC §6's pattern, changed in one way:

1. every line ends with `\r\n` instead of `\n`;
2. the header is written `5  5 +2` (two spaces, and a plus sign);
3. the header is written `٥ ٥ ٢` (5, 5, and 2 in Arabic-Indic digits);
4. one blank line follows the grid;
5. the input is completely empty.

For each, does the Python version simulate the pattern or print an error? If it
prints an error, what does the error say? Name the call in `parse_input` that
decides each case.

> [!answer]-
> **Python's own string functions decide: `splitlines` decides what a line is, and
> `split` and `int` decide what a header is.**
> 1. **Simulates.** `str.splitlines` splits at `\r\n` as well as `\n`, so no line
>    keeps a `\r`.
> 2. **Simulates.** `header.split()` with no argument splits at any run of
>    whitespace, giving `["5", "5", "+2"]`, and `int("+2")` is 2.
> 3. **Simulates.** `int` accepts decimal digits from any script, so `int("٥")` is
>    5. SPEC doesn't forbid this; it leaves reading the header to each version.
> 4. **Error:** `error: expected 5 grid lines, got 6`. The blank line is a sixth
>    line after the header, and `len(grid) != rows` catches it.
> 5. **Error:** `error: header needs rows cols generations: ''`.
>    `"".splitlines()` is an empty list, so `or [""]` supplies one empty header.
>    Splitting it gives no fields, unpacking three names from `map(int, [])`
>    raises `ValueError`, and `parse_input` re-raises it with the header in the
>    message.
>
> In every case the program exits with status 0 and, on bad input, prints exactly
> one line, as SPEC §4 requires. (`parse_input` in `python/solution.py`;
> SPEC §2, §4.)

## Beyond this program

### 6. A world with no edges

SPEC §1 bounds the world: every cell outside the `rows × cols` grid is dead.
Suppose instead the world were an unbounded plane, where a live cell can be at any
integer coordinates, including negative ones, and a pattern such as a glider can
travel forever.

Which line of `step` is the only one that uses `rows` and `cols`? What happens if
you delete it? Then go through `parse_input`, `_render`, and `main`, and say which
of them would have to change for an unbounded world, and why.

> [!answer]-
> **Only the check `0 <= r < rows and 0 <= c < cols` ties `step` to the grid.
> Delete it and `step` simulates an unbounded plane, unchanged otherwise.** Cells
> born above row 0 or past the last column would then be kept, and Python's `int`
> coordinates can grow without limit. The rest of the program is built around the
> grid's size:
> - `_render` prints `range(rows)` by `range(cols)`. On an unbounded plane it
>   needs a window to print, such as the smallest rectangle around the live cells,
>   and that rectangle moves as the pattern does, so each frame would also need to
>   say where it is.
> - `parse_input` reads exactly `rows` lines of `cols` characters and limits both
>   to 100. A pattern on an unbounded plane would describe only its live cells and
>   where they sit, and its limits would be about file size, not grid size.
> - `main` passes `rows` and `cols` to `step` and `_render`, and would pass the
>   window instead.
>
> In a C or Rust version, coordinates would also need a signed integer type, and
> the program would have to decide what happens when a pattern reaches that type's
> limit. `step` stays about five statements; nearly all the new work is in reading
> and printing patterns. (`python/solution.py`; `python/notes.md` §Where
> this shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions store the world and read the input

The Python and Rust versions store the live cells in a set (`set` in Python,
`HashSet` in Rust) and count neighbors in a dictionary (`Counter` in Python,
`HashMap` in Rust). The C version stores a 100 × 100 array of `bool`, one entry
for every cell, and its `step` updates that array in place.

Why is each choice reasonable in its language? How does each version keep a
neighbor that lies off the grid from being counted as live? Then find an input
that one version simulates and another refuses.

> [!answer]-
> **Each version uses what its standard library offers, and the grid's 100 × 100
> limit is what makes C's array reasonable.**
> - **Python and Rust** have a hash set and a hash map in their standard libraries,
>   so both keep the set of live cells and count neighbors by adding one to each
>   neighbor of each live cell. Python counts neighbors anywhere and drops off-grid
>   cells in its final check. Rust's coordinates are `usize`, which can't be
>   negative: `checked_add_signed` returns `None` for a neighbor above row 0 or
>   left of column 0, so that neighbor is never counted, and the final filter
>   checks only `r < rows && c < cols`.
> - **C** has no set type in its standard library. The largest grid is
>   100 × 100 = 10,000 `bool`s, about 10 KB, so `World` holds a fixed
>   `bool live[MAX_SIDE][MAX_SIDE]`, and `main` keeps it in `static` storage with
>   no heap allocation. Its `step` still counts by adding one to each live cell's
>   neighbors, into a `counts` array with a one-cell border on every side: a count
>   for an off-grid neighbor lands in the border and is never read. All counting
>   finishes before any cell changes, so updating in place is safe. C's `step`
>   visits every cell each generation, but printing each generation does that in
>   every version anyway.
>
> They read input differently too. Python uses `splitlines`, `split`, and `int`;
> Rust uses `lines`, `split_whitespace`, and `parse::<usize>()`; C reads each line
> with `fgets` and the header with `sscanf("%d %d %d %c")`, where a fourth match
> means something follows the three numbers. Inputs where they differ:
> - **`\r\n` line endings:** Python and Rust simulate. C prints an error, because
>   `fgets` keeps the `\r` in each grid line, and `\r` is not `#` or `.`.
> - **A header of `1 1 -0`:** Python and C read `-0` as 0 and simulate. Rust
>   refuses it, because `parse::<usize>()` does not accept a minus sign.
> - **Lines separated by a lone `\r`:** only Python simulates, since
>   `splitlines` also splits there.
> - **A header number too big to store:** Python reads it and reports it out of
>   range, and Rust's `parse` returns an error. In C, `sscanf("%d")` on a number
>   too big for `int` is undefined behavior; reading it with `strtol` would detect
>   the overflow.
>
> All three give the same frames on the plain inputs the shared tests send, which
> is all SPEC §5 requires. (`notes.md` and `solution.*` in `c/` and `rust/`;
> `python/notes.md`.)
