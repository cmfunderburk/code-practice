# Roman Numerals — SPEC

The converter every version implements, in any language. The Python version
(`python/problem.md`) adds the API. Each implementation is its language's natural
program: how it reads a line (whether it trims spaces, folds case, or accepts a
sign or leading zeros) and how it words a refusal are its own. The **numerals**
(§1) are not: they are the program's data, the same in every implementation.
Beyond them, only the output facts in §4 are fixed.

## 1. Numerals

The program converts both ways between the integers **1 to 3999** and their
**canonical** Roman numerals: modern subtractive form, uppercase.

A number is written place by place, thousands first. Each decimal digit becomes:

| Digit | Ones | Tens | Hundreds | Thousands |
| --- | --- | --- | --- | --- |
| 1 | `I` | `X` | `C` | `M` |
| 2 | `II` | `XX` | `CC` | `MM` |
| 3 | `III` | `XXX` | `CCC` | `MMM` |
| 4 | `IV` | `XL` | `CD` | |
| 5 | `V` | `L` | `D` | |
| 6 | `VI` | `LX` | `DC` | |
| 7 | `VII` | `LXX` | `DCC` | |
| 8 | `VIII` | `LXXX` | `DCCC` | |
| 9 | `IX` | `XC` | `CM` | |

A zero digit writes nothing. So 1990 is `M` + `CM` + `XC` = `MCMXC`, and 2026 is
`MMXXVI`.

A string of the letters `IVXLCDM` is **canonical** when it is exactly the numeral
of some number from 1 to 3999. `IIII`, `IC`, `VX`, `XM`, and `MMMM` are made of
numeral letters but are not canonical. There are exactly 3999 canonical numerals,
and the longest, `MMMDCCCLXXXVIII` (3888), has 15 letters.

## 2. Playing

The program is used at a terminal, one request per line, on stdin and stdout. It
prints no banner and no prompt.
- A number from 1 to 3999 is answered with its numeral.
- A canonical numeral is answered with its value in decimal.
- Anything else is refused with one line, and the program goes on to the next:
  a number outside 1–3999, a string of numeral letters that is not canonical, or
  a line that is neither a number nor a numeral.
- End of input ends the program.

Which lines count as a number or a numeral beyond plain ASCII digits and plain
uppercase letters (`0042`, ` 12 `, `+7`, `mcmxc`, `XLII\r`) is each
implementation's choice. The exit status is 0 whenever input is well formed UTF-8
text.

## 3. A session (one implementation)

The Python version's shell prints this; other implementations may word their
refusals, and read their lines, their own way.

```
> 1990
MCMXC
> MCMXC
1990
> IIII
error: not a canonical numeral: IIII
> 0042
XLII
> 4000
error: out of range: 4000
> mcmxc
1990
> hello
error: enter a number 1-3999 or a Roman numeral
```

(`> ` marks the user's lines, which a terminal echoes; the program prints no
prompt.)

## 4. Fixed output

These are the only output facts every implementation keeps fixed; all other
wording is each implementation's own. They hold for plain lines: ASCII digits
without leading zeros, uppercase letters, and junk no implementation would read
as either.
- Each line is answered with exactly one line.
- A numeral answer holds the numeral exactly (§1), and no other word made only of
  the letters `IVXLCDM`.
- A value answer holds the value as its one number.
- A refusal contains the word `error` (any case); no other answer does.
