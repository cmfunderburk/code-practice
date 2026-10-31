Python source: `python/solution.py`

- Move: the table is the algorithm, as in Python. Thirteen descending
  value/symbol rows, with the subtractive pairs as rows of their own, and a
  greedy walk that subtracts each value while it fits.
- `to_roman` writes into a 16-byte buffer the caller owns (the longest numeral
  is 15 letters), and its parameter says so with `char out[static 16]`. It
  returns `false` out of range where Python raises; `answer` writes the line.
- The canonical test is Python's round trip, render the parse and compare,
  with `to_roman`'s `false` standing in for the caught `ValueError`.
- `letter_value` is a `switch` that returns 0 for a non-letter, so one function
  is both the parser's lookup and the "is it a numeral" test.
- `main` reads lines the usual C way: `fgets` into a 64-byte buffer, `strcspn`
  to cut the line ending (`\r\n` too), and `toupper` to convert to uppercase.
  `strtol` reads a number: it skips spaces before the number, accepts a sign, and
  turns a huge number into `LONG_MAX`, which is out of range like any other. No
  other spaces are removed, so ` 12` is a number but `12 ` and ` XII` are
  refused. A line too long for the buffer is read to its end and refused once.
- No heap: the line and every numeral live in fixed buffers on the stack.
- Python contrasts and idioms: annotated in the reference above.
- O(L) per line for a line of L bytes.
