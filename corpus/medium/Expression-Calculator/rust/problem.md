# Expression Calculator

Evaluate one arithmetic expression per stdin line, answering each with one line.
The session ends at end of input or at an empty line.

```
expr   := term (('+' | '-') term)*
term   := factor (('*' | '/') factor)*
factor := '-' factor | '(' expr ')' | INT
INT    := one or more ASCII digits
```

- Spaces and tabs around the numbers and symbols are ignored. Binary operators
  group from the left (`20-5-3` is `(20-5)-3`), and unary minus can be repeated
  (`--3` is 3).
- `+`, `-`, `*`, and negation on integers give the exact integer; `/` is true
  division (`7/2` is 3.5). How large an integer may grow, and how a non-whole
  number prints, are yours.
- A line outside the grammar, or one that divides by zero, is answered with a
  line containing `error`, and the session continues.
- A value line holds the one number it computed, in decimal or exponent
  notation.

The calculator is the program's `SPEC.md`. Wording is yours; only the
value and error lines' shape is fixed.

## A session

```text
> 2+3*4
14
> 7/2
3.5
> 1/0
error: division by zero
> 2)*3
error: trailing input
```

(`> ` marks the user's lines.)

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
#[derive(Clone, Copy, Debug, PartialEq)]
enum Value {
    Int(i64),
    Float(f64),
}

fn calculate(text: &str) -> Result<Value, String>
```

Integer arithmetic that would overflow `i64` is an `Err`, not a panic.

Differences from the Python version:
- `tokenize`, `parse`, and `evaluate` are yours to shape; only `calculate`'s
  signature is fixed.
- Integers are `i64`, not unbounded: overflow is an `Err`.
- Every stage returns `Result<_, String>` instead of raising.
- Values print with `Display`: an `f64` shows the shortest text that reads back
  as the same number, as in Python, but a whole-number float prints without `.0`
  (`8/2` shows `4`), and no float prints in exponent notation.
