# Editor Buffer — oral defense

Seven questions about the design of the text buffer with undo and redo, for
practising explaining it aloud. Answer each question with its answer closed, then
open the answer to check yourself. Each answer starts with the main point and names
the file that settles it: `SPEC.md`, `python/solution.py`, or
`python/notes.md`.

Question 7 compares the Python version with the C and Rust versions, which are in
`c/` and `rust/`.

> [!note]- Examiner prompt
> Paste this into an LLM session, with `SPEC.md`, `python/solution.py`,
> and `python/notes.md` attached (for question 7, attach the C and Rust
> `solution` files too):
>
> *You are examining a student on a small text buffer with undo and redo,
> specified in SPEC.md and implemented in solution.py. Ask the questions from
> DEFENSE.md one at a time, in order. After each answer, ask follow-up questions
> about anything vague: ask for the specific function, input, or line of SPEC.
> Don't accept "commands are more flexible" without the student saying what a list
> of commands can do that the alternative can't, and what it requires. Keep a list
> of claims that contradict SPEC.md or the code, and read it back at the end.
> Don't show the answers unless the student gives up.*

## Following a session through the program

### 1. Trace SPEC §4's session, and the two stacks

`EditorBuffer` records each edit as a *command object*: an `Insert` or a `Delete`,
each holding a position and a string. It keeps two lists used as stacks (last in,
first out): `_undo`, the edits that can be undone, and `_redo`, the edits that
have been undone and can be redone.

Take the session in SPEC §4, from `i 0 hello` to the last `p`. Say which
functions the first three lines pass through on their way from `input()` to the
text. Then write out what `_undo` and `_redo` hold after `d 0 6`, after the two
`u` lines, and after `r`, and explain why the second `r` prints
`nothing to redo`.

> [!answer]-
> **Every edit goes through `_do`; undo and redo only move commands between the
> two stacks.**
> 1. `input()` returns each line without its `\n`. `_command` parses it:
>    `i 5  world` becomes `("i", (5, " world"))`, because the text starts after
>    the second space. `main` calls `buffer.insert(5, " world")`.
> 2. `insert` and `delete` check the range, build a command, and pass it to
>    `_do`, which applies it, pushes it on `_undo`, and clears `_redo`.
> 3. `d 0 6` builds `Delete(0, "hello ")`, saving the six characters before they
>    are removed. The text is `world`. `_undo` holds `Insert(0, "hello")`,
>    `Insert(5, " world")`, `Delete(0, "hello ")`, with the last on top; `_redo`
>    is empty.
> 4. Each `u` pops a command from `_undo`, applies its `invert()`, and pushes the
>    command on `_redo`. After two, the text is `hello`, `_undo` holds
>    `Insert(0, "hello")`, and `_redo` holds `Delete(0, "hello ")` with
>    `Insert(5, " world")` on top of it.
> 5. `r` pops `Insert(5, " world")`, applies it again, and pushes it on `_undo`.
>    The text is `hello world`, and `Delete(0, "hello ")` is still on `_redo`.
>    Then `i 11 !` is an edit, so `_do` clears `_redo`, and the next `r` finds it
>    empty: `redo` raises `ValueError("nothing to redo")`, and `main` prints it.
>    `x` is not a command, so `_command` returns `None` and `main` prints `HELP`.
>
> Every `input()` and `print()` is in `main`; every change to the text happens in
> `_do`, `undo`, or `redo`. (`python/solution.py`; SPEC §4.)

## Design choices

### 2. Command objects or snapshots

There are two common ways to give a text buffer undo. This program stores
*commands*: each history entry is the edit itself, an `Insert` or `Delete` that
can apply itself and produce its inverse. The other way stores *snapshots*: before
each edit, push a copy of the whole text; to undo, push the current text on the
redo stack and restore the latest copy.

Compare the two designs. How large is one history entry in each, say for a
one-character insert into a 10,000-character text? What can a list of command
objects be used for that a list of snapshots can't? And what must the command
design get right that the snapshot design doesn't need at all?

> [!answer]-
> **A command records what the edit did; a snapshot records only what the text
> was.**
> - **Size.** A snapshot entry is the whole text, 10,000 characters for the
>   one-character insert. A command entry is a position and the edit's own text,
>   one character.
> - **Uses.** Because a command describes the edit, a list of them is also a log
>   of what the user did, and it can be applied again, to the same text or to
>   another one, as a replay or a macro. `Insert` and `Delete` are frozen
>   dataclasses, so a command can't change after it is recorded, and two commands
>   with the same fields are equal (`test_commands_are_values_that_apply_and_invert`
>   checks this). A list of snapshots can only be restored.
> - **What it requires.** Every command needs an exact inverse, so `delete` must
>   save the text it removes (question 3). The snapshot design needs no inverse:
>   pushing a copy and restoring it is a few lines with nothing to get wrong. The
>   tests use exactly that design as their reference.
>
> (`python/solution.py`; `python/notes.md` §Design choices.)

