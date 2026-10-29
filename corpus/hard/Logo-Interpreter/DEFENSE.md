# Logo Interpreter — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or the code.
The last compares the C and Rust ports; attach their `solution` files to the committee
prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small Logo interpreter, specified in SPEC.md and
> implemented in solution.py. Ask the questions from DEFENSE.md one at a time, in
> order. After each answer, press on anything vague: demand the specific structure,
> failure mode, or line of SPEC. Don't accept "undo is just a stack" without naming
> what each entry holds and what it costs. Keep a list of claims that contradict
> SPEC.md or the code, and read it back at the end. Don't reveal the answer callouts
> unless the candidate concedes.*

## Lifecycle

### 1. Trace `FORWARD 2 LEFT`, then `penup REPEAT 2 [ FORWARD 1 RIGHT ]`, then `UNDO`

Name each function a line passes through, which ones are pure, and what `Logo` holds
after each line.

> [!answer]-
> 1. `input()` reads one line without its `\n`.
>    `_is_undo` checks whether the line's only token is `UNDO`; for the first two
>    lines it isn't, so `main` calls `logo.execute(line)`.
> 2. `execute` calls `parse`, which pads `[` and `]` with spaces, uppercases, splits,
>    and hands the tokens to `_parse`. `_parse` builds `Command("forward", 2)` and
>    `Command("left")`; for the second line it builds `Command("penup")` and one
>    `Command("repeat", (2, (forward 1, right)))`, recursing once for the block.
> 3. For each **top-level** command, `execute` keeps `before`, sets
>    `self._drawing = command.apply(before)`, and pushes `command.inverse(before)`,
>    a `Restore` holding `before`. After line 1 the stack has 2 entries; after line 2
>    it has 4. The `REPEAT`'s `apply` runs its two children twice each, but pushes
>    nothing itself.
> 4. `UNDO` makes `main` call `logo.undo()`, which pops the `REPEAT`'s `Restore` and
>    applies it: the drawing is exactly the one from before the `REPEAT`, at `(2, 0)`
>    heading N with the pen up.
> 5. After each success `_report` writes the state line and the drawing, one
>    `x1,y1 -> x2,y2` line per segment.
>
> `parse`, `render`, `Command.apply`, and `Restore.apply` are pure. `Logo` holds the
> current drawing and the stack; the shell holds only `logo`.
> (`python/solution.py`; SPEC §3.)

## Trade-offs

### 2. A replay version undoes by replaying history. What does each implementation store per history entry, and what does each operation cost?

> [!answer]-
> **This implementation stores the old drawing; replay stores the command.**
> - Here, an entry is a `Restore` holding the whole drawing from before the command.
>   Undo is one pop and one assignment, O(1). The cost is memory: each saved drawing
>   has its own copy of the segments tuple, because `segments += ...` builds a new
>   tuple, so h entries over s segments hold up to O(h·s) tuple slots.
> - A replay version keeps the parsed top-level commands as its history. It
>   replays the whole history from an empty `Drawing()` on **every** `execute` and
>   every `undo`, so both cost time proportional to everything drawn in the session.
>   Its memory is just the commands.
>
> Both keep a whole `REPEAT` as one entry, so SPEC §1's history rule holds either
> way, and both are exact because commands are deterministic. Replay would stop being
> exact the moment a command read a clock or an RNG.
> (`python/notes.md` §Complexity and §Shapes chosen and rejected.)

### 3. `Command.inverse` ignores the command and returns `Restore(before)`. Why not compute a real inverse, such as `RIGHT` for `LEFT`?

> [!answer]-
> Because most commands have no inverse that depends only on themselves:
> - `PENUP`'s inverse depends on the pen before it. After `PENUP PENUP`, undoing the
>   second must leave the pen **up**, so the inverse is "set the pen to what it was",
>   not `PENDOWN`.
> - `FORWARD n`'s inverse must move back **and** remove the segment it drew, if it
>   drew one, which again depends on the pen before it.
> - `REPEAT`'s inverse is its block's inverses in reverse order, each of which has the
>   same problem.
>
> Saving `before` makes every inverse exact by construction and the same for every
> command. The notes name the middle ground: an inverse could keep only the changed
> position, heading, pen bit, and segment suffix, which is what a large canvas would
> need. (`python/solution.py`; `python/notes.md` §Discussed, not drilled.)

### 4. `FORWARD 1 SPIN` prints an error and the turtle doesn't move. Where is that guaranteed, and what would break it?

