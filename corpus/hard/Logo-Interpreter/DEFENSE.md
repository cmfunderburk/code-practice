# Logo Interpreter — oral defense

Seven questions about the design of the Logo interpreter, for practising explaining
it aloud. Answer each question with its answer closed, then open the answer to
check yourself. Each answer starts with the main point and names the file that
settles it: `SPEC.md`, `python/solution.py`, or `python/notes.md`.

Question 7 compares the Python version with the C and Rust versions, which are in
`c/` and `rust/`.

> [!note]- Examiner prompt
> Paste this into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached (for question 7, attach the C and Rust
> `solution` files too):
>
> *You are examining a student on a small Logo interpreter, specified in SPEC.md and
> implemented in solution.py. Ask the questions from DEFENSE.md one at a time, in
> order. After each answer, ask follow-up questions about anything vague: ask for
> the specific function, input, or line of SPEC. Don't accept "undo is just a
> stack" unless the student says what each entry holds and how much work one undo
> does. Keep a list of claims that contradict SPEC.md or the code, and read it back
> at the end. Don't show the answers unless the student gives up.*

## Following a line through the program

### 1. Trace three input lines through the program

The user types these three lines, one after another: `FORWARD 2 LEFT`, then
`penup REPEAT 2 [ FORWARD 1 RIGHT ]`, then `UNDO`. For each line, say which
functions and methods it passes through, what `Logo` holds afterwards (the
turtle's state, and how many entries are on its undo stack), and what the program
prints.

Then say which of those functions are *pure*: they compute a result from their
arguments and change nothing else.

> [!answer]-
> **Each line is parsed whole, then applied one top-level command at a time, with
> one undo entry per top-level command.**
> 1. `input()` returns each line without its `\n`. `main` asks `_is_undo` whether
>    the line's only word is `UNDO`. For the first two lines it isn't, so `main`
>    calls `logo.execute(line)`.
> 2. `execute` calls `parse`, which puts spaces around `[` and `]`, converts the
>    line to uppercase, splits it into words, and passes the words to `_parse`. For
>    line 1, `_parse` builds `Command("forward", 2)` and `Command("left")`. For
>    line 2, it builds `Command("penup")` and one `Command("repeat", (2, body))`,
>    where `body` is `(Command("forward", 1), Command("right"))`; `_parse` calls
>    itself once to read the block.
> 3. For each top-level command, `execute` keeps the current drawing as `before`,
>    sets `self._drawing = command.apply(before)`, and pushes
>    `command.inverse(before)`, a `Restore` holding `before`. After line 1 the
>    turtle is at (2, 0) heading N, and the stack holds 2 entries. After line 2 it
>    holds 4: the `REPEAT`'s `apply` runs its two children twice each, but only the
>    `REPEAT` itself gets an entry. The turtle is at (3, 1) heading S with the pen
>    up, and there is still one segment, because the pen was up for both moves.
> 4. For `UNDO`, `main` calls `logo.undo()`, which pops the `REPEAT`'s `Restore`
>    and applies it. That returns the saved drawing: (2, 0), heading N, pen up, one
>    segment. The stack holds 3 entries.
> 5. After each line, `main` prints `_report(logo)`: the state line, then one
>    `x1,y1 -> x2,y2` line per segment. All three reports show the one segment
>    `0,0 -> 2,0`.
>
> `parse`, `_parse`, `render`, `Command.apply`, `Command.inverse`, and
> `Restore.apply` are pure: each returns its result and changes nothing passed
> to it. `Logo.execute` and `Logo.undo` are not, since they replace `Logo`'s drawing
> and change its stack. `main` keeps only `logo` from one line to the next.
> (`python/solution.py`; SPEC §3.)

## Design choices

### 2. Two ways to undo: save the old drawing, or replay the history

`Logo` undoes by saving. Before each top-level command runs, `execute` pushes a
`Restore` holding the whole drawing from before it, and `undo` pops one and puts
that drawing back.

Another way to undo is by replaying. Keep a list of the parsed top-level commands
instead. To undo, remove the last command from the list, then start again from an
empty `Drawing()` and apply every command left in the list.

Compare the two designs. What does each store per history entry? How much work
does one undo do in each as the session grows? And what must be true of the
commands for replay to give exactly the right drawing?

> [!answer]-
> **Saving stores a drawing per entry and undoes in constant time; replay stores
> only the commands and redoes the whole session on every undo.**
> - In `Logo`, an entry is a `Restore` holding the drawing from before the command.
>   `undo` is one `pop` and one assignment, so it takes the same time however long
>   the session has run. The price is memory: `Command.apply` builds a new
>   `segments` tuple each time it draws (`segments += ...`), so every saved drawing
>   has its own tuple. With h entries over s segments, the saved tuples hold up to
>   h·s slots in all (the segment pairs inside them are shared, not copied).
> - A replay design stores only the parsed commands, which are small. But each
>   undo applies every remaining command again from the start, so its time grows
>   with everything the session has drawn.
> - Replay is exact only if the same commands, applied to the same starting
>   drawing, always give the same result. That holds here: no command reads a
>   clock, a random number, or input. A command that did could draw something
>   different when replayed.
>
> Either design can keep a whole `REPEAT` as one entry, so either can follow SPEC
> §1's history rule. (`Logo.execute` and `Logo.undo` in
> `python/solution.py`; `python/notes.md` §Design choices.)

