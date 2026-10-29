## Command Objects — worked example

**Intuition.** The command-history move: reify each edit as a frozen
value that knows `apply` and `invert`, and undo/redo stop being features
you write — they fall out of the representation. `undo` is pop +
apply-inverse; `redo` is pop + re-apply; the redo-clearing invariant is
one `clear()` in the single `_do` choke point every edit goes through.
The load-bearing move is in `delete`: it captures the removed text when
it constructs the `Delete`, because that is the exact information the
inverse needs and the buffer is about to destroy. The natural
implementation: an editor's history IS a sequence of actions, and here the
program says so.

Worked check: insert "hello", insert " world" at 5, delete 6 chars at 0 →
"world"; undo re-inserts the captured "hello " → "hello world"; undo again
→ "hello"; redo replays the recorded Insert → "hello world".

**Complexity.**
- Time: $O(b)$ string rebuild per edit/undo/redo; Space: $O(e)$ per
  history entry (the edit's own text, not the buffer).

**Discussed, not drilled.** Reified commands buy more than undo: a command
list is a log, a macro, a replay — the dataclass value semantics make
that safe. Real editors coalesce keystrokes into one command and cap
history; both are policy on top of this exact representation. The guards
validate BEFORE constructing the command — that ordering is what keeps a
failed edit from touching either history.

**The shell.** A line loop over `i/d/u/r/p/q`, read with `input()`.
`_command` parses each line and returns `None` for anything malformed, which
gets the `HELP` line, so the shell's one `except ValueError` catches only
the buffer's guards. The tiny verb ladder is fine at six verbs; Adventure
Rooms (`corpus/medium/Adventure-Rooms`) makes the case for a table when verbs
are the program.

## Shapes chosen and rejected

- **Command objects (chosen)** over **snapshot history**. Snapshots push the
  whole text before every edit, so each history entry costs the buffer's size
  and records a state, not what happened. A command costs its own text and *is* the edit, so the history
  can also serve as a log, a macro, or a replay. The price is the inverse:
  `delete` must capture the removed text before the buffer loses it.
- **Positions count characters, not bytes, and not ASCII only.** Python's `str`
  indexes code points, so the reference needs no conversion. Bytes would let
  `d` cut a UTF-8 sequence in half, and `p` would then print invalid UTF-8. An
  ASCII-only precondition would avoid the question instead of answering it. The
  ports pay for this choice: C and Rust must decode UTF-8 to find the `p`-th
  character. A full-screen editor may pin the opposite choice (below); either
  is defensible once it is written down.
- **A line protocol, read the Python way.** The Python-isms that would leak
  into the output are kept out of it:
  - `line.strip()` and `rest.split()`, which trim Unicode whitespace;
  - unpacking and `int()` errors printed as the protocol's output
    (`not enough values to unpack (expected 2, got 1)`);
  - `repr(buffer.text)` for `p`, which switches between `'` and `"` and escapes
    by Python's rules.

  A malformed line gets the usage line, `p` prints the text between `"`
  without escaping, and the only messages are the buffer's own. The shell
  reads with `input()`, a number is any run of ASCII digits (`isascii()`
  beside `isdigit()`, so `٣` is refused), and a `\r` from a
  `\r\n` terminal is inserted as text, which `p` echoes. Python's `int` refuses
  past 4,300 digits with a `ValueError` that `_command` doesn't catch, so such a
  line ends the session with a traceback; no editor user types one.
- **What `p` shows is the program's data.** The text between two `"`, character
  for character, is the one output every implementation shares exactly, and
  SPEC §5 fixes it byte for byte. Refusal wording is each implementation's own.
- **No prompt and no usage banner at start.** A prompt would interleave with
  every answer, and successful edits print nothing, so a session's output is
  just its `p` lines and refusals. End of input ends the session silently:
  the shell catches `input()`'s `EOFError` rather than exiting 1.

## Scales up to

A kilo-style terminal editor adds undo and redo as the same command-history
move; there it lives in a whole program. Its spec must pin the text encoding,
and one defensible choice is a buffer of bytes with ASCII displayed and other
bytes shown by a defined substitution, leaving UTF-8 display width out. This
program pins characters instead, because its only display is `p`. Such an
editor's representation is usually an array of lines, with gap buffers, piece
tables, and ropes as the alternatives; this program's single string, rebuilt
on every edit, is the simplest member of that family.
