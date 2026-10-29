# Editor Buffer — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or
the code. The last compares the C and
Rust ports; attach their `solution` files to the
committee prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small text-buffer program with undo and redo,
> specified in SPEC.md and implemented in solution.py. Ask the questions from
> DEFENSE.md one at a time, in order. After each answer, press on anything vague:
> demand the specific structure, failure mode, or line of SPEC. Don't accept "commands
> are more flexible" without naming what the history can do and what it costs. Keep a
> list of claims that contradict SPEC.md or the code, and read it back at the end.
> Don't reveal the answer callouts unless the candidate concedes.*

## Lifecycle

### 1. Trace SPEC §4's session from stdin to the last line

Name each function a line passes through, and say what the undo and redo stacks hold
after `d 0 6`, after the two `u` lines, and after `r`.

> [!answer]-
> 1. `input()` reads one line without its `\n`. `_command` parses it; `i 5  world` becomes `("i", (5, " world"))`,
>    because the text starts after the second space.
> 2. `insert` and `delete` check their guards, build a command, and hand it to
>    `_do`, which applies it, pushes it on the undo stack, and clears redo.
> 3. `d 0 6` builds `Delete(0, "hello ")`, capturing the six characters before they
>    go. The text is `world`; undo holds `Insert(0, "hello")`,
>    `Insert(5, " world")`, `Delete(0, "hello ")`; redo is empty.
> 4. Each `u` pops a command and applies its `invert()`. After two, the text is
>    `hello`, undo holds `Insert(0, "hello")`, and redo holds
>    `Delete(0, "hello ")` under `Insert(5, " world")`.
> 5. `r` pops `Insert(5, " world")` and applies it again: `hello world`, with
>    `Delete(0, "hello ")` still on redo. `i 11 !` is an edit, so `_do` clears it,
>    and the next `r` prints `nothing to redo`. `x` is malformed and gets the
>    usage line.
>
> Every read and print is in `main`; every change to the text goes through `_do`,
> `undo`, or `redo`. (`python/solution.py`; SPEC §4.)

## Trade-offs

### 2. A snapshot version pushes a copy of the whole text before each edit. What does a command buy over a snapshot, and what does it cost?

> [!answer]-
> **A command records what happened; a snapshot records a state.** A snapshot costs
> the whole buffer per entry and can only be restored. A command costs its own text,
> and because it is a frozen value that knows how to `apply` itself, the history can
> also be a log, a macro, or a replay (frozen dataclass value semantics make that
> safe). The cost is that every command needs an exact inverse, so
> `delete` must capture what it removes. Snapshots need no inverse at all, which is
> why a snapshot version's `_edit` is three lines with nothing to get wrong.
> (`python/notes.md` §Shapes chosen and rejected.)

### 3. Why does `delete` store the removed text, when `delete(pos, n)` is called with a count?

> [!answer]-
> **Because the inverse of a delete is an insert, and an insert needs the text.**
> `Delete(pos, n)` alone could apply itself, but `invert()` would have nothing to put
> back, and that text is gone from the buffer the moment the delete applies. So
> `delete` slices `self._text[pos:pos + n]` while it builds the command, before
> `_do` runs it. `Insert` has the opposite situation: its text is its argument, and
> its inverse deletes `len(text)` characters at `pos`. Storing the text also makes
> `Delete` and `Insert` symmetric: each is a position and a string.
> (`python/solution.py`; `python/notes.md` §Intuition.)

### 4. SPEC counts positions in characters. Why not bytes, and what does a bare `int()` get wrong about digits?

