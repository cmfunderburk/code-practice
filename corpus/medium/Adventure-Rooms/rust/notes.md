Python source: `python/solution.py`

- Move: the dispatch table, as in Python. `VERBS` is a `const` array of
  `(name, handler)` pairs, each handler a function pointer of one type,
  `fn(&mut State, &str) -> String`. `execute` finds the verb and calls its
  handler; adding a verb is a new entry, not an edit to `execute`.
- The table is fixed when the program compiles. Python's `VERBS` is a dict that
  `execute` reads at call time, so a caller can register a new verb; nothing in
  this program registers one, so a `HashMap` would buy only that. A `match` on
  the verb would be an if/elif ladder's shape again.
- Handlers mutate the state through `&mut State` and return only the text.
  Python's handlers mutate in place too, then return the same dict alongside the
  text, which Rust's borrow makes unnecessary.
- The world is `const` data: rooms in an array, with exits and items as
  `&'static` slices, so nothing is built at startup except the item lists that
  change. Items stay `&'static str`, since every item a player can carry started
  in a room.
- The exits are listed by walking `DIRECTIONS` in order, as in Python, so the
  data's own order doesn't matter.
- The shell reads with `io::stdin().lines()` and breaks once `quit` sets
  `over`; `execute` trims with `trim()`, which removes Unicode whitespace much as
  Python's `strip()` does.
- Python contrasts and idioms: annotated in the reference above.
- O(V + R) per command for V verbs and R rooms, all small constants.
