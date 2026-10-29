# Adventure Rooms — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or the
code. The last compares the C and
Rust ports; attach their `solution` files to the
committee prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small text-adventure program, specified in
> SPEC.md and implemented in solution.py. Ask the questions from DEFENSE.md one at a
> time, in order. After each answer, press on anything vague: demand the specific
> structure, failure mode, or line of SPEC. Don't accept "it's more extensible"
> without the mechanism. Keep a list of claims that contradict SPEC.md or the code,
> and read it back at the end. Don't reveal the answer callouts unless the candidate
> concedes.*

## Lifecycle

### 1. Trace `take lamp`, `go north`, `dance`, then end of input, from stdin to the last line

Name each function the input passes through, what changes, and what the shell holds
between turns.

> [!answer]-
> 1. `main` calls `new_game`, which builds one dict: room `hall`, an empty
>    inventory, a fresh copy of every room's item list, and `over` false. It prints
>    `_look(state)`, the hall's three-line look text.
> 2. `input()` reads `take lamp` without its `\n`. `execute` checks `over`, trims, and splits at the first space into `take` and
>    `lamp`, then calls `VERBS["take"]`, which is `_do_take`. It moves `lamp` from
>    `state["items"]["hall"]` to `state["inventory"]` **in place** and returns the
>    same dict with `Taken.`.
> 3. `go north` reaches `_do_go`, which sets `state["room"]` to `library` and
>    returns the library's look text.
> 4. `dance` misses the table, so `execute` raises `unknown verb: dance` before
>    touching anything. `main` prints the message and keeps its binding.
> 5. At end of input `input()` raises `EOFError`, and `main` returns without
>    writing anything (SPEC §2).
>
> Between turns the shell holds one binding, `state`. For the built-in verbs it is
> the same dict object the whole session, because every handler returns the state
> it was given. `_look` only reads it. (`python/solution.py`; SPEC §4.)

## Trade-offs

### 2. Why a `VERBS` table rather than an if/elif ladder?

> [!answer]-
> **The table makes verb selection data.** Adding a verb is a handler and an entry;
> `execute` never changes. In a ladder, selection and behavior are welded
> into one function, so a new verb is an edit to the engine. The seam shows
> behaviorally: register `xyzzy` into `VERBS` at run time, and `execute` finds it,
> because it indexes `VERBS[verb]` on every call rather than a copy.
> The cost is indirection: a reader follows the table to the handler. For a closed
> six-verb game the ladder is locally more readable, and the notes' *Reversal
> pressures* paragraph says so. Growing verbs favor the table. (`python/notes.md`
> §Shapes chosen and rejected.)

### 3. A world-as-data version puts the whole map in one `WORLD` value. Why keep three module constants here, and when would `WORLD` win?

> [!answer]-
> **One fixed world doesn't need an interpreter.** `DESCRIPTIONS`, `EXITS`, and
> `START_ITEMS` read directly, and every handler indexes them by room name. The
> data version makes the engine generic: `new_game(world)` builds the session from
> any world, even a two-room world the program never saw. It pays for that with a
> schema the engine trusts but never validates, and a copy of every room's item
> list per session. It wins as soon as content grows or must be swapped, for
> example loaded from a file, and then the schema becomes a boundary that needs
> checking. (`python/notes.md` §Shapes chosen and rejected.)

### 4. `execute` mutates the state in place and also returns it. Why does `main` still rebind `state`, and what can't its `except` branch undo?

> [!answer]-
> **The return value is the contract; in-place mutation is an implementation
> detail.** Every handler has the shape `(state, arg) -> (state, output)`, so a
> handler that built a new state instead of mutating would work unchanged, because
> `main` always keeps what came back. On a `ValueError`, `main` keeps its old
> binding, and that is safe for the built-in failures: the unknown-verb and
> game-over guards raise before anything changes. It is not a rollback. A
> registered handler that mutates the dict and then raises leaves its change
> behind, and the old binding *is* that mutated dict. Making failures atomic would
> need copies or a new-state discipline in every handler.
> (`python/notes.md`, the composition-root paragraph.)

## Adversarial

### 5. A Windows terminal sends `take lamp\r\n`. What does each implementation print, and why doesn't SPEC rule the line out?

> [!answer]-
> **All three print their `Taken.`, each for its own reason.** `input()` removes
> only the `\n`, but `execute` trims with `str.strip()`, which removes all 29
> characters Python counts as whitespace, `\r` among them. Rust's `lines()` drops
> the `\r\n` together, and its `trim()` removes Unicode whitespace much as
> Python's does. C cuts the line at `\n` and trims with `isspace`, which covers the ASCII
> whitespace, `\r` included, but not U+00A0 or U+3000.
>
> Ruling out every whitespace character but the space would let one exact
> transcript fit all three, but pinning Python's answer would force every port to
> carry Python's whitespace table, and pinning a port's would mean changing the
> drilled core to `strip(" ")`. SPEC §2 fixes only the space, so the question is
> each language's, and each answers it with its own trimming. A line with U+00A0
> around a word is where they differ: Python and Rust trim it, C keeps it and
> finds no such item. (SPEC §2; `python/notes.md` §Shapes chosen and
> rejected.)

## Scale

### 6. How does this dispatch reappear in a Unix shell?

> [!answer]-
> **As its builtins table.** A shell looks the first word of a parsed line up
> among builtins such as `cd`, `exit`, and `export`, as a verb is looked up in
> `VERBS`, and `exit` ends the loop as `quit` does. In interactive mode EOF exits,
> as end of input ends this session. What changes is the miss: here an unknown
> verb is an error line, while in the shell a word outside the table names a
> program to run with `fork`, `exec`, and `wait`. And the shell must tokenize with
> quoting and expand before it can find the first word. (`python/notes.md` §Scales up to.)

## Across languages

### 7. Python's `VERBS` is a dict a caller can extend at run time. How do the C and Rust ports store the verb table and read a line, and what do they give up?

> [!answer]-
> **Both ports fix the table at compile time and read lines their language's
> usual way.**
> - **Python** looks verbs up in `VERBS` when each line runs, so a caller can
>   register a brand-new verb and `execute` finds it. Handlers mutate the state
>   dict and also return `(state, output)`. The shell reads with `input()`.
> - **Rust** keeps `const VERBS: [(&str, Handler); 6]`, with
>   `type Handler = fn(&mut State, &str) -> String`. A handler changes the state
>   through `&mut` and returns only the text. A `match` on the verb would rebuild
>   the if/elif ladder, and a `HashMap` would only add run-time
>   registration, which nothing in the program uses. `main` loops over
>   `io::stdin().lines()` and stops once `quit` sets `over`; `execute` trims with
>   `trim()`.
> - **C** keeps an array of `{verb, Command *}` pairs, with
>   `typedef void Command(State *, const char *)`.
>   Handlers print their own lines. Rooms and items are `enum`s, so the world
>   tables are arrays indexed by room, and the whole `State` is a 152-byte struct
>   with no heap. `main` reads with `fgets` into a 256-byte buffer; `execute`
>   copies the line, trims it with `isspace`, and splits it at the first space
>   with `strchr`, so verbs and arguments are ordinary C strings.
>
> The dispatch-table move survives: a new verb is a new table row, not an edit to
> `execute`. What the ports give up is registration while the program runs, the
> property registering `xyzzy` in Python shows. A byte-and-length line grown with
> `realloc` would let C repeat any argument byte for byte as Python does; a fixed
> buffer is the ordinary C choice when wording is each implementation's.
> (`c/notes.md` and `rust/notes.md`.)
