# Expression Calculator — oral defense

Seven questions about the design of the expression calculator, for practising
explaining it aloud. Answer each question with its answer closed, then open the
answer to check yourself. Each answer starts with the main point and names the file
that settles it: `SPEC.md`, `python/solution.py`, or `python/notes.md`.

Question 7 compares the Python version with the C and Rust versions, which are in
`c/` and `rust/`.

> [!note]- Examiner prompt
> Paste this into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached (for question 7, attach the C and Rust
> `solution` files too):
>
> *You are examining a student on a small calculator program, specified in SPEC.md
> and implemented in solution.py. Ask the questions from DEFENSE.md one at a time,
> in order. After each answer, ask follow-up questions about anything vague: ask
> for the specific function, grammar rule, input, or line of SPEC. Don't accept
> "it's more extensible" without the student naming what could be added and where
> it would go. Keep a list of claims that contradict SPEC.md or the code, and read
> it back at the end. Don't show the answers unless the student gives up.*

## Following a line through the program

### 1. Trace `2*-3` through the program

The user types `2*-3`. `calculate` passes it through three stages: `tokenize`
splits it into tokens, `parse` builds a tree from the tokens with its helpers
`_expr`, `_term`, and `_factor`, and `evaluate` computes the tree's value.

Say what each stage returns for this line, and what `main` prints. Which helper
reads the minus sign, and which rule of the grammar in SPEC §1 allows a minus sign
straight after `*`?

> [!answer]-
> **`_factor` reads the minus sign, under the rule `factor := '-' factor`.**
> 1. `input()` returns `2*-3`, and `main` passes it to `calculate`.
> 2. `tokenize` returns `["2", "*", "-", "3"]`.
> 3. `parse` calls `_expr`, which calls `_term`, which calls `_factor`; that reads
>    `2` and returns `("num", 2)`. Back in `_term`, the next token is `*`, so
>    `_term` calls `_factor` for the right operand. This `_factor` sees `-`, calls
>    itself to read `3`, and returns `("neg", ("num", 3))`. The tree is
>    `("*", ("num", 2), ("neg", ("num", 3)))`.
> 4. `evaluate` computes 2 × −3 and returns the integer `-6`, and `main` prints
>    `-6`.
>
> The right operand of `*` is a `factor`, and a `factor` may be a minus sign
> followed by another `factor`, so a minus sign is allowed wherever an operand is.
> Only `main` reads input or prints; the three stages just return values.
> (`python/solution.py`; SPEC §1.)

## Design choices

### 2. Why build a tree at all?

A shorter calculator computes while it parses. Its helpers return numbers instead
of tree nodes. Its `_term`, for example, would be:

```python
def _term(tokens, pos):
    value, pos = _factor(tokens, pos)
    while pos < len(tokens) and tokens[pos] in "*/":
        op = tokens[pos]
        right, pos = _factor(tokens, pos + 1)
        value = value * right if op == "*" else value / right
    return value, pos
```

This version gives the same answers on valid lines and allocates no tree. Name two
things the tree version can do that it can't: one about testing, and one about
what each version prints for the line `1/0+(2`. Then say what extra memory and
work the tree version needs.

> [!answer]-
> **With a tree, reading the line and computing its value are separate steps, so
> each can be checked, or reused, on its own.**
> - **Testing.** `parse` returns a tree, so a test can check the exact structure
>   without computing anything: `test_parse_builds_the_tuple_ast` checks that
>   `2+3*4` parses to `("+", ("num", 2), ("*", ("num", 3), ("num", 4)))`, and
>   `test_evaluate_hand_built_nodes` calls `evaluate` on a tree built by hand. The
>   other version can only be tested by its final numbers. The same separation
>   means another function could take the tree (to print it, simplify it, or
>   compile it) without any change to the parser.
> - **`1/0+(2`.** The tree version parses the whole line before evaluating any of
>   it. The parenthesis is never closed, so `parse` raises, and the program prints
>   `error: expected )`. The other version divides as soon as `_term` has read
>   `1/0`, so it prints `error: division by zero` and never notices the missing
>   parenthesis. Here the difference is only which error is reported, because
>   arithmetic changes nothing outside the calculator. In a language with
>   variables or output, computing before the whole line is read would run part of
>   a broken program.
>
> The tree version needs one tuple per node, which is memory proportional to the
> line's length, and a second recursive pass in `evaluate`, whose depth question
> 5 explores. (`python/notes.md` §Design choices.)

### 3. How the grammar sets precedence and grouping

