Python source: `python/solution.py`

- Move: functional core / imperative shell, as in Python. `Game` is never
  changed in place: `guess` borrows it, clones it, and returns the next game in
  `Ok`, so `main` rebinds `game = next` as Python rebinds `state`.
- Status is an enum with three variants, derived on demand by `status()`, where
  Python returns a string.
- The word is picked with `WORDS.choose(&mut rand::rng())`. Rust's standard
  library has no random numbers, and `rand` is the crate everyone reaches for:
  its thread-local generator is seeded from the operating system, like Python's
  `random`. `choose` returns `Option` because the slice could be empty, so the
  shell unwraps it with `expect` naming why it can't be.
- `io::stdin().lines()` yields `io::Result<String>`, without the newline. A line
  that isn't UTF-8 is an `Err`, and the shell quits there, as it does at end of
  input. `letter_of` trims the line, as Python's `strip()` does, and accepts one
  ASCII letter.
- Python contrasts and idioms: annotated in the reference above.
- O(26 · |secret|) per turn, plus a clone of at most 26 guesses per guess.