### 3. Why `Delete` stores text, not a count

`delete(pos, n)` is called with a position and a count. But the `Delete` it builds
does not store `n`; it stores the removed characters, `self._text[pos:pos + n]`.

Suppose `Delete` stored `pos` and `n` instead. Could it still apply itself? What
would `invert` have to return, and where would it get what it needs? Why must
`delete` slice the text before calling `_do`, rather than after?

> [!answer]-
> **The inverse of a delete is an insert, and an insert needs the text.**
> `Delete(pos, n)` could still apply itself: remove `n` characters at `pos`. But
> its `invert()` would have to return `Insert(pos, ?)`, and the characters to put
> back are gone from the buffer the moment the delete is applied. So `delete`
> slices `self._text[pos:pos + n]` while it builds the command, before `_do`
> applies it. After `_do`, the buffer no longer holds those characters.
>
> `Insert` doesn't have this problem: its text is its argument, and its inverse
> deletes `len(text)` characters at `pos`. Storing the text also makes the two
> classes the same shape, a position and a string, so `invert` only swaps the
> class. (`Delete.apply` and `delete` in `python/solution.py`.)

### 4. Counting characters and reading numbers

SPEC §1 counts positions in characters (Unicode code points), not bytes. In UTF-8,
`é` is two bytes.

First: suppose the buffer holds `héllo` and the user types `d 1 1`. What does this
program print for the next `p`? What would a program that counted bytes remove
instead, and what would its `p` print?

Second: `_number` accepts a field only when `text.isascii() and text.isdigit()`
are both true. What would `i ٣ z` do if `_number` checked only `isdigit()`?
(`٣` is the Arabic-Indic digit three.)

> [!answer]-
> **Counting bytes would let an edit cut a character in half, and `isdigit()` alone
> accepts digits SPEC doesn't mean.**
> - This program prints `"hllo"`: Python's `str` is a sequence of code points, so
>   index 1 is the whole `é`. A program counting bytes would remove only the first
>   of `é`'s two bytes, and its `p` would print a lone continuation byte, which is
>   not valid UTF-8 (many terminals show it as `�`). A code point is still not always
>   one visible character: `e` followed by U+0301, a combining accent, is two
>   characters that display as one `é`
>   (`test_a_combining_mark_is_its_own_character`).
> - `"٣".isdigit()` is true, and `int("٣")` is 3, so `i ٣ z` would insert `z` at
>   position 3. With the `isascii()` check, `_number` returns `None`, `_command`
>   returns `None`, and `main` prints the `HELP` line.
>
> (SPEC §1–§2; `_number` in `python/solution.py`;
> `python/notes.md` §Design choices.)

## Unusual input

### 5. An empty insert, and a refused one

SPEC §2 says `i 0 ` (with a space after the `0`) inserts empty text. The user types
these four lines: `i 0 ab`, `u`, `i 0 `, `r`.

What does the program print, and what do `_undo` and `_redo` hold after each line?
Is the result what SPEC asks for? Then replace `i 0 ` with `i 9 x`, an insert past
the end of the text, and say what changes.

> [!answer]-
> **`r` prints `nothing to redo`, and SPEC asks for exactly that.**
> After `i 0 ab` and `u`, the text is empty and `Insert(0, "ab")` is on `_redo`.
> `i 0 ` inserts empty text. The position is in range, so `insert` builds
> `Insert(0, "")` and `_do` pushes it on `_undo` and clears `_redo`, losing the
> undone `ab`. So `r` finds `_redo` empty. A `u` after that would undo the empty
> insert, which changes nothing visible. SPEC §1 says "Inserting empty text is
> legal, and it is an edit like any other" (`test_an_empty_insert_is_an_edit`). A
> real editor might skip edits that change nothing, but that would be a rule
> added on top of these commands, and the check in `insert` is only about the
> range.
>
> With `i 9 x` instead, the position is past the end of the empty text, so
> `insert` raises `ValueError("insert out of range: 9")` before any command is
> built. `main` prints that message, `_do` never runs, and both stacks stay as
> they were. Now `r` redoes `ab`, and `p` would print `"ab"`
> (`test_a_refused_edit_keeps_both_histories`). (`insert` and `_do` in
> `python/solution.py`; SPEC §1.)

## Beyond this program

