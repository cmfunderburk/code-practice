## How it works

The program converts in both directions between numbers, which it computes with,
and numerals, which the user reads and types. `to_roman` is the *renderer*, from
number to text, and `from_roman` is the *parser*, from text to number.

`to_roman` uses one table of value and symbol pairs in descending order, in which
the subtractive pairs (`CM`, `CD`, `XC`, `XL`, `IX`, `IV`) are rows of their own
beside the single letters. It walks the table from the top. For each row, `divmod`
gives how many times the value fits into what is left, and `to_roman` appends the
symbol that many times. Everything `to_roman` knows about Roman numerals is in the
table's 13 rows; the loop is three lines.

Worked check: 1990 → `M` (990 left) → `CM` (90 left) → `XC` (0 left) →
`"MCMXC"`.

**Complexity.** Time $O(1)$: 13 table rows and at most 15 output symbols. Space
$O(1)$.

**Checking `to_roman`.** Because the program converts both ways, you can check
`to_roman` by hand: run the program, type a number, then type the numeral it
prints, and `from_roman` should give the number back. The tests check
every number from 1 to 3999 in both directions against a different method, one
lookup table per decimal place, which is how SPEC §1 writes numerals.

## `main`

`main()` reads one line at a time with `input()`. It removes surrounding spaces and
converts the line to uppercase, since a person who types ` mcmxc ` at a terminal
means `MCMXC`. A line of ASCII digits goes to `to_roman`, and if `to_roman` raises
`out of range`, `main` prints that error. A line of numeral letters goes to
`from_roman`, but `main` prints the value only after `_canonical` confirms that the
numeral is valid. Every refusal is one line, `error: <message>`.

## Design choices

- **A table, not a rule.** The six subtractive pairs could be handled by a rule
  instead of rows, as `from_roman` does: it subtracts a symbol's value whenever the
  next symbol is larger. The rule is shorter to state, but it never says which
  pairs are allowed, so `from_roman` reads `IM` as 999. The table lists exactly the
  allowed pairs, so `to_roman` can't write an invalid numeral.
- **Checking a numeral with the round trip.** `from_roman` accepts any string of
  numeral letters: `IIII` is 4, `IM` is 999, `MMMM` is 4000. `_canonical` checks a
  numeral by converting it to a number and back, and comparing the result with the
  original. Because `to_roman` writes only valid numerals, this check uses the
  table's definition of a valid numeral. A regular expression for valid numerals
  would be a second definition, which someone would have to keep in step with the
  table by hand. A run of fifteen `M`s parses to 15000, which has no numeral, so
  `_canonical` also catches `to_roman`'s `ValueError` and returns `False`.
- **Checking every line before trusting it.** Removing spaces and changing case
  are conveniences; the checks after them are what keep the program correct. An
  empty line is refused, since `from_roman("")` would return 0. A number must be
  ASCII digits (`isascii()` beside `isdigit()`), because `str.isdigit` is also true
  for digits in other scripts, such as Arabic-Indic `٤٢`, and `int` reads those as
  42. A line containing a letter outside `VALUES` is refused before `from_roman`
  can raise `KeyError`, and `to_roman`'s `ValueError` is caught and printed, so no
  input ends the program with a traceback. A number may be any length: Python's
  `int` takes any size, and anything past 3999 is out of range.
- **Every refusal contains `error`.** The shared tests read only that word from a
  refusal, so the C and Rust versions can word their messages their own way. The
  numerals must be the same in every version.

## Where this shows up again

Any program that both writes and reads the same text format has a renderer and a
parser that must agree. Two larger examples:

- A Lisp interpreter has a *reader*, which turns source text into integers,
  booleans, strings, symbols, and nested lists, and a *printer*, which turns those
  values back into text, as `from_roman` and `to_roman` do here. A careful printer
  writes strings with the same backslash escapes its reader understands, so
  printed data reads back as the same data.
- A key-value store can write every change to a log file in the same format it
  uses on the network, and rebuild its data at startup by parsing that log (Redis
  does this with its RESP protocol). A renderer and parser that disagreed there
  would lose stored data, where here they would only refuse a line or print a wrong
  answer.
