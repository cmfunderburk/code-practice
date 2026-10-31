# Adventure Rooms — oral defense

Seven questions about the design of the text adventure, for practising explaining
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
> *You are examining a student on a small text-adventure program, specified in
> SPEC.md and implemented in solution.py. Ask the questions from DEFENSE.md one at a
> time, in order. After each answer, ask follow-up questions about anything vague:
> ask for the specific function, input, or line of SPEC. Don't accept "it's more
> extensible" without the reason. Keep a list of claims that contradict SPEC.md or
> the code, and read it back at the end. Don't show the answers unless the student
> gives up.*

## Following a line through the program

### 1. Trace a short session through the program

The program starts, and the user types three lines, `take lamp`, `go north`, and
`dance`, and then ends the input (Ctrl-D at a terminal). For each line, say which
functions it passes through, what in the game's state changes, and what the
program prints. Then say what `main` keeps from one line to the next.

> [!answer]-
> **`main` keeps one variable, `state`, and every line goes through `execute`,
> which looks the verb up in `VERBS`.**
> 1. At the start, `main` calls `new_game`, which returns one dict: `room` is
>    `"hall"`, `inventory` is an empty list, `items` holds a fresh copy of every
>    room's list from `START_ITEMS`, and `over` is `False`. `main` prints
>    `_look(state)`, the hall's three lines.
> 2. `input()` returns `take lamp` without its `\n`. `execute` checks `over`,
>    removes surrounding spaces with `strip()`, and splits the line at the first
>    space with `partition(" ")` into `take` and `lamp`. It calls `VERBS["take"]`,
>    which is `_do_take`. `_do_take` removes `lamp` from `state["items"]["hall"]`,
>    appends it to `state["inventory"]`, and returns the same dict with `Taken.`,
>    which `main` prints.
> 3. `go north` reaches `_do_go`, which finds `north` in `EXITS["hall"]`, sets
>    `state["room"]` to `"library"`, and returns `_look(state)`: the library's
>    description, its exits, and `You see: book.`
> 4. `dance` is not a key of `VERBS`, so `execute` raises
>    `ValueError("unknown verb: dance")` before any handler runs. `main` catches
>    it, prints `unknown verb: dance`, and keeps its `state` as it was.
> 5. At end of input, `input()` raises `EOFError`, and `main` returns without
>    printing anything (SPEC §2).
>
> Between lines, `main` holds only `state`. For the six commands in `VERBS` it is
> the same dict object all session, because every handler changes the dict it was
> given and returns that same dict. `_look` only reads it.
> (`python/solution.py`; SPEC §4.)

## Design choices

### 2. A dictionary of handlers, or a chain of `if` statements

`execute` decides what to do with a verb by looking it up in `VERBS`, a dictionary
from each command word to the function that handles it. A dictionary used this
way is called a *dispatch table*, and the functions in it are *handlers*.

The same six commands could instead be branches of one function:

```python
def execute(state, line):
    if state["over"]:
        raise ValueError("the game is over")
    verb, _, arg = line.strip().partition(" ")
    arg = arg.strip()
    if verb == "look":
        return state, _look(state)
    elif verb == "go":
        if not arg:
            return state, "Go where?"
        ...
    elif verb == "quit":
        state["over"] = True
        return state, "Goodbye."
    raise ValueError(f"unknown verb: {verb}")
```

Suppose you add a seventh command, `sing`. What do you change in each design?
Then suppose other code runs `VERBS["xyzzy"] = handler` while the program is
running, and then calls `execute(state, "xyzzy")`. What happens in each design,
and what about the real `execute` decides it? When would the `if`/`elif` chain be
the better choice?

> [!answer]-
> **With the table, a new command is a new function and a new entry in `VERBS`;
> `execute` never changes.**
> - With `VERBS`, `sing` is a function `_do_sing(state, arg)` and one more line,
>   `"sing": _do_sing`, in the dictionary. With the chain, `sing` is a new `elif`
>   branch inside `execute`, so every new command is an edit to the function that
>   handles all the others.
> - The real `execute` reads `VERBS[verb]` every time it is called, not a copy
>   made when the module was loaded, so an entry added later is found on the next
>   call, and `execute(state, "xyzzy")` runs the new handler.
>   (`test_execute_finds_a_verb_added_to_verbs_at_run_time` checks this.) The
>   chain has no place to add a command from outside, so it raises
>   `unknown verb: xyzzy`.
> - The chain keeps choosing a command and carrying it out in one place, so a
>   reader sees all six commands without going from the table to each handler. For
>   a game whose six commands will never change, that can be easier to read. Once
>   commands are being added, the table is the better choice.
>   (`python/notes.md` §Design choices.)

### 3. Where the map lives

