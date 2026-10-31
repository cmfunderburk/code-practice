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

## C contract

A whole program, `int main(void)`, with this core above it:

```c
typedef struct {
    bool is_float;
    union {
        int64_t integer;
        double real;
    };
} Value;

static bool calculate(const char *text, size_t len, Value *result, const char **error);
```

`calculate` writes the value through `result` and returns `true`, or points
`*error` at a message and returns `false`. Integer arithmetic that would
overflow `int64_t` is an error, not undefined behavior.

Differences from the Python version:
- `tokenize`, `parse`, and `evaluate` are yours to shape; only `calculate`'s
  signature is fixed.
- Integers are `int64_t`, not unbounded: overflow is reported as an error.
- Floats print with `printf("%.15g")`, not as Python's shortest text that reads
  back as the same number: `1/3` prints `0.333333333333333`.