### 3. Why every command's inverse is a saved drawing

Each `Command` has a method `inverse(before)`, which returns an object whose
`apply` undoes the command. In `solution.py`, `inverse` ignores the command itself
and always returns `Restore(before)`, which holds the drawing from before the
command ran.

Another design would compute an inverse from the command alone: `RIGHT` for
`LEFT`, `PENDOWN` for `PENUP`, and for `FORWARD n`, a move of n cells back. For
`PENUP`, `FORWARD n`, and `REPEAT`, say whether such an inverse would work, and
give a short program where it would undo to the wrong drawing.

> [!answer]-
> **Most commands have no inverse that depends only on the command; the right
> undo depends on the drawing before it ran.**
> - **`PENUP`:** after `PENUP PENUP`, undoing the second `PENUP` must leave the pen
>   up, because it was already up. An inverse of `PENDOWN` would put it down. The
>   correct undo is "set the pen to what it was before", which needs `before`.
> - **`FORWARD n`:** moving back n cells restores the position, but the undo must
>   also remove the segment the move drew, and only if it drew one. After
>   `FORWARD 2` with the pen down, moving back 2 would draw a second segment
>   instead of removing the first.
> - **`REPEAT`:** its inverse would be the inverses of every command it ran, in
>   reverse order, so it has both problems above, once per repetition.
>
> Only `LEFT` and `RIGHT` have exact inverses of their own. Returning
> `Restore(before)` gives every command an exact undo with the same one line of
> code. Its drawback is size: each saved drawing carries all its segments. An
> inverse could instead save only what a command can change: the position,
> heading, pen, and how many segments there were. The C and Rust versions do this
> (question 7). (`Command.inverse` and `Restore` in `python/solution.py`;
> `python/notes.md` §Design choices.)

### 4. A line with a mistake at the end

The user types `FORWARD 1 SPIN`. `SPIN` is not a command, so SPEC §1 says the line
is an error and nothing on it runs, not even the `FORWARD 1` before the mistake.

Which lines of `Logo.execute` guarantee this? Describe an `execute` that would
break the rule, and say what the user would see after typing `UNDO` next. Then
explain what `execute` does with an empty line, and with `REPEAT 3 [ ]`.

