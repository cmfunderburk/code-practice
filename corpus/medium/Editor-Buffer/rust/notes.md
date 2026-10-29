Python source: `python/solution.py`

- Move: command objects, as in Python. `Edit` is an enum with `Insert` and
  `Delete` variants, each holding a position and the text it inserts or
  removed; `apply` performs one, and `invert` turns one into the other. Undo
  pops an edit, applies its inverse, and pushes the edit for redo; redo
  re-applies it.
- The buffer is `Vec<char>`, so a position is an index. SPEC counts code
  points, and a `String` is indexed by byte: every edit would first walk the
  text to turn character positions into byte offsets. `splice` inserts and
  `drain` removes in place, each O(length) like Python's slicing, without
  building a new text.
- Ownership: each `Edit` owns its characters. `delete` copies the removed
  characters out with `to_vec` before removing them, which is what makes the
  inverse exist. `invert(self)` moves the text into the new variant, so undo
  and redo never copy text. A parsed `Command::Insert` borrows its text from
  the line; it becomes owned characters only when the edit is built.
- Errors are `Result<(), String>`, and `main` prints the `Err` text, as
  Python's shell prints the `ValueError`. `ok_or` with `?` turns an empty stack
  into its message.
- The parser splits with `split_once(' ')`: one space after the verb, one after
  `<pos>`, and everything after that is the text. A second `split_once` for `d`
  leaves any third field inside `<n>`, which then fails to parse. Numbers are
  `str::parse::<usize>()`, which also takes a `+` and refuses anything past
  `usize::MAX`; `delete` compares `n` with `len - pos`, so a huge `pos + n` is
  never computed.
- The shell reads with `io::stdin().lines()`, which drops a `\r\n` whole.
- Python contrasts and idioms: annotated in the reference above.
- O(L) per edit, undo, or redo for a buffer of L characters; O(L) per `p`.
