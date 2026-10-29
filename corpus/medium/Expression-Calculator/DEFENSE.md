# Expression Calculator — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or the code.
The last compares the C and Rust ports; attach their `solution` files to the committee
prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small calculator program, specified in SPEC.md
> and implemented in solution.py. Ask the questions from DEFENSE.md one at a time, in
> order. After each answer, press on anything vague: demand the specific structure,
> grammar rule, failure mode, or line of SPEC. Don't accept "it's more extensible"
> without naming what would attach and where. Keep a list of claims that contradict
> SPEC.md or the code, and read it back at the end. Don't reveal the answer callouts
> unless the candidate concedes.*

## Lifecycle

### 1. Trace `2*-3` from stdin to the printed line

Name each stage, what it hands the next, and which grammar rule handles the minus.

> [!answer]-
> 1. `input()` gives `2*-3`.
> 2. `tokenize` gives `["2", "*", "-", "3"]`.
> 3. `parse` runs `_expr` → `_term` → `_factor`, which reads `2`. `_term` sees `*`
>    and calls `_factor` again, which sees `-` and recurses (`factor := '-' factor`)
>    to build `("neg", ("num", 3))`. The tree is
>    `("*", ("num", 2), ("neg", ("num", 3)))`.
> 4. `evaluate` folds it to the integer `-6`, and `print` shows `-6`.
>
> Every stage is pure; only `main` reads and prints. Unary minus is legal after `*`
> because it lives in `factor`, below the binary operators.
> (`python/solution.py`; SPEC §1.)

## Trade-offs

### 2. Single-pass evaluation is shorter and allocates no tree. Why build the AST?

> [!answer]-
> The tree is a representation that exists between text and number, so other things
> can attach to it: a printer, a simplifier, a compiler. `parse` can also be tested
> without evaluating anything. A single-pass evaluator returns values from each
> grammar level, so there is nothing to inspect or reuse. The cost is O(n) nodes,
> trivial here. (`python/notes.md` §Shapes chosen and rejected.)

### 3. How does the grammar encode precedence and left associativity?

> [!answer]-
> - **Precedence** comes from layering: `expr` is built from `term`s, and `term`
>   from `factor`s. `*` and `/` live one level down, so they bind tighter.
> - **Left associativity** comes from the loops, not recursion. `_expr` reads one
>   term, then repeatedly folds `node = (op, node, right)`. So `20-5-3` becomes
>   `((20-5)-3)`, which is 12.
>
> A right-recursive rule (`expr := term '-' expr`) would give `20-(5-3)`, which is 18.
> (SPEC §1; `_expr` and `_term` in `python/solution.py`.)

### 4. Why does `calculate` raise `ZeroDivisionError` while the program prints an error line?

> [!answer]-
> They are two boundaries with different jobs. `calculate` is an API whose contract
> is "a value or an exception", so it raises. The shell owns the session, and one
> bad line shouldn't end it, so `main` catches both `ValueError` and
> `ZeroDivisionError` and prints `error:`. A shell that caught only `ValueError`
> would let `1/0` kill the REPL with a traceback. (`python/notes.md`, the shell
> paragraph; SPEC §4.)

## Adversarial

### 5. Feed it 5,000 nested parentheses, then a 5,000-digit number. What happens, and is either a bug?

> [!answer]-
> - **Nesting.** Each `(` is one more `_factor` → `_expr` → `_term` call, so a few
>   thousand open parentheses exceed Python's recursion limit. `RecursionError`
>   is neither `ValueError` nor `ZeroDivisionError`, so the shell doesn't catch
>   it and the program dies with a traceback.
> - **Digits.** `int(token)` refuses a literal of more than 4,300 digits with a
>   `ValueError` (a guard against slow conversions), which the shell reports as
>   an `error:` line.
>
> Neither is part of the calculator's spec; both are Python facts. The ports have
> the opposite limits: their stacks run much deeper, but their integers are 64
> bits, so a 20-digit literal is already an overflow error. Catching
> `RecursionError` in the shell would be a one-line hardening, not a design
> change. (`python/notes.md` §Shapes chosen and rejected; SPEC §1.)

## Scale

### 6. What does this calculator become in a Lisp interpreter?

> [!answer]-
> - The tokenizer and parser become a **reader** that keeps source locations, and a
>   **printer** renders values back to text.
> - "Build the whole tree before evaluating" becomes a rule over **batches**: reading
>   finishes before evaluation begins, so malformed source can't partially execute.
> - `evaluate`'s `match` becomes an evaluator with special forms, lexical
>   environments, closures, tail calls, and a dispatch table of primitives.
> - Because Lisp values can outlive their line, the language also needs garbage
>   collection.
>
> (`python/notes.md` §Scales up to.)

## Across languages

### 7. Python's integers never overflow. What do the C and Rust ports do instead, and how does each print `1/3`?

> [!answer]-
> **Both ports use 64-bit integers and check every operation.** C uses C23's
> `ckd_add`, `ckd_sub`, and `ckd_mul`, which report overflow, and Rust uses
> `checked_add` and its siblings, which return `None`. Either way an overflowing
> line is an error line. Unchecked, the C would hit undefined behavior, and Rust
> would panic in a debug build and wrap silently in a release build. Negation is
> checked too, since negating the most negative `i64` overflows.
>
> Each prints a float its own way:
> - **Python** `print` gives the shortest text that reads back to the same float:
>   `0.3333333333333333`, and `4.0` for `8/2`.
> - **C** `printf("%.15g")` gives 15 significant digits, the most a `double`
>   always keeps, with trailing zeros dropped: `0.333333333333333`, and `4`.
> - **Rust** `Display` gives the shortest round-trip text like Python, but drops a
>   whole number's `.0`: `0.3333333333333333`, and `4`.
>
> SPEC §4 fixes the value, to nine significant digits, not the text.
> (`c/notes.md` and `rust/notes.md`.)