> [!answer]-
> **`execute` parses the whole line before it applies anything.**
> `for command in parse(source):` calls `parse` once, before the loop body first
> runs. `_parse` raises `ValueError("unknown command: SPIN")` while it reads the
> words, so the loop never starts: the drawing and the stack are unchanged, and
> `main` prints one line, `error: unknown command: SPIN` (SPEC §1–§2).
>
> An `execute` that read one command and applied it before reading the next would
> move the turtle one cell and push one entry for `FORWARD 1`, then reach `SPIN`
> and raise. The user would be told the line failed, yet the next report would
> show the turtle at (1, 0), and the next `UNDO` would remove a move from a line
> that supposedly never ran.
>
> The same order explains two quieter cases. An empty line parses to no commands,
> so the loop runs zero times: nothing is pushed, and `main` prints the report.
> `REPEAT 3 [ ]` parses to one command, so `execute` pushes one entry that changes
> nothing visible, and the next `UNDO` seems to do nothing. Both follow SPEC §1:
> history counts top-level commands, not visible changes.
> (`Logo.execute` in `python/solution.py`; `test_a_bad_line_runs_nothing`
> and `test_nested_and_empty_blocks` in `test_program.py`.)

## Unusual input

### 5. Numbers that Python reads differently

`_positive` reads a count or distance with Python's `int()`, which accepts more
than plain digits: `int("+3")` is 3, `int("007")` is 7, and `int("1_0")` is 10,
because Python allows `_` between digits. Python's integers have no size limit for
arithmetic, but Python refuses to convert an integer of more than 4,300 digits to
or from a string: `int()` and `str()` raise `ValueError`.

What does the program print for `FORWARD 1_0`? What happens when the user types
`FORWARD` followed by 4,300 nines, and then the same line again? (Look at where
`main` calls `_report`.) Is either behavior allowed by SPEC?

> [!answer]-
> **`FORWARD 1_0` moves the turtle 10 cells, which SPEC allows. The second
> 4,300-digit line stops the program with a traceback, which SPEC does not.**
> - `int("1_0")` is 10, so `FORWARD 1_0` draws `0,0 -> 10,0`. SPEC §1 fixes only
>   plain digits and lets each version read other spellings with its own integer
>   parser. The C version's `strtoll` and the Rust version's `parse::<i64>` also
>   accept `+3` and `007`, but stop at the `_`, so both report `FORWARD 1_0` as an
>   error.
> - A 4,300-digit number is just within `int()`'s limit, so the first line moves
>   the turtle to an x of 4,300 nines, and `_report` can still print it. The second
>   line moves it to an x of 4,301 digits. `execute` succeeds, and `main` calls
>   `_report` in the `else` branch of its `try`, which its `except ValueError` does
>   not cover. `str()` raises `ValueError` while `_report` formats x, and the
>   program stops with a traceback and exit status 1.
>
> SPEC §1 lets each version decide how far its turtle may travel, but SPEC §2 says
> the program exits with status 0 on any well-formed input, so this crash is a gap
> in the Python version. About a thousand nested `REPEAT`s cause another: `_parse`
> calls itself once per `[`, Python's recursion limit raises `RecursionError`, and
> `main` doesn't catch that either. The C and Rust versions have different limits:
> their coordinates are 64-bit integers, and a line that would overflow them is
> answered with an error line and changes nothing (question 7).
> (`_positive` and `main` in `python/solution.py`;
> `python/notes.md` §Design choices; SPEC §1–§2.)

## Beyond this program

### 6. The stages of an interpreter

Most interpreters work in the same stages as this program. A *tokenizer* splits
the source text into words. A *parser* builds a structure from the words, often a
tree. An *evaluator* runs that structure. A *REPL* (read-eval-print loop) reads a
line, evaluates it, prints the result, and repeats.

Name the function or class that does each stage in this program. Then think about
an interpreter for a small Lisp, a language whose programs are nested lists in
parentheses, such as `(define (square x) (* x x))`. Which part of this program is
most like reading a nested list? Name two things a Lisp interpreter needs that
this program does not have.

