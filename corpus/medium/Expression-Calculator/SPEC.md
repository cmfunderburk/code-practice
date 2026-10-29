# Expression Calculator — SPEC

The calculator every implementation builds, in any language. The Python version
(`python/problem.md`) adds the API and its design. Each implementation is its
language's natural program for this calculator: how big its numbers get, how it
prints a fraction, and how it words an error are its own. All of them keep the
fixed output of §4.

## 1. Expressions

```
expr   := term (('+' | '-') term)*
term   := factor (('*' | '/') factor)*
factor := '-' factor | '(' expr ')' | INT
INT    := one or more ASCII digits (leading zeros allowed)
```

Spaces and tabs between tokens are ignored. Binary operators are
left-associative, and unary minus nests (`--3` is 3).

**Values.** `+`, `-`, `*`, and unary minus on integers give the exact integer.
`/` is true division: `7/2` is 3.5, not 3. Once a value is a fraction, the
arithmetic on it is the language's floating point. Dividing by zero is an error.

How large an integer may grow is the implementation's choice: Python's are unbounded,
and a port may use a fixed-width type and report overflow as an error.

## 2. Playing

The program is used at a terminal, one expression per line, on stdin and stdout.
- Each expression line is answered with one line: its value, or an error.
- An error is a line that isn't in the grammar (an unknown character, trailing
  input, unbalanced parentheses, adjacent integers, nothing but spaces) or that
  divides by zero. It is reported and the session continues.
- An empty line or end of input ends the session.

The exit status is 0 whenever input is well formed UTF-8 text.

## 3. A session (one implementation)

The Python version's shell prints this; other implementations may word it, and print
fractions, their own way.

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

## 4. Fixed output

These are the only output facts every implementation keeps fixed:
- Each expression line produces exactly one line of output.
- A value line contains one number, the value, written in decimal or exponent
  notation (`3.5`, `-6`, `1e+20`), and no other digits. Its value must agree with
  the expression's to nine significant digits.
- An error line contains the word `error` (any case). A value line does not.