The map is stored in three module constants, `DESCRIPTIONS`, `EXITS`, and
`START_ITEMS`, each a dictionary keyed by room name. The handlers read them
directly, as in `EXITS[state["room"]]`.

Another design puts the whole map into one value and passes it to `new_game`,
which stores it in the state:

```python
WORLD = {
    "start": "hall",
    "rooms": {
        "hall": {"description": "a dusty entrance hall",
                 "exits": {"north": "library", "west": "garden"},
                 "items": ["lamp"]},
        ...
    },
}

def new_game(world=WORLD):
    return {"world": world, "room": world["start"], ...}
```

The handlers then read the map from `state["world"]` instead of from module
constants. What can this design do that the program as written cannot? What must
the program trust about the `world` it is given, and what happens when that trust
is wrong? When would you switch to it?

> [!answer]-
> **One `WORLD` value lets the same code play any map; the three constants
> describe exactly one map.**
> - With `new_game(world)`, a test or a second game can pass a different map, for
>   example a two-room world, and every handler works unchanged, because none of
>   them names a module constant. In the program as written, the handlers read
>   `EXITS` and `DESCRIPTIONS` directly, so a different map means editing those
>   constants.
> - The program must trust the shape of `world`: a `"start"` key that names a room,
>   every room with `"description"`, `"exits"`, and `"items"`, and every exit
>   leading to a room that exists. Nothing checks this. If an exit names
>   `"librray"`, nothing goes wrong until a player walks through it; then `_do_go`
>   moves the player there, and looking the room up raises `KeyError: 'librray'`.
>   The module constants could hold the same mistake, but they are part of the
>   source, and the shared tests walk every exit
>   (`test_every_exit_leads_where_the_map_says`). A map loaded later is never
>   seen by the tests.
> - For one fixed five-room world, the three constants are shorter and read
>   directly. The `WORLD` design is worth it once the map grows or has to be
>   replaced, for example loaded from a file, and then the program should check
>   the map's shape when it loads it. (`python/notes.md` §Design choices.)

### 4. Why `main` reassigns `state`

Every handler changes the state dict it is given and then returns that same dict,
along with the text to print. Yet `main` writes `state, output = execute(state,
line)`, reassigning `state` after every successful line, even though the dict it
gets back is the one it already had.

Why does `main` reassign it anyway? What would happen if a handler returned a new
dict instead of changing the old one? And when `execute` raises `ValueError`,
`main` keeps its old `state`: when is that the state from before the line, and
when could it not be?

> [!answer]-
> **`main` relies only on the value `execute` returns, so a handler may change the
> dict or build a new one, and `main` works either way.**
> - Every handler has the same shape, `(state, arg) -> (state, output)`, and `main`
>   always keeps the state that comes back. If `_do_take` returned a new dict with
>   the lamp moved, `main` would still hold the right state on the next line. A
>   `main` that ignored the returned state would work only as long as every handler
>   changed the dict in place.
> - When `execute` raises, the assignment doesn't happen, so `main` keeps the state
>   it had. For the program's own errors, that is the state from before the line:
>   `execute` raises `the game is over` and `unknown verb: ...` before it calls any
>   handler, so nothing has changed.
> - It is not an undo. A handler added to `VERBS` that changed the dict and then
>   raised `ValueError` would leave its change behind, and `main`'s old `state` is
>   that same, changed dict. To undo such a change, `main` would have to copy the
>   state before every line, or every handler would have to build a new state
>   instead of changing the old one. (`main` in `python/solution.py`;
>   `python/notes.md` §`main`;
>   `test_main_uses_each_returned_state_and_keeps_the_old_one_after_an_error`.)

## Unusual input

### 5. A line that ends in a carriage return

On Windows, a terminal or a file may end each line with two characters, `\r\n`
(a carriage return, then a newline), instead of just `\n`. Suppose the program
reads the line `take lamp\r\n`. What does each of the three versions print, and
which function in each one removes the `\r`?

Then suppose the line is `take lamp` followed by a no-break space (U+00A0, a
character that looks like a space). Which versions take the lamp? SPEC §2 fixes
how ordinary spaces are handled and leaves other whitespace to each version. Why
does it stop there?