> [!answer]-
> **Bytes would let an edit cut a character in half.** In `héllo`, `é` is two bytes
> in UTF-8. A byte-counted `d 1 1` would remove only its first byte, and `p` would
> then print bytes that aren't valid UTF-8. So SPEC counts code points, as Python's
> `str` does. Ports must decode UTF-8 to find the `p`-th character. A code point is
> still not a glyph: `e` followed by U+0301 is two characters.
>
> A bare `int()` accepts any Unicode decimal digit, so `i ٣ z` would insert at
> position 3 (`٣` is Arabic-Indic three), and printing its errors would leak Python
> into the output, such as `invalid literal for int() with base 10: 'x'`. `_number`
> checks `isascii()` beside `isdigit()` before calling `int`, and a malformed line
> gets the usage line. (SPEC leaves a number's size to each implementation.
> Python's one limit is `int`'s own: past 4,300 digits it raises a `ValueError`
> that `_command` doesn't catch, so that line ends the session with a traceback.)
> (SPEC §1–§2; `python/notes.md` §Shapes chosen and rejected.)

## Adversarial

### 5. Run `i 0 ab`, `u`, `i 0 ` (with the trailing space), `r`. What happens, and is it a bug?

> [!answer]-
> `r` prints `nothing to redo`. `i 0 ` inserts empty text, and an insert is an edit
> whether or not it changes anything, so `_do` pushes `Insert(0, "")` on the undo
> stack and clears redo, losing the undone `ab`. A following `u` then undoes the
> empty insert, which changes nothing visible.
>
> It is the specified behavior, not a bug (SPEC §1: "Inserting empty text is legal,
> and it is an edit like any other"). A real editor might skip no-op commands or
> coalesce keystrokes, but that is policy on top of this representation, and the
> buffer's guard is about range, not effect. Note the difference from a *rejected* edit: `i 9 x` fails its guard before any command is
> built, so both stacks stay as they were.

## Scale

### 6. Where does this history reappear in a full text editor, and what changes there?

> [!answer]-
> In a kilo-style terminal editor that adds undo and redo, which is this same
> command-history move. There it is one part of a whole program: raw-mode input, a
> viewport separate from the buffer, search, and perhaps a headless mode whose core
> is a pure step, (state, key) → state. Its spec must pin the text encoding, and one
> defensible choice is a buffer of bytes with non-ASCII bytes shown by a
> substitution, the opposite of this program's choice, made for a program that has
> to draw every character on a screen. Its buffer is an array
> of lines, with gap buffers, piece tables, and ropes as the alternatives, where this
> program rebuilds one string per edit. (`python/notes.md` §Scales up to.)

## Across languages

### 7. SPEC counts positions in code points. How does each language store the text and read a command line, and how do the ports move a command between the undo and redo stacks?

> [!answer]-
> - **Python**'s `str` already indexes by code point. `Insert` and `Delete` are
>   frozen dataclasses whose `apply` builds a new string by slicing, and `invert`
>   returns a new command holding the same text. The shell reads with `input()`,
>   so a `\r` from a `\r\n` terminal stays in inserted text, and takes any run of
>   ASCII digits as a number.
> - **Rust** can't index a `String` by character, so the buffer is a
>   `Vec<char>`, edited in place with `splice` and `drain`. `enum Edit` has
>   `Insert` and `Delete` variants, each holding a position and a `Vec<char>`.
>   `invert(self)` consumes the command and moves its text into the inverse, so
>   undo and redo never copy text. The only copy is the one `delete` makes of the
>   removed characters. The shell reads with `io::stdin().lines()`, which drops a
>   `\r\n` whole, and a number is `parse::<usize>()`, which also takes `+1`; the
>   range check compares `n` with `len - pos`, so a huge `pos + n` can't overflow.
> - **C** decodes each insert from UTF-8 into `char32_t` once, edits a growable
>   array with `memmove`, and encodes back to UTF-8 only on `p`. A `Command` is a
>   `Kind` tag (`INSERT` or `DELETE`), a position, and the text it owns, so
>   inverting flips the tag. A command moves between stacks by struct copy and
>   lives on one stack at a time; clearing the redo stack frees the text it
>   drops. Lines are read by a growable `getchar` loop, since an insert's text has
>   no natural limit, and a number is ASCII digits accumulated with C23's
>   `ckd_mul` and `ckd_add`, so one too big for `size_t` is refused instead of
>   wrapping.
>
> The command-object move survives in both ports. What changes is who owns the
> text: Python shares immutable strings, Rust moves them, and C frees them by
> hand. (`c/notes.md` and `rust/notes.md`.)
