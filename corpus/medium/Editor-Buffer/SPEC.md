# Editor Buffer — SPEC

This document specifies a small text editor that keeps one buffer of text and
unlimited undo and redo, and takes one command per line. There are three versions
of it, in Python, C, and Rust, and each is written the way a programmer in that
language would usually write it. All three must agree on the buffer (§1): its
text, counted in characters, and what `p` shows of it. They may differ in how they
word an error message and in which unusual lines they accept as commands, such as
a number with a sign, a very large number, a non-ASCII digit, or a line ending in
a carriage return (`\r`).

The Python version's API is in `python/problem.md`. Each version has its own
tests, and all three also run the shared tests in `test_program.py`, which check
only the facts in §5.

## 1. The buffer

The program edits one text buffer, which starts empty, and keeps unlimited undo and
redo.

- The text is a sequence of **characters**, meaning Unicode code points. Positions
  and counts are in characters, not bytes: `é` is one character, though UTF-8
  spells it in two bytes.
- **Insert** at position `p` puts text before the character at index `p`. Legal
  positions are `0` to the length of the text, so inserting at the end is legal.
  Inserting empty text is legal, and it is an edit like any other.
- **Delete** of `n` characters at position `p` removes the characters at indexes
  `p` to `p + n − 1`. It needs `n ≥ 1` and `p + n` at most the length of the text.
- **Undo** reverses the most recent edit that hasn't been undone. **Redo** reapplies
  the most recently undone edit.
- Every successful insert or delete **clears the redo history**. Undo and redo are
  not edits, so they don't clear it.
- A refused command changes nothing: not the text, and not either history.

## 2. Using the program

The program is used at a terminal, one command per line, on stdin and stdout. It
prints no banner and no prompt.

| Line | Command |
| --- | --- |
| `i <pos> <text>` | insert `<text>` at `<pos>` |
| `d <pos> <n>` | delete `<n>` characters at `<pos>` |
| `u` | undo |
| `r` | redo |
| `p` | print the text |
| `q` | quit |

- Fields are separated by one space. `<pos>` and `<n>` are decimal numbers.
- `<text>` is everything after the space that follows `<pos>`. It may be empty, and
  it may contain spaces: in `i 5  world` the text is ` world`, with its leading
  space. `i 5` with no second space is not a command; `i 5 ` inserts empty text.

The session ends after `q`, or at end of input. Lines after `q` are not read. The
exit status is 0 whenever input is well formed UTF-8 text.

## 3. Answers

- `p` prints the whole text on one line between two `"`, as is: a `"` in the text
  is not escaped.
- A successful insert, delete, undo, or redo prints nothing.
- A line that isn't a command, an edit §1 refuses, and an undo or redo with
  nothing to undo or redo are each answered with one line, and the session goes on.

Each version decides for itself whether to accept lines beyond the plain forms
above, such as a number with a sign or leading zeros, a non-ASCII digit, a number
too large for 32 bits, `U` for `u`, or a line ending in `\r`, and how to word a
refusal.

## 4. A sample session (the Python version)

The Python version prints this, and the C and Rust versions print the same for
these lines. They differ on some unusual lines. For example, the Rust version
reads `i +0 x` as an insert at position 0, while the Python and C versions refuse
it. And when a line ends in `\r\n` (a Windows-style line ending), the Rust version
drops the `\r`, while the Python and C versions keep it as part of the line, so an
insert puts it in the text.

```
> i 0 hello
> i 5  world
> d 0 6
> p
"world"
> u
> u
> p
"hello"
> r
> p
"hello world"
> i 11 !
> r
nothing to redo
> x
i <pos> <text> | d <pos> <n> | u | r | p | q
> p
"hello world!"
```

(`> ` marks the user's lines, which a terminal echoes; the program prints no
prompt.)

## 5. What the shared tests check

These are the only facts about the output that every version must share. The
tests send only plain lines: numbers without signs or leading zeros, and no
whitespace other than the space.
- A `p` answer is exactly `"<text>"` (§3), the text character for character.
- A successful edit, undo, or redo prints nothing.
- Every other line before `q` is answered with exactly one line.
