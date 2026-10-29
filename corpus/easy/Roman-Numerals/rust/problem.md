# Roman Numerals

Convert both ways between the integers 1 to 3999 and their canonical Roman
numerals (modern subtractive form, uppercase), one request per stdin line.

- A number is written place by place, thousands first: each digit becomes its
  place's letters (`IV`, `IX`, `XL`, `XC`, `CD`, `CM` for the 4s and 9s), and a
  zero digit writes nothing. So 1990 is `MCMXC`. A string of `IVXLCDM` letters is
  **canonical** when it is exactly the numeral of some number from 1 to 3999:
  `IIII`, `IC`, and `MMMM` are not.
- Each line is answered with exactly one line: a number from 1 to 3999 with its
  numeral, a canonical numeral with its value, and anything else (a number out of
  range, a non-canonical numeral, junk) with a refusal containing `error`.
- No prompt and no banner; end of input ends the program.

The converter is the program's `SPEC.md`.
How you read a line (trimming, case, signs, leading zeros) and how you word a
refusal are yours; the numerals are not.

## A session

```text
> 1990
MCMXC
> MCMXC
1990
> IIII
error: "IIII" is not a number 1-3999 or a canonical numeral
> 4000
error: 4000 is not in 1-3999
```

(`> ` marks the user's lines.)

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
fn to_roman(n: i64) -> Option<String>
fn from_roman(numeral: &str) -> Option<i64>
fn canonical(numeral: &str) -> Option<i64>
fn answer(line: &str) -> String
```

`to_roman` is `None` outside 1–3999. `from_roman` totals any string of the seven
numeral letters by the subtractive scan (`IIII` is 4) and is `None` for any other
letter; `canonical` is the value only when `to_roman` of it gives the numeral
back. `answer` is the line to print for one input line.

Differences from the Python version:
- `to_roman` returns `Option` where Python raises, and every number is `i64`.