> [!answer]-
> **All four stages are here, in small.**
> - **Tokenizer:** the first line of `parse`, which puts spaces around the brackets,
>   converts to uppercase, and splits.
> - **Parser:** `_parse`, which turns the words into a tuple of `Command`s, nested
>   inside `REPEAT`s. `render` does the reverse, from commands back to text, which
>   is the job of a Lisp interpreter's *printer*.
> - **Evaluator:** `Command.apply`, which runs one command against a drawing, and
>   `Logo.execute`, which runs a whole program.
> - **REPL:** `main`, which reads a line, executes or undoes it, and prints the
>   report.
>
> A `REPEAT` block is the nearest thing to a Lisp list. `_parse` calls itself at
> each `[` and returns at the matching `]`, as a Lisp reader calls itself at each
> `(` and returns at `)`, and both report a missing or extra closing bracket as an
> error.
>
> A Lisp interpreter needs much that this program leaves out: names, which
> `define` binds to values; *environments*, which hold those bindings; functions
> that remember the environment they were made in (*closures*); a way to run a loop
> written as recursion without the call stack growing (*tail calls*); and error
> messages that give a line and column. A Lisp interpreter written in several
> languages may also keep its integers in 64 bits and treat overflow as an error,
> so that every version gives the same answers, as the C and Rust versions here do
> with coordinates. (`python/notes.md` §Where this shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions store a program and its history

All three versions parse a whole line before running it, and push one undo entry
per top-level command. But each stores a parsed program and an undo entry in its
own way, and reads words and numbers with its own language's usual tools.

For each version, say what one undo entry holds and how a parsed `REPEAT` keeps its
block. Then find one line that one version accepts while another reports an error.

> [!answer]-
> **Python saves the whole drawing; C and Rust save only the turtle and a segment
> count, because commands only ever add segments at the end.**
> - **Python** pushes `Restore(before)`, a frozen `Drawing` with the position,
>   heading, pen, and the whole tuple of segments. A `REPEAT` is a `Command` whose
>   `arg` is a `(count, body)` pair, and `body` is a tuple of `Command`s, so a
>   parsed program is a tree. Words come from `upper().split()`, and numbers from
>   `int`.
> - **Rust** keeps `undo: Vec<(Turtle, usize)>`: a copy of the turtle (a small
>   struct that derives `Copy`, so assigning it copies it) and the number of
>   segments. `undo` puts the turtle back and calls `segments.truncate(n)`, which
>   drops the segments drawn since. A parsed program is a tree of
>   `enum Command { Forward(i64), Turn(usize), Pen(bool), Repeat(i64, Vec<Command>) }`.
>   A type that contains itself needs its children behind a pointer, and the `Vec`
>   already keeps them on the heap, so no `Box` is needed. Words come from
>   `split_whitespace` and numbers from `parse::<i64>`. Moves use `checked_mul` and
>   `checked_add`, so `run` returns `Option<()>`, with `None` for an overflow.
> - **C** keeps an array of `Turtle` structs, each with its own segment count, so
>   putting one back also cuts the drawing back. A parsed line is one flat array of
>   `Command`s in preorder (each `REPEAT` just before its body), and a `REPEAT`
>   records `span`, the number of entries in its body, nested ones included. `run`
>   steps over a command and its body with `i += 1 + span`, so parsing builds no
>   pointers. `read_line` reads with `getchar` into a buffer that grows as needed
>   (a fixed `fgets` buffer would cut a long `REPEAT` line in two), `tokenize`
>   splits words at `isspace`, numbers come from `strtoll`, and moves use `ckd_mul`
>   and `ckd_add`, so `apply` returns `false` for an overflow.
>
> When a move would overflow, C and Rust put back the first undo entry pushed for
> that line, which restores the turtle and drawing from before the line, so a
> failed line changes nothing, as SPEC §2 requires.
>
> Examples where they differ: `FORWARD 1_0` moves 10 cells in Python but is an
> error in C and Rust. `FORWARD`, a non-breaking space (U+00A0), and `2` is
> `FORWARD 2` in Python and Rust, which count Unicode spaces as whitespace, but C's
> `isspace` does not, so C reports `unknown command`. `FORWARD 9223372036854775000`
> typed twice moves Python's turtle past the 64-bit range, but C and Rust answer
> the second line with an overflow error. All three print the same reports for the
> lines the shared tests send. (`notes.md` and `solution.*` in `c/` and
> `rust/`.)
