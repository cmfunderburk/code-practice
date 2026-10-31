# Expression Calculator — SPEC

This document specifies a calculator that reads arithmetic expressions such as
`2+3*4` and prints their values. There are three versions of it, in Python, C, and
Rust, and each is written the way a programmer in that language would usually
write it. All three must agree on which lines are expressions and what they are
worth (§1). They may differ in how large an integer may grow, in how they print a
number that is not whole, and in how they word an error message.

The Python version's API is in `python/problem.md`. Each version has its own tests, and
all three also run the shared tests in `test_program.py`, which check only the
facts in §4.

## 1. Expressions

An expression is built from integers, the binary operators `+ - * /`, unary minus,
and parentheses. This grammar says exactly which lines are expressions:

```
expr   := term (('+' | '-') term)*
term   := factor (('*' | '/') factor)*
factor := '-' factor | '(' expr ')' | INT
INT    := one or more ASCII digits (leading zeros allowed)
```

Read `:=` as "is", `|` as "or", and `( ... )*` as "zero or more times". So an
`expr` is one or more `term`s joined by `+` or `-`, a `term` is one or more
`factor`s joined by `*` or `/`, and a `factor` is a minus sign before another
factor, an `expr` in parentheses, or an integer. The pieces a line is split into
before this grammar is applied (integers, operators, and parentheses) are its
*tokens*. Spaces and tabs around tokens are ignored; no other character counts as
a space.

Because `*` and `/` appear one level below `+` and `-`, they are applied first:
`2+3*4` is 14. This is called *precedence*. A run of operators at the same level is
applied from left to right: `20-5-3` is `(20-5)-3`, which is 12. This is called
*left associativity*. Unary minus can be repeated (`--3` is 3) and can follow
another operator (`2*-3` is -6).

**Values.** `+`, `-`, `*`, and unary minus on integers give the exact integer.
`/` is true division and always gives a floating-point number: `7/2` is 3.5, not
3, and `8/2` is the floating-point number 4. Any arithmetic with a floating-point
operand uses the language's floating-point numbers. Dividing by zero is an error.

How large an integer may grow is up to each version. Python's integers have no
size limit; the C and Rust versions use 64-bit integers and report an integer too
large for 64 bits as an error.

## 2. Using the program

The program is used at a terminal, one expression per line, on stdin and stdout.
It prints no banner and no prompt.
- Each expression line is answered with one line: its value, or an error.
- A line is an error if it isn't in the grammar (an unknown character, input left
  over after a complete expression, unbalanced parentheses, two integers next to
  each other, nothing but spaces) or if it divides by zero. The program prints the
  error and goes on to the next line.
- An empty line or end of input ends the program.

The program exits with status 0 whenever its input is well-formed UTF-8 text.

## 3. A sample session (the Python version)

The Python version prints this. The C and Rust versions word their error messages
differently and print some numbers differently: the C version prints `1/3` as
`0.333333333333333`, and both print `8/2` as `4` where Python prints `4.0`.

```
> 2+3*4
14
> 7/2
3.5
> 1/3
0.3333333333333333
> 1/0
error: division by zero
> 2)*3
error: trailing input: )
```

(`> ` marks the user's lines, which a terminal echoes; the program prints no
prompt.)

## 4. What the shared tests check

These are the only facts about the output that every version must share:
- Each expression line is answered with exactly one line.
- A value line contains one number, the value, written in decimal or exponent
  notation (`3.5`, `-6`, `1e+20`), and no other digits. The number must agree
  with the expression's value to nine significant digits.
- An error line contains the word `error` (in any case). A value line does not.
