# Roman Numerals — Table Render

A Roman numeral converter that works in both directions, for the numbers 1 to
3999, using the modern subtractive forms (`IV`, not `IIII`) in uppercase.
`to_roman(n)` turns a number into its numeral, and raises `ValueError` when `n` is
outside 1 to 3999. `from_roman(s)` turns a numeral back into a number, and may
assume that `s` is a valid numeral. Because the program converts both ways, you
can check `to_roman` with `from_roman`: run the program, type a number, then type
the numeral it prints, and you should get the number back.

## Examples

```
to_roman(1990) -> "MCMXC"      from_roman("MCMXC") -> 1990
to_roman(2026) -> "MMXXVI"     from_roman("MMMCMXCIX") -> 3999
to_roman(4)    -> "IV"         to_roman(0) / to_roman(4000) -> ValueError
```

Constraints: `from_roman`'s input is a valid uppercase numeral.

## Table Render

The number-to-numeral direction is a table and a walk:

```python
ROMAN_TABLE = ((1000, "M"), (900, "CM"), ...)   # descending; subtractive pairs are rows

def to_roman(n: int) -> str
```

Walk the table from the largest value down. For each row, `divmod` gives how many
times the value fits into what is left, and the remainder; append the symbol that
many times. Most of the work is getting the table's 13 rows right.

Around it sit `VALUES` (each letter's value), `from_roman`, `_canonical`, and
`main()`. `main()` reads lines with `input()` until end of input,
removing surrounding spaces and converting each line to uppercase. A line of ASCII
digits prints `to_roman` of its value, or the `out of range` error it raises. A
line of numeral letters prints its value if it is a valid numeral, which
`_canonical` checks by converting it to a number and back and comparing the result
with the line. Every refusal prints as `error: <message>`. The full behavior is in
`SPEC.md`.
