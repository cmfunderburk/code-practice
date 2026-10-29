Python source: `python/solution.py`

- Move: functional core / imperative shell, as in Python. The core is a set of
  functions over a `const Game *` that derive the misses, the win, and the mask
  on demand. `guess` takes a `Game` by value and writes the next one, so `main`
  threads a value through the loop as Python's `state = guess(state, letter)` does.
- The state is a pointer to the secret plus 26 flags. The secret is one of the
  `WORDS` string literals, which live for the whole run and are never written,
  so every copy of a `Game` can share it. Nothing is allocated.
- The word is picked from `WORDS` as in Python. `main` seeds the C library
  generator once with `srand(time(nullptr))` and indexes `WORDS[(size_t)rand() %
  WORD_COUNT]`, the ordinary C idiom; the modulo's slight bias toward the first
  words is harmless for a game.
- Lines are read with `fgets` into a 64-byte buffer, and `strcspn` cuts the
  `\r\n`. A longer line arrives in pieces, and each piece is answered as not one
  letter. `isalpha` and `tolower` from `<ctype.h>` work on ASCII in the C locale.
- Python contrasts and idioms: annotated in the reference above.
- O(26 · |secret|) per turn.
