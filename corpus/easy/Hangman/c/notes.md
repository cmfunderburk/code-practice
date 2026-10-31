Python source: `python/solution.py`

- The design is the Python version's: functions that only compute, and a `main`
  that does all the input, output, and random choice. The functions take a
  `const Game *` and work out the misses, the win, and the mask each time they are
  called. `guess` takes a `Game` by value and writes the next one through `next`,
  so `main` carries one value through the loop, as Python's
  `state = guess(state, letter)` does.
- The state is a pointer to the secret plus 26 flags, one per letter. The secret
  is one of the `WORDS` string literals, which exist for the whole run and are
  never written, so every copy of a `Game` can share it. Nothing is allocated.
- `main` picks the word from `WORDS` as Python does. It seeds the C library's
  generator once with `srand(time(nullptr))` and takes
  `WORDS[(size_t)rand() % WORD_COUNT]`, the usual C way. The seed is the time in
  whole seconds, so two games started in the same second pick the same word.
  With glibc's `RAND_MAX` of 2³¹ − 1, `rand() % 8` picks each of the eight words
  equally often, because 8 divides 2³¹; with a word count that didn't divide
  `RAND_MAX + 1`, the first words would be very slightly more likely.
- `main` reads lines with `fgets` into a 64-byte buffer, and `strcspn` cuts the
  `\n` and any `\r` before it. No spaces are removed, so ` j ` is not a guess. A
  longer line arrives in pieces, each answered on its own, so a line of 63 `x`s
  and then `j` gets one reminder and then counts as a guess of `j`. `isalpha` and
  `tolower` from `<ctype.h>` work on ASCII in the C locale.
- Python contrasts and idioms: annotated in the reference above.
- O(26 · |secret|) per turn.
