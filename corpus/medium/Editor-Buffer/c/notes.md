Python source: `python/solution.py`

- Move: command objects, as in Python. An edit is a 40-byte `Command`, a
  `Kind` tag (`INSERT` or `DELETE`), a position, and the text it inserts or
  removed. `apply` switches on the tag, and `inverse` flips it, which is all
  Python's two `invert` methods do. A delete copies the doomed characters into
  its command before cutting them, so undo can put them back.
- The text is a growable array of `char32_t` code points, so a position indexes
  it directly. Each inserted line is decoded from UTF-8 once, and `p` encodes
  the text back. An edit moves the tail with `memmove` in place, where Python
  builds a new `str` per edit.
- The undo and redo stacks are growable arrays of commands (24 bytes each as
  structs; the `Editor` is 72 bytes). Each command owns its `chars` array and
  moves between the stacks by struct copy, so one stack holds it at a time;
  clearing the redo history frees the arrays it drops. Everything is freed at
  exit, and LeakSanitizer checks it under ASan.
- The editor functions return `false` where Python raises, and `main` writes
  the message for the verb it ran.
- `parse` finds the spaces with `memchr` and keeps pointers into the line; it
  returns the verb's letter, or 0 for a malformed line. A number is ASCII digits
  accumulated with C23's `ckd_mul` and `ckd_add`, so one too big for `size_t`
  is not a command, and the range check compares `n` with `len - pos`, so
  `pos + n` is never computed.
- Lines are read by a growable `getchar` loop, since an insert's text has no
  natural limit; a `\r` before the `\n` stays in the text, as in Python. SPEC
  leaves a number's size and a `\r` to each implementation.
- Python contrasts and idioms: annotated in the reference above.
- O(length of the text) per edit, undo, or redo, for the `memmove`; O(length)
  to print.
