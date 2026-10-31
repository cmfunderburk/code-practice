## How it works

`EditorBuffer` records every edit as a *command object*: an `Insert` or a `Delete`,
each a frozen dataclass holding a position and a string. A command knows how to
apply itself to a text (`apply`, which returns the new text) and how to produce
its inverse (`invert`, which returns the edit that reverses it). The inverse of
`Insert(pos, text)` is `Delete(pos, text)`, and the other way round.

The buffer keeps two lists used as stacks, `_undo` and `_redo`. `insert` and
`delete` first check that the position and count are in range, then build a
command and pass it to `_do`, the one method every edit goes through. `_do`
applies the command, pushes it on `_undo`, and clears `_redo`, so the rule "every
edit clears the redo history" is one line in one place. `undo` pops a command
from `_undo`, applies its inverse, and pushes the command on `_redo`. `redo` pops
a command from `_redo`, applies it again, and pushes it on `_undo`.

`delete` is where the design needs care. It is called with a count, but the
`Delete` it builds holds the removed text, `self._text[pos:pos + n]`, sliced before
`_do` removes it. The inverse of a delete is an insert, and an insert needs the
text; once the delete has run, the buffer no longer has it.

Worked check: insert `"hello"`, insert `" world"` at 5, delete 6 characters at 0,
leaving `"world"`. Undo inserts the saved `"hello "` back, giving
`"hello world"`; undo again removes `" world"`, giving `"hello"`; redo applies the
recorded `Insert(5, " world")` again, giving `"hello world"`.

**Complexity.** Time $O(b)$ per edit, undo, or redo for a text of $b$ characters,
since each builds a new string. Space $O(e)$ per history entry, where $e$ is the
length of that edit's own text, not of the whole buffer.

**Checking the buffer.** The tests compare `EditorBuffer` with a simpler design
that saves a copy of the whole text before every edit, over hundreds of random
edits, undos, and redos.

## `main`

`main()` reads one line at a time with `input()` and passes it to `_command`, which
returns the verb and its arguments, or `None` for a line that isn't a command.
`main` answers `None` with the `HELP` line. Otherwise it calls the matching buffer
method, with an `if`/`elif` chain over the six verbs, which is easy to read at this
size. Its one `except ValueError` catches only the buffer's own range and
empty-stack errors, and prints the message as it is. For `p` it prints the text
between two `"`. End of input ends the program quietly.

## Design choices

- **Commands, not snapshots.** Another way to get undo is to push a copy of the
  whole text before every edit and restore it on undo. Each history entry is then
  as large as the whole buffer, and it records only what the text was, not what
  the edit did. A command is as large as its own text, and it is the edit itself,
  so a list of commands can also serve as a log of what the user did, or be
  applied again to another text. In exchange, every command needs an exact
  inverse, which is why `delete` must save the text it removes. A snapshot design
  needs no inverse at all.
- **Checks before commands.** `insert` and `delete` check the range before they
  build a command, so a refused edit never reaches `_do` and leaves both stacks
  as they were. An empty insert passes the check: it changes nothing visible, but
  it is an edit, so it clears the redo history (SPEC §1).
- **Positions count characters.** Python's `str` is a sequence of Unicode code
  points, so `text[:pos]` already counts characters. Counting bytes instead would
  let `d` remove half of a character that UTF-8 spells in two bytes, such as `é`,
  and `p` would then print bytes that aren't valid UTF-8. A code point is still
  not always one visible character: `e` followed by U+0301 (a combining accent) is
  two characters that display as one `é`.
- **Reading a line exactly as SPEC writes it.** `_command` splits on single spaces
  with `partition` and `split(" ")`, so the text of `i 5  world` keeps its leading
  space. `strip()` and a bare `split()` would remove spaces and other Unicode
  whitespace from the text. `_number` accepts only ASCII digits (`isascii()`
  beside `isdigit()`), because `str.isdigit` is also true for digits in other
  scripts, such as the Arabic-Indic `٣`, and `int` reads `٣` as 3. A number may
  have any number of digits; a position past the end of the text is then refused
  as out of range.
  The one exception is a number of more than 4,300 digits: `int` raises a
  `ValueError` for it, `_command` doesn't catch it, and the program stops with a
  traceback.
- **`p` prints the text as it is.** `main` prints `f'"{buffer.text}"'`, without
  escaping anything, rather than `repr(buffer.text)`. `repr` would switch to single
  quotes or add backslashes depending on the text: `repr('say "hi"')` is
  `'say "hi"'`. Because `input()` keeps a `\r` from a `\r\n` line ending, an
  insert puts that `\r` in the text, and `p` prints it.
- **No prompt and no banner.** Successful edits print nothing, so a session's
  output is only its `p` lines and its refusals. A prompt would be mixed in with
  every one of them.

## Where this shows up again

A full-screen terminal text editor, such as antirez's *kilo* (written in under a
thousand lines of C), has a buffer like this one, and undo and redo can be added
to it with these same command objects. In such a program the buffer is one part
among many: reading keys one at a time, a view of the visible lines, search, and
saving to a file. Two decisions change:

- **How the text is stored.** This program keeps one string and rebuilds it on
  every edit, which is the simplest choice. Kilo stores an array of lines, so
  most keystrokes change only one line. Other editors use a *gap buffer* (an
  array with an empty gap at the cursor), a *piece table* (a list of spans, each
  pointing into either the original file or a buffer of added text), or a
  *rope* (a tree of short strings).
- **How positions are counted.** This program counts code points, because its
  only display is `p`. An editor that draws text on a screen must decide how
  much screen space each character takes. One simple choice is a buffer of bytes
  that shows ASCII as it is and every other byte as a placeholder, leaving out
  the width of non-ASCII characters.
