Python source: `python/solution.py`

- Move: the table render, as in Python. `TABLE` is a `const` array of the 13
  `(value, symbol)` rows, subtractive pairs included, in descending order;
  `to_roman` walks it, appending `symbol.repeat(count)` and keeping the
  remainder. Getting the rows right is the drill.
- Canonical means "renders back to itself": `canonical` parses with the
  subtractive scan and compares `to_roman` of the result with the line, as
  Python's shell does. The scan is a total for any string of numeral letters,
  canonical or not, so no separate grammar check is needed.
- One integer type, `i64`, runs through the program. The scan's total must be
  signed, since a subtraction can come first (`IV` starts at −1), and keeping
  `to_roman` on `i64` too means the round trip needs no conversion.
- Out of range is `None` from `to_roman`, and `answer` words the refusal.
  Python raises `ValueError` and the shell prints it.
- The shell reads with `io::stdin().lines()`, trims with `trim()`, folds with
  `to_ascii_uppercase()`, and reads a number with `parse::<i64>()`, which takes
  a sign: `+12` is `XII` and `-1` is out of range.
- Python contrasts and idioms: annotated in the reference above.
- O(L) per line for a line of L bytes.
