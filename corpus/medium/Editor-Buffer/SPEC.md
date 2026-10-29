# Editor Buffer — SPEC

The editor every implementation builds, in any language. The Python version
(`python/problem.md`) adds the API and the design. Each implementation is its
language's natural program: how it words a refusal, how large a number it reads,
and how it treats a `\r` or a non-ASCII digit are its own. The **buffer** (§1) is
not: its text, counted in characters, and what `p` shows of it are the program's
data, the same in every implementation. §5 fixes the few output facts all of them
share.

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

## 2. Playing

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

Which lines are commands beyond the plain forms above (a sign, leading zeros, a
non-ASCII digit, a number past 32 bits, `U` for `u`, a trailing `\r`), and how a
refusal is worded, is the implementation's choice.

## 4. A session (one implementation)

The Python version's shell prints this; other implementations may word their
refusals their own way.

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

## 5. Fixed output

These are the only output facts every implementation keeps fixed, for plain
lines: numbers without signs or leading zeros, and nothing but spaces for
whitespace. All other wording is each implementation's own.
- A `p` answer is exactly `"<text>"` (§3), the text character for character.
- A successful edit, undo, or redo prints nothing.
- Every other line before `q` is answered with exactly one line.