### 6. The same buffer inside a full-screen editor

This program keeps the whole text in one Python string, builds a new string on
every edit, and counts positions in code points. Its only display is the `p`
command.

A full-screen terminal text editor, such as antirez's *kilo* (under a thousand
lines of C), draws the text on the screen and redraws it after every key. Undo
and redo could be added to it with the same `Insert` and `Delete` commands. Name
two decisions in this program that such an editor would make differently: how it
stores the text, and how it counts positions. For each, say what the editor would
do instead, and why.

> [!answer]-
> **The commands carry over; the storage and the counting change, because the
> editor edits large files one key at a time and has to draw every character.**
> - **Storage.** Rebuilding one string per edit costs time proportional to the
>   whole text on every keystroke. Kilo stores an array of lines, so most
>   keystrokes change only one short line. Other editors use a *gap buffer* (an
>   array with an empty gap at the cursor, so typing fills the gap), a *piece
>   table* (a list of spans, each pointing into the original file or into a
>   buffer of added text), or a *rope* (a tree of short strings). A command's
>   position then becomes a line and column, or an offset into that structure.
> - **Counting.** Here a code point is a fine unit because `p` prints the text
>   and nothing else. An editor must decide how many screen columns each
>   character takes: some take two columns, and a combining accent takes none.
>   One simple choice is to store bytes, show ASCII as it is, and show every other
>   byte as a placeholder, leaving out the width of non-ASCII characters. Whatever
>   it chooses, it has to write the choice down, as SPEC §1 does here.
>
> Such an editor would also usually group a run of typed characters into one
> undo step and limit how long the history grows. Both are rules added on top of
> the same commands. (`python/notes.md` §Where this shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions store the text and move commands

All three versions record edits as command objects and keep an undo stack and a
redo stack. Each stores the text, and the characters inside each command, with its
own language's usual tools.

For each version, say: what holds the text, and how a position finds its
character; what happens to a command's characters when `undo` moves the command
from the undo stack to the redo stack; and how `main` reads a line and a number.
Then find one line that one version accepts as a command while another refuses
it.

> [!answer]-
> **The command objects are the same in all three; what differs is who owns each
> command's characters, and how a line is read.**
> - **Python** stores the text as a `str`, which is already indexed by code point.
>   `Insert` and `Delete` are frozen dataclasses, and `apply` builds a new string
>   by slicing. `invert` returns a new command that refers to the same string,
>   which is never copied, because Python strings can't change. `main` reads with
>   `input()`, which keeps a `\r` from a `\r\n` line ending, and takes any run of
>   ASCII digits as a number.
> - **Rust** can't index a `String` by character, so the text is a `Vec<char>`,
>   edited in place with `splice` and `drain`. `enum Edit` has `Insert` and
>   `Delete` variants, each holding a position and a `Vec<char>`. `invert(self)`
>   takes the edit by value and moves its `Vec<char>` into the new variant, so
>   `undo` (invert, apply, invert back, push) never copies text. The only copy is
>   the one `delete` makes of the removed characters. `main` reads with
>   `io::stdin().lines()`, which drops a whole `\r\n`, and reads a number with
>   `parse::<usize>()`, which also accepts a leading `+`. `delete` compares `n`
>   with `len - pos`, so a huge `pos + n` is never computed.
> - **C** decodes each inserted line from UTF-8 into `char32_t` code points once,
>   keeps the text in a growable array that it edits with `memmove`, and encodes
>   back to UTF-8 only for `p`. A `Command` is a `Kind` tag (`INSERT` or
>   `DELETE`), a position, and an array of characters it owns; `inverse` flips the
>   tag on a temporary copy. A command moves between the stacks by copying the
>   struct, so exactly one stack holds it at a time, and clearing the redo stack
>   frees the arrays it drops. `main` reads lines with a `getchar` loop into a
>   growable buffer, since an insert's text has no length limit, and a `\r`
>   stays in the line. A number is ASCII digits added up with C23's `ckd_mul`
>   and `ckd_add`, so a number too big for `size_t` makes the line not a command,
>   instead of wrapping around.
>
> Examples where they differ: `i +0 x` inserts `x` in Rust, but Python and C answer
> with the `HELP` line. `i 99999999999999999999 x` is
> `insert out of range: 99999999999999999999` in Python, but C and Rust answer with
> the `HELP` line. A line `u` ending in `\r\n` is an undo in Rust, but Python and C
> see `u\r` and answer with the `HELP` line. On the plain lines the shared tests
> send, all three print the same, which is all SPEC §5 requires.
> (`notes.md` and `solution.*` in `c/` and `rust/`.)