SPEC §1 defines two terms. *Precedence* is which operator applies first: in
`2+3*4`, the `*` does, so the value is 14, not 20. *Left associativity* is how a
run of operators at the same level groups: `20-5-3` is `(20-5)-3`, which is 12,
not `20-(5-3)`, which is 18.

Point to the part of the grammar, and the lines in `_expr` and `_term`, that give
each of these results. Then suppose `_expr` were written to follow the rule
`expr := term ('-' expr)?` instead (`?` means "optional"), calling itself for
everything to the right of a `-`. What would `20-5-3` give, and why?

> [!answer]-
> **Precedence comes from the levels of the grammar, and left associativity from
> the loops in `_expr` and `_term`.**
> - **Precedence.** An `expr` is made of `term`s, and a `term` of `factor`s, so
>   `*` and `/` are one level below `+` and `-`. In `2+3*4`, `_expr` gets each
>   operand from `_term`, and the second `_term` call reads all of `3*4` before
>   returning. So `3*4` becomes one node, which is the right operand of `+`.
> - **Left associativity.** `_expr` reads one term, then loops: each `+` or `-`
>   reads the next term and sets `node = (op, node, right)`, so the tree built so
>   far becomes the left operand. `20-5-3` becomes
>   `("-", ("-", ("num", 20), ("num", 5)), ("num", 3))`, which is 12. `_term`'s loop
>   does the same for `*` and `/`, so `100/5/2` is `(100/5)/2`, which is 10.0.
>
> The rule `expr := term ('-' expr)?` makes everything after the first `-` one
> `expr`, so `20-5-3` would group as `20-(5-3)` and give 18. Writing a loop where
> the grammar has `( ... )*` is what keeps the grouping to the left.
> (SPEC §1; `_expr` and `_term` in `python/solution.py`.)

### 4. Who turns an exception into an error line?

`calculate("1/0")` raises `ZeroDivisionError`, and `calculate("2)*3")` raises
`ValueError`. Yet when the user types either line, the program prints one line
starting with `error:` and then reads the next line.

Which function turns each exception into an output line? Why doesn't `calculate`
return the text `"error: division by zero"` itself? And what would the program do
with `1/0` if `main` caught only `ValueError`?

> [!answer]-
> **`calculate` reports a failure by raising, and `main` decides what the user
> sees.** `main` wraps `print(calculate(line))` in `try` and catches both
> `ValueError` and `ZeroDivisionError`, printing `error: <message>`. Then its loop
> goes on to the next line.
>
> If `calculate` returned error text, its result could be a number or a string,
> and every caller would have to check which before using it. A caller that
> forgot would treat `"error: division by zero"` as a value. Raising keeps the
> return type `int | float`, and lets the tests check failures directly
> (`test_malformed_raises` and `test_zero_division_propagates`). It also leaves the
> wording and the `error:` prefix to `main`, the only function that talks to the
> user.
>
> If `main` caught only `ValueError`, the `ZeroDivisionError` from `1/0` would pass
> out of `main`, and the program would stop with a traceback and exit status 1.
> SPEC §2 requires a division by zero to be reported and the session to continue.
> (`main` in `python/solution.py`; SPEC §2.)

## Unusual input

### 5. Three lines that stress the program's limits

Python stops any chain of more than 1,000 nested function calls by raising
`RecursionError`. Its `int()` refuses to convert a string of more than 4,300
digits, raising `ValueError`, to guard against very slow conversions.

The user types each of these lines:
1. 5,000 `(`, then `1`, then 5,000 `)`;
2. a 5,000-digit number;
3. `1+1+1+...+1`, with 1,000 ones.

For each, what does the program print or do, and in which function does it fail,
if it fails? Which of these break SPEC §2's promise that the program goes on after
an error and exits with status 0?

> [!answer]-
> **The two deep lines crash the program with a `RecursionError`; the long number is
> an ordinary error line.**
> 1. **Nested parentheses.** Each `(` makes `_factor` call `_expr`, which calls
>    `_term`, which calls `_factor` again: three calls per pair. About 330 pairs
>    reach the limit, so `parse` raises `RecursionError`. `main` catches only
>    `ValueError` and `ZeroDivisionError`, so the program stops with a traceback
>    and exit status 1.
> 2. **The long number.** `tokenize` keeps the digits as a string; `_factor`
>    calls `int()` on it, which raises `ValueError`. `main` prints
>    `error: Exceeds the limit (4300 digits) for integer string conversion: ...`
>    and reads the next line.
> 3. **The long sum.** `_expr` reads it with a loop, so `parse` is fine. But each
>    `+` makes the tree so far the left child of a new node, so the tree is 999
>    `+` nodes deep, and `evaluate` calls itself once per level. It raises
>    `RecursionError`, and the program stops with a traceback and exit status 1.
>
> Lines 1 and 3 break the promise: the Python version does not meet SPEC §2 there. `main`
> could catch `RecursionError` and print an `error:` line instead; a parser could
> also refuse nesting past a fixed depth with an ordinary error. The C and Rust
> versions handle all three lines differently: their integers are 64 bits, so line
> 2 is `error: number too large`, but their recursion is limited only by the size
> of the stack, and both compute lines 1 and 3 correctly.
> (`python/notes.md` §Design choices; SPEC §2.)