> [!answer]-
> **In `execute`'s order: parse the whole line first, then apply.** `parse` raises
> `ValueError("unknown command: SPIN")` before the loop that applies commands runs, so
> neither the drawing nor the stack changes, and `main` prints one `error:` line
> (SPEC §1–§2). An implementation that parsed and applied in one pass would move the
> turtle one cell and push one entry, then report an error for the same line, and the
> next `UNDO` would undo half of a line the user was told had failed.
>
> The same order explains two quieter cases. An empty line parses to no commands, so
> it runs, pushes nothing, and prints the state. `REPEAT 3 [ ]` parses to one command,
> so it pushes one entry that changes nothing, and the next `UNDO` appears to do
> nothing. Both follow SPEC §1: history counts top-level commands, not visible changes.
> (`python/solution.py`, `Logo.execute`.)

## Adversarial

### 5. `FORWARD 1_0` moves the Python turtle 10 cells and is an error in C and Rust, and two `FORWARD`s of 4,300 nines crash the Python program. Bugs, or contract?

> [!answer]-
> **Neither is in the contract; both are each language's integer rules.**
> - **Spellings.** `_positive` calls `int(token)`, which accepts a sign and single
>   `_` separators between digits, so `1_0` is 10 and `+3` is 3. C's `strtoll` and
>   Rust's `parse::<i64>` take the sign and leading zeros but stop at the `_`.
>   SPEC fixes plain digits and leaves the rest to each implementation. Spelling
>   out `int`'s grammar would make the ports match Python byte for byte only by
>   reimplementing Python's parser.
> - **Size.** Python's coordinates never overflow, but `int()` refuses a literal
>   of more than 4,300 digits (a `ValueError`, reported as an error line), and
>   `str()` refuses to print an integer that long. Two `FORWARD`s of 4,300 nines
>   move the turtle to a 4,301-digit x, and then `_report`, which runs in the
>   `try`'s `else`, raises outside the handler: a traceback. About a thousand
>   nested `REPEAT`s hit the recursion limit the same way. The ports have the
>   opposite limit: `int64_t` and `i64` coordinates, where an overflowing line is
>   checked with `ckd_add` or `checked_add` and rolled back as an error.
>
> Catching both in the shell would be hardening, not a design change.
> (`python/notes.md` §Shapes chosen and rejected; SPEC §1.)

## Scale

### 6. How does this program relate to a Lisp interpreter?

> [!answer]-
> It is the same pipeline at a smaller size. A Lisp interpreter has a tokenizer, a
> reader, a data representation, an evaluator, and a REPL, with *parser / renderer
> separation (reader and printer)* and a *dispatch table (special forms,
> primitives)* among its moves. Here `parse` is the reader, `Command` the data,
> `apply` the evaluator, `render` the printer, and `main` the REPL; a `REPEAT` block is
> a nested form whose brackets the reader must match, like a Lisp list. What Lisp
> adds is what this program leaves out: names, environments, closures, tail calls,
> and errors that carry a line and column. The undo half reappears in a text editor,
> whose undo and redo are the command-history move in a whole program; Editor
> Buffer (`corpus/medium/Editor-Buffer`) is a small one. (`python/notes.md` §Scales
> up to.)

## Across languages

### 7. Python's `Restore` keeps a whole `Drawing` snapshot. What does an undo entry hold in the C and Rust ports, and how does each read words, numbers, and lines?

> [!answer]-
> **Both ports shrink the snapshot, because commands only ever append
> segments.**
> - **Python** pairs each command with `Restore(before)`, a frozen `Drawing` that
>   holds the turtle's fields and the whole tuple of segments. Drawing a segment
>   copies that tuple, which is where the notes' O(s²) comes from. It reads lines
>   with `input()`, words with `upper().split()`, and numbers with `int`.
> - **Rust** keeps `undo: Vec<(Turtle, usize)>`: a `Copy` turtle and the
>   segment count. Undo restores the turtle and calls `truncate`. A parsed
>   program is `enum Command { …, Repeat(i64, Vec<Command>) }`; the `Vec` holds
>   its items on the heap, so the recursive type needs no `Box`. It reads with
>   `stdin().lines()`, `split_whitespace`, and `parse::<i64>`, and moves with
>   `checked_add`, so `run` returns `Option<()>`.
> - **C** keeps an array of `Turtle`s that carry their own segment count. A
>   parsed line is one flat array of `Command`s in preorder, and a `REPEAT`
>   records `span`, the length of its body, so the parse builds no pointers. It
>   grows a line buffer with `getchar` (a fixed `fgets` buffer would cut a long
>   `REPEAT`), splits at `isspace`, reads numbers with `strtoll`, and moves with
>   `ckd_add`, so `apply` returns `bool`.
>
> All three keep the command objects and their undo, and print the same drawing.
> On an overflow both ports put back the line's first undo entry, which is the
> history doing a second job: making a failed line change nothing.
> (`c/notes.md` and `rust/notes.md`.)
