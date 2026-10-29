# Expression Calculator — AST Eval

A line calculator for integer arithmetic. Expressions are integer literals
combined with binary `+ - * /`, parentheses, and unary minus (which nests:
`--3` is legal); spaces and tabs between tokens are ignored. Only ASCII digits make
integers, and no other character counts as whitespace. Precedence and
associativity match Python exactly, and `/` is **true division** — it
returns a `float`; every other result stays `int`. Malformed input (empty
text, trailing junk, unbalanced parentheses, adjacent integers, unknown
characters) raises `ValueError`; dividing by zero propagates Python's own
`ZeroDivisionError`.

## Examples

```
calculate("2+3*4")   -> 14
calculate("(2+3)*4") -> 20
calculate("7/2")     -> 3.5
calculate("2*-3")    -> -6
calculate("20-5-3")  -> 12      (left-associative)
calculate("2)*3")    -> ValueError
```

Constraints: integer literals fit in Python ints; the grammar is

```
expr   := term (('+' | '-') term)*
term   := factor (('*' | '/') factor)*
factor := '-' factor | '(' expr ')' | INT
```

## AST Eval

Implement the three stages as separate pure functions:

```python
def tokenize(text: str) -> list[str]              # raises ValueError
def parse(tokens: list[str]) -> Node              # raises ValueError
def evaluate(node: Node) -> int | float
def calculate(text: str) -> int | float           # evaluate(parse(tokenize(text)))
```

`parse` is a recursive-descent parser with one helper per grammar level
(`_expr`, `_term`, `_factor`, each `(tokens, pos) -> (node, next_pos)`)
building the tagged-tuple AST — `("num", 7)`, `("neg", node)`,
`(op, left, right)` — and `evaluate` reads the shapes back off with
`match`/`case`. Python's `eval` (and the `ast` module) is **banned** in the
solution: it is the program this program displaces.

Around the three stages sit the `Node` alias and the `main()` shell. The shell
reads one expression per line with `input()` until end of input or an empty
line. It prints each result as Python prints it (`print(calculate(line))`, so
`7/2` shows `3.5` and `1/3` shows `0.3333333333333333`) and reports `ValueError`
and `ZeroDivisionError` as `error: <message>`. The calculator itself is
`SPEC.md`.
