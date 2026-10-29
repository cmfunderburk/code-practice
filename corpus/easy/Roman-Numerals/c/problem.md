# Roman Numerals

A two-way converter over stdin and stdout, between the integers 1 to 3999 and
their canonical Roman numerals (modern subtractive form, uppercase). Each input
line is one request, answered with exactly one line, with no prompt:

- a number from 1 to 3999: its numeral;
- a canonical numeral: its value in decimal;
- anything else (a number out of range, a string of numeral letters that is not
  canonical, junk): a refusal containing `error`.

A numeral is **canonical** when it is exactly the modern subtractive numeral of
some number from 1 to 3999: `IIII`, `IC`, and `MMMM` are not. End of input ends
the program.

The converter is the program's `SPEC.md`.
How you read a line (trimming, case, signs, leading zeros, long lines) and how you
word a refusal are yours; the numerals are not.

## A session

```text
> 1990
MCMXC
> MCMXC
1990
> IIII
error: not a number or a canonical numeral: IIII
> 4000
error: out of range (1-3999)
```

(`> ` marks the user's lines.)

## C contract

A whole program, `int main(void)`, with this core above it:

```c
constexpr size_t NUMERAL_MAX = 15;

static bool to_roman(long n, char out[static NUMERAL_MAX + 1]);
static long from_roman(const char *numeral);
static bool canonical(const char *numeral);
static bool number(const char *line, long *value);
```

`to_roman` writes the numeral and returns `true`, or returns `false` outside
1–3999. `from_roman` totals a string of the seven numeral letters by the
subtractive scan (`IIII` is 4). `canonical` is true only for numeral letters that
render back to themselves. `number` is true when the whole line reads as a
number, and stores it.

Differences from the Python version:
- `to_roman` writes into a buffer the caller owns and returns `false` where
  Python raises.
