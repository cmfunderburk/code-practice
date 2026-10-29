# Roman Numerals — Table Render

A both-ways Roman numeral converter, domain **1..3999**, canonical modern
subtractive forms, uppercase. `to_roman(n)` renders an int as a numeral and
raises `ValueError` outside the domain; `from_roman(s)` parses a canonical
numeral back to an int (it may assume canonical input). Both directions
live in one program, and each doubles as a round-trip oracle for the other.

## Examples

```
to_roman(1990) -> "MCMXC"      from_roman("MCMXC") -> 1990
to_roman(2026) -> "MMXXVI"     from_roman("MMMCMXCIX") -> 3999
to_roman(4)    -> "IV"         to_roman(0) / to_roman(4000) -> ValueError
```

Constraints: `from_roman` input is a canonical uppercase numeral.

## Table Render

The render direction is a table and a walk:

```python
ROMAN_TABLE = ((1000, "M"), (900, "CM"), ...)   # descending; subtractive pairs are rows

def to_roman(n: int) -> str
```

Walk the descending table, `divmod` off each value, append
`symbol * count`. Getting the 13 rows right IS the drill.

The surrounding program is `VALUES`, `from_roman` (the subtractive scan),
`_canonical`, and the both-ways `main()` shell. `main()` reads lines with
`input()` until end of input, trimming each and folding it to uppercase. ASCII
digits print `to_roman` of their value, or its `out of range` error. Numeral
letters print their value when the numeral is canonical, which `_canonical`
checks by rendering the parse back and comparing. Every refusal prints as
`error: <message>`. The converter itself is `SPEC.md`.
