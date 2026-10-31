Python source: `python/solution.py`

- The design is Python's: a dispatch table. `VERBS` is a `const` array of
  `(name, handler)` pairs, each handler a function pointer of one type,
  `fn(&mut State, &str) -> String`. `execute` finds the verb and calls its
  handler; adding a verb is a new entry, not an edit to `execute`.
- The table is fixed when the program compiles. Python's `VERBS` is a dictionary
  that `execute` reads on every call, so other code can add a verb while the
  program runs; nothing in this program adds one, so a `HashMap` would allow
  something no code uses. A `match` on the verb would put every command back
  into one function, as an `if`/`elif` chain does in Python.
- Handlers change the state through `&mut State` and return only the text.
  Python's handlers change the dict in place too, then return the same dict
  alongside the text; with `&mut`, the caller already holds the changed state,
  so there is nothing to return.
- The world is `const` data: rooms in an array, with exits and items as
  `&'static` slices, so nothing is built at startup except the item lists that
  change. Items stay `&'static str`, since every item a player can carry started
  in a room.
- `look` lists the exits by walking `DIRECTIONS` in order, as in Python, so the
  order of a room's `exits` slice doesn't matter.
- `main` reads with `io::stdin().lines()` and stops once `quit` sets `over`;
  `execute` trims with `trim()`, which removes the same characters as Python's
  `strip()` except four ASCII control characters (`\x1c` to `\x1f`).
- Python contrasts and idioms: annotated in the reference above.
- O(V + R) per command for V verbs and R rooms, all small constants.