## Beyond this program

### 6. From calculator to interpreter

A Lisp interpreter reads programs such as `(define (square x) (* x x))` followed
by `(square 5)`. Every expression is a list in parentheses with the operator
first. It has the same stages as this calculator (split the text, build a tree,
compute a value), but a program can define variables and functions that later
lines use.

For each of `tokenize` and `parse`, `evaluate`, and `main`, name one thing it
would have to do in the interpreter that it doesn't do here. Then name one thing
the interpreter needs that the calculator never does, and say why the calculator
doesn't.

> [!answer]-
> **The stages stay the same; what grows is what each stage has to remember.**
> - **`tokenize` and `parse`** become a *reader* that records where each
>   expression came from (line and column), so an error can point at it. It reads
>   a whole batch of input before any of it runs, so broken source never runs
>   halfway, as `calculate` parses the whole line first. A careful reader also
>   refuses nesting past a fixed depth with a syntax error, which avoids question
>   5's crash.
> - **`evaluate`** needs *environments*, tables that map names like `x` and
>   `square` to values, and *special forms* such as `if` and `define`, which
>   decide which of their parts run instead of computing all of them as `+` does.
>   A function must remember the environment it was defined in.
> - **`main`** must keep the environment from one line to the next, so that
>   `(square 5)` can use the `square` defined earlier. The calculator's `main`
>   keeps nothing between lines.
>
> The interpreter also needs a way to free memory. A function or list can outlive
> the line that made it, so something must find which values are still reachable
> and reclaim the rest: a garbage collector, which an interpreter written in C or
> Rust must include itself. The calculator needs none: each line's tokens and tree
> are garbage as soon as its value is printed. (`python/notes.md` §Where this
> shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions handle large numbers and fractions

The C and Rust versions have the same three stages as the Python version. But
Python's integers have no size limit, while C's `int64_t` and Rust's `i64` hold at
most 9223372036854775807, and each language has its own usual way to print a
floating-point number.

For each version, say what it prints for `9223372036854775807+1`, and how it
prints `1/3` and `8/2`. Then find a line that one version answers with a value
while another reports an error.

> [!answer]-
> **All three give the same values on the lines the shared tests send; they differ
> in how large an integer may be and in how they write a float.**
> - **Python** prints `9223372036854775808`. `print` writes a float as the
>   shortest text that reads back as the same float: `0.3333333333333333`, and
>   `4.0` for `8/2`.
> - **C** prints `error: integer overflow`. Every integer operation goes through
>   C23's `ckd_add`, `ckd_sub`, or `ckd_mul`, which report whether the exact
>   result fit; a plain `+` that overflowed would be undefined behavior. Negation
>   is checked too, since negating the most negative `int64_t` overflows.
>   `printf("%.15g")` writes 15 significant digits, the most a `double` always
>   keeps exactly, and drops trailing zeros: `0.333333333333333`, and `4`.
> - **Rust** prints `error: integer overflow`, through `checked_add` and its
>   siblings, which return `None` on overflow; a plain `+` would panic in a debug
>   build and wrap around in a release build. Printing an `f64` with `{}` writes the
>   shortest text that reads back, like Python, but without a whole number's `.0`:
>   `0.3333333333333333`, and `4`. It never uses exponent notation, so
>   `1000000000000/1*1000000000000` prints as 25 digits where Python and C print
>   `1e+24`.
>
> Lines where they differ: `99999999999999999999` is a value in Python, but C and
> Rust print `error: number too large`, since the literal itself doesn't fit. So is
> `-9223372036854775808`, even though the result would fit, because the literal
> is read before it is negated. And `2` followed by a Windows line ending (`\r\n`)
> is 2 in Rust, whose line reader removes `\r\n`, while Python and C keep the `\r`
> and report an unknown character. (`notes.md` and `solution.*` in `c/` and
> `rust/`.)
