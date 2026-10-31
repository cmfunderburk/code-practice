# Expression Calculator — AST Eval

A line calculator for integer arithmetic. An expression is integer literals
combined with the binary operators `+ - * /`, parentheses, and unary minus, which
can be repeated (`--3` is 3). Spaces and tabs around the numbers and symbols are
ignored, and no other character counts as a space; only ASCII digits make
integers. Operators
bind and group as they do in Python: `*` and `/` before `+` and `-`, and left to
right within a level. `/` is **true division** and returns a `float`; every other
result stays an `int`. Malformed input (an empty line, input left over after a
complete expression, unbalanced parentheses, two integers next to each other, an
unknown character) raises `ValueError`. Dividing by zero raises Python's own
`ZeroDivisionError`.

## Examples

```
calculate("2+3*4")   -> 14
calculate("(2+3)*4") -> 20
calculate("7/2")     -> 3.5
calculate("2*-3")    -> -6
calculate("20-5-3")  -> 12      (left to right: (20-5)-3)
calculate("2)*3")    -> ValueError
```

Constraints: integer literals fit in Python ints. The grammar (SPEC §1 explains
how to read it) is

```
expr   := term (('+' | '-') term)*
term   := factor (('*' | '/') factor)*
factor := '-' factor | '(' expr ')' | INT
```

## AST Eval

The calculator is three separate stages, none of which reads input or prints,
plus `calculate`, which chains them:

```python
def tokenize(text: str) -> list[str]              # raises ValueError
def parse(tokens: list[str]) -> Node              # raises ValueError
def evaluate(node: Node) -> int | float
def calculate(text: str) -> int | float           # evaluate(parse(tokenize(text)))
```

`tokenize` splits the text into tokens: integers, operators, and parentheses.
`parse` turns the tokens into an *abstract syntax tree* (AST): a tree whose leaves
are numbers and whose other nodes are operations, with their operands as children.
The nodes are tagged tuples: `("num", 7)`, `("neg", node)`, and
`(op, left, right)`. `parse` is a *recursive-descent* parser: it has one helper
per grammar rule (`_expr`, `_term`, `_factor`), each taking the tokens and a
position and returning `(node, next_pos)`, and each calling the helpers for the
rules inside its own. `evaluate` computes the tree's value, matching each node's
shape with `match`/`case`. The solution must not use Python's `eval` or the `ast`
module, either of which would do the whole job in one call. The tests use `eval`
as the reference, comparing `calculate` with it on 200 random expressions, types
included.

Around the three stages sit the `Node` alias and `main()`. `main()` reads one
expression per line with `input()` until end of input or an empty line. It prints
each result as Python prints it (`print(calculate(line))`, so `7/2` shows `3.5`
and `1/3` shows `0.3333333333333333`), and prints a `ValueError` or
`ZeroDivisionError` as `error: <message>`. The full behavior is in `SPEC.md`.
