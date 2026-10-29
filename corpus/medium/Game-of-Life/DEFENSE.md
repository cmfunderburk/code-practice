# Game of Life — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or the
code. The last compares the C and Rust ports; attach their `solution` files to the
committee prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small Game of Life program, specified in
> SPEC.md and implemented in solution.py. Ask the questions from DEFENSE.md one at a
> time, in order. After each answer, press on anything vague: demand the specific
> structure, cost, failure mode, or line of SPEC. Don't accept "it's cleaner" or "it's
> faster" without the mechanism. Keep a list of claims that contradict SPEC.md or the
> code, and read it back at the end. Don't reveal the answer callouts unless the
> candidate concedes.*

## Lifecycle

### 1. Trace `5 5 2` plus a blinker from stdin to the last byte

Name each function the input passes through, what crosses each boundary, and where
the side effects are.

> [!answer]-
> 1. `main` reads all of stdin with `sys.stdin.read()`.
> 2. `parse_input`, which is pure, splits lines, validates the header and grid, and
>    returns `(rows, cols, generations, grid lines)`. It raises `ValueError` on bad
>    input, and `main` turns that into one `error:` line.
> 3. `main` builds the live-cell **set** from the grid lines.
> 4. For each generation, `main` steps from the second frame on, then prints
>    `gen g` and `_render(live, rows, cols)`. Both `step` and `_render` are pure.
>
> The only side effects are reading stdin and printing, both in `main`.
> (`python/solution.py`; SPEC §2–§4.)

## Trade-offs

### 2. Both a set and a 2-D list work on a bounded board. Why the set, and when would you reverse that?

> [!answer]-
> A step costs time proportional to the **population**, not the area: only live cells
> and their neighbors are counted. The grid size appears once, in the bounds clip.
> A dense grid allocates `rows × cols` per step and clips neighbor ranges at every
> cell. Reverse the choice for a crowded, bounded world, where a dense
> or vectorized array wins per cell. On an unbounded plane there's no choice: only
> the set can represent it. (`python/notes.md` §Shapes chosen and rejected.)

### 3. Why does `parse_input` return grid lines instead of the live-cell set?

> [!answer]-
> So the parser doesn't choose the representation. Validation is the same for every
> representation, so it's shared. Turning lines into a set (or a dense list, or an
> array) is the representation decision, and it belongs in the composition root
> beside the step that consumes it. A dense-grid or vectorized version could reuse
> this parser unchanged. (`python/notes.md` §Shapes chosen and rejected.)

### 4. `step` returns a new set and never mutates its input. What does that buy here, and what does it buy a full-size Life program?

> [!answer]-
> - **Here:** `main` can rebind `live` each generation without aliasing bugs, and
>   `step` can be called on a value and its result compared, with no setup or
>   teardown.
> - **In a full-size Life program:** purity makes the **fixed-point early exit**
>   legal. If generation g+1 equals g, every later one does too, so a statistics run
>   can stop early on a still life given a huge generation count. A mutating
>   `World.tick()` would hide that. (`python/notes.md` §Scales up to.)

## Adversarial

### 5. Input arrives with `\r\n` line endings, or a header like `5  5 +2`. What happens, and who decides?

> [!answer]-
> Each implementation decides; SPEC fixes the pattern, not how a language reads it.
> - **Python** accepts both. `str.splitlines` splits at `\r\n` (and `\r`, `\v`,
>   `\f`, and more), and `int` reads ` +2` after `str.split()` has dropped the
>   extra spaces.
> - **Rust** accepts both too: `str::lines` strips a `\r\n`, `split_whitespace`
>   ignores runs of spaces, and `usize::from_str` takes a leading `+`.
> - **C** reads the header with `sscanf("%d %d %d")`, which skips any whitespace
>   and takes a sign, but a grid line from `fgets` keeps its `\r`, which is then a
>   bad character.
>
> SPEC could say exactly one space and `\n` only, so Python would split on `"\n"`
> and read bytes, but that rule would serve only a transcript shared by three
> languages, not the program. (SPEC §2; `python/notes.md` §Shapes chosen and
> rejected.)

## Scale

### 6. What one line ties `step` to a bounded grid, and what would a full-size Life program's spec force you to add?

> [!answer]-
> The clip `0 <= r < rows and 0 <= c < cols`. Delete it and `step` runs on an
> unbounded plane. A full-size Life program would then need:
> - 64-bit coordinates, and an error when a pattern would leave their range;
> - RLE and plaintext readers and a canonical RLE writer;
> - `B/S` rule strings, with B0 rejected because it would make infinitely many births;
> - options collected first and validated afterward, in a fixed order;
> - exit codes, and the fixed-point exit.
>
> The step stays about five statements, and nearly everything else is shell.
> (`python/notes.md` §Scales up to.)

## Across languages

### 7. The C port stores a dense grid, while Python and Rust keep a set. Why did each language choose as it did?

> [!answer]-
> **The library decides, and the bounded board lets it.**
> - **Python and Rust** have a hash set and a hash map in the standard library, so
>   they keep the live-cell set and the `Counter` scatter. Rust's coordinates are
>   `usize`, so a neighbor above row 0 or left of column 0 can't be made at all:
>   `checked_add_signed` returns `None` for it.
> - **C** has no set type. A 100×100 board is only 10,000 `bool`s, so the port
>   stores a dense grid. It keeps the scatter, into a count array with a one-cell
>   border that replaces the clip.
>
> Their parsers differ the same way: Python uses `splitlines` and `int`, Rust
> `lines`, `split_whitespace`, and `parse`, and C reads the header with `fgets`
> and `sscanf` and each row with `fgets`. `sscanf("%d")` on a number too big for
> `int` is undefined behavior, which a careful C reader replaces with `strtol`;
> Python's mirror-image limit is `int()` refusing more than 4,300 digits.
>
> The dense step costs time proportional to the area, not the population. That
> doesn't change the program's cost, because printing each frame is already
> proportional to the area. On an unbounded board the dense grid stops working,
> and a C port would need a hash set first. (`python/notes.md`; `c/notes.md`.)