> [!answer]-
> **All three print `Taken.` for the carriage return, each for its own reason;
> they differ on the no-break space.**
> - **Python:** `input()` removes only the `\n`, so `execute` receives
>   `take lamp\r`. `strip()` removes every character Python counts as whitespace
>   (29 of them, `\r` among them), so the verb is `take` and the argument `lamp`.
> - **Rust:** `lines()` removes `\r\n` as a pair, so `execute` never sees the
>   `\r`. Its `trim()` would remove it anyway.
> - **C:** `main` cuts the line at the `\n` with `strcspn`, and `trim` in
>   `execute` removes the `\r`, because `isspace` is true for it.
>
> The no-break space is where they differ. Python's `strip()` and Rust's `trim()`
> both count U+00A0 as whitespace and remove it, so both take the lamp. C's
> `isspace` covers only the ASCII whitespace characters (space, `\t`, `\n`, `\v`,
> `\f`, `\r`), so the C version keeps the no-break space as part of the argument,
> finds no item with that name, and refuses the line.
>
> SPEC stops at ordinary spaces because each language's usual trimming function
> removes a different set of characters. Requiring one answer for every whitespace
> character would mean replacing at least two of those ordinary functions with
> hand-written ones. So the shared tests send only ordinary spaces
> (`test_surrounding_spaces_are_ignored`), and the C and Rust versions' own tests
> check `\t` and `\r`. (SPEC §2; `python/notes.md` §Design choices.)

## Beyond this program

### 6. The same table in a Unix shell

A Unix shell such as `sh` or `bash` also reads one line at a time and looks at the
first word. A few words, called *builtins*, are handled by the shell itself: `cd`
changes the shell's current directory, `export` sets an environment variable, and
`exit` ends the shell. Any other first word is taken as the name of a program to
run.

Compare the shell's builtins with `VERBS`. What plays the part of the table, of a
handler, and of `quit`? What does the shell do with a first word that is not a
builtin, where this program prints `unknown verb`? And what must the shell do to a
line before it can find the first word, which `execute` does with one
`partition(" ")`?

> [!answer]-
> **The builtins are a dispatch table: the shell looks the first word up among
> them as `execute` looks a verb up in `VERBS`.**
> - The list of builtin names, each with the function that carries it out, plays
>   the part of `VERBS`, and each builtin's function plays the part of a handler.
>   `exit` ends the shell's loop as `quit` sets `over` and ends `main`'s loop. An
>   interactive shell also ends at end of input (Ctrl-D), as `main` does at
>   `EOFError`.
> - A word that is not a builtin is not an error. The shell looks for a program
>   with that name in the directories listed in `PATH`, starts it in a new process
>   (`fork`, then `exec`), and waits for it to finish (`wait`). Only when no such
>   program exists does it print an error, such as `command not found`.
> - Before the lookup, the shell must split the line into words while respecting
>   quotes and backslashes (`echo "a b"` has two words, not three), and replace
>   variables such as `$HOME` with their values. `execute` only removes
>   surrounding spaces and splits at the first space.
>   (`python/notes.md` §Where this shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions store the table and read a line

All three versions keep a table from command word to handler, but each stores it
with its own language's usual tools. For each version, say what type the table
has, what a handler receives and returns, and how `main` reads a line. Then say
what the C and Rust tables cannot do that Python's `VERBS` can, and whether
anything in the program needs it.

> [!answer]-
> **All three look the verb up in a table, so a new command is a new row; only
> Python's table can gain a row while the program runs.**
> - **Python:** `VERBS` is a `dict` from verb to handler, and `execute` looks the
>   verb up on every call. A handler changes the state dict and returns
>   `(state, output)`; `execute` raises `ValueError` for an unknown verb, and
>   `main` prints the message. `main` reads with `input()`.
> - **Rust:** `VERBS` is `const VERBS: [(&str, Handler); 6]`, with
>   `type Handler = fn(&mut State, &str) -> String`. A handler changes the state
>   through `&mut` and returns only the text. `execute` returns
>   `Result<String, String>`, an `Err` for an unknown verb, and `main` prints
>   either side the same way. `main` loops over `io::stdin().lines()`, stops after
>   `quit` sets `over`, and `execute` trims with `trim()`.
> - **C:** `VERBS` is a `static const` array of `{verb, run}` pairs, with
>   `typedef void Command(State *state, const char *arg)`. Handlers return nothing
>   and print their own lines, and `execute` prints `unknown verb: ...` itself.
>   Rooms and items are `enum`s, so the world tables are arrays indexed by room,
>   and the whole `State` is one 152-byte struct with nothing on the heap. `main`
>   reads with `fgets` into a 256-byte buffer, and refuses a longer line once with
>   `That's too long to understand.` `execute` copies the line, trims it with
>   `isspace`, and splits it at the first space with `strchr`, so the verb and the
>   argument are ordinary C strings.
>
> Python's `VERBS` is an ordinary dictionary, so any code can add a verb to it
> while the program runs. The C and Rust tables are constants fixed when the
> program is compiled, so they cannot. Nothing in the program itself adds a verb;
> only a Python test does. A Rust `HashMap` would allow it, but nothing would use
> it, and a `match` on the verb would put every command back into one function,
> like the `if`/`elif` chain in question 2. (`notes.md` and `solution.*` in
> `c/` and `rust/`.)
