# Roman Numerals — SPEC

This document specifies a program that converts between numbers and Roman
numerals. There are three versions of it, in Python, C, and Rust, and each is
written the way a programmer in that language would usually write it. All three
must agree on the numerals themselves (§1). They may differ in how they read a
line (whether they ignore surrounding spaces, accept lowercase letters, or accept
a sign or leading zeros) and in how they word an error message.

The Python version's API is in `python/problem.md`. Each version has its own tests,
and all three also run the shared tests in `test_program.py`, which check only
the facts in §4.

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

## 2. Using the program

The program is used at a terminal, one request per line, on stdin and stdout. It
prints no banner and no prompt.
- A number from 1 to 3999 is answered with its numeral.
- A canonical numeral is answered with its value in decimal.
- Anything else is refused with one line, and the program goes on to the next:
  a number outside 1–3999, a string of numeral letters that is not canonical, or
  a line that is neither a number nor a numeral.
- End of input ends the program.

A line of plain ASCII digits is always read as a number, and a line of plain
uppercase letters as a possible numeral. Each version decides for itself how to
read other lines, such as `0042`, ` 12 ` (with spaces), `+7`, `mcmxc`, or `XLII`
followed by a carriage return. The program exits with status 0 whenever its input
is well-formed UTF-8 text.

## 3. A sample session (the Python version)

The Python version prints this. The C and Rust versions word their error messages
differently, and read some other lines differently. For example, the Python and
Rust versions ignore spaces around any line, while the C version accepts them only
before a number.

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

## 4. What the shared tests check

These are the only facts about the output that every version must share. The
tests send only plain lines: ASCII digits without leading zeros, uppercase
letters, and junk that no version would read as a number or a numeral.
- Each line is answered with exactly one line.
- A numeral answer contains the numeral exactly (§1), and no other word made only
  of the letters `IVXLCDM`.
- A value answer contains the value as its only number.
- A refusal contains the word `error` (in any case); no other answer does.
