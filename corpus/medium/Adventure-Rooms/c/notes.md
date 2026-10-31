Python source: `python/solution.py`

- The design is Python's: a dispatch table. `VERBS` is an array of
  `{verb, run}` pairs, standing in for Python's dictionary, and `execute` finds
  the verb and calls its handler through a function pointer.
- Rooms and items are numbers, not names: they are `enum`s, so `DESCRIPTIONS`
  and `EXITS` are arrays indexed by room, and each room's items and the inventory
  are fixed lists of item numbers. Only five items exist, so a 24-byte list of
  five slots always has room, and the whole `State` is a 152-byte struct with
  nothing on the heap.
- Handlers change the state through a pointer and print their own lines, where
  Python's handlers return `(state, output)` for `main` to print. An unknown
  verb prints `unknown verb: ...` instead of raising.
- `main` reads lines the usual C way: `fgets` into a 256-byte buffer, and
  `strcspn` to cut the `\n`. A line too long for the buffer is read to its end
  and refused once, with `That's too long to understand.` `execute` copies the
  line, trims it with `isspace` (the ASCII whitespace characters, `\r` among
  them; Python's `strip()` also removes U+00A0 and other Unicode spaces), and
  splits it at the first space with `strchr`, so the verb and the argument are
  ordinary C strings.
- Python contrasts and idioms: annotated in the reference above.
- O(n) per command for a line of n bytes; O(1) game state.
