Python source: `python/solution.py`

- The design is the Python version's: methods that only compute, and a `main`
  that does all the input, output, and random choice. `Game` is never changed in
  place: `guess` borrows it, clones it, and returns the next game in `Ok`, so
  `main` assigns `game = next` as Python assigns `state`.
- `status()` returns an enum with three variants, computed each time it is called,
  where Python returns a string.
- The word is picked with `WORDS.choose(&mut rand::rng())`. Rust's standard
  library has no random numbers, and `rand` is the crate Rust programmers usually
  use: its thread-local generator is seeded from the operating system, like
  Python's `random`. `choose` returns `Option` because the slice could be empty,
  so `main` unwraps it with `expect`, whose message says why it can't be.
- `io::stdin().lines()` yields `io::Result<String>`, without the newline. A line
  that isn't UTF-8 is an `Err`, and `main` quits there, as it does at end of
  input. `letter_of` removes surrounding spaces with `trim()`, as Python's
  `strip()` does, and accepts one ASCII letter.
- Python contrasts and idioms: annotated in the reference above.
- O(26 · |secret|) per turn, plus a clone of at most 26 guesses per guess.
