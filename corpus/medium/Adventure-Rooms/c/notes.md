Python source: `python/solution.py`

- Move: a dispatch table, as in Python. `VERBS` is an array of
  `{verb, handler}` pairs, Python's dict, and `execute` looks the verb up and
  calls the handler through a function pointer.
- The world is numbers, not names: rooms and items are `enum`s, so
  `DESCRIPTIONS` and `EXITS` are arrays indexed by room, and each room's items
  and the inventory are fixed lists of item numbers. Only five items exist, so
  a 24-byte list of five slots always suffices, and the whole `State` is a
  152-byte struct with no heap.
- Handlers change the state through a pointer and print their own lines, where
  Python's return `(state, output)` for `main` to print; an unknown verb prints
  its message instead of raising.
- The shell is C's usual line reader: `fgets` into a 256-byte buffer, a line
  too long for it drained and refused once, and `strcspn` to cut the `\n`.
  `execute` copies the line, trims it with `isspace` (the ASCII whitespace;
  Python also strips U+00A0 and its kin), and splits it at the first space with
  `strchr`, so verbs and arguments are ordinary C strings.
- Python contrasts and idioms: annotated in the reference above.
- O(n) per command for a line of n bytes; O(1) game state.
