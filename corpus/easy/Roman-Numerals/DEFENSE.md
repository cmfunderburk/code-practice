# Roman Numerals — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or the
code. The last compares the C and Rust ports; attach their `solution` files to the
committee prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small Roman numeral converter, specified in
> SPEC.md and implemented in solution.py. Ask the questions from DEFENSE.md one at a
> time, in order. After each answer, press on anything vague: demand the specific
> structure, failure mode, or line of SPEC. Don't accept "it's cleaner" without the
> mechanism. Keep a list of claims that contradict SPEC.md or the code, and read it
> back at the end. Don't reveal the answer callouts unless the candidate concedes.*

## Lifecycle

### 1. Trace `1990`, `IIII`, `0042`, and `mcmxc` from stdin to the last line

Name each function each line passes through and the branch that decides its output.

> [!answer]-
> `input()` reads each line without its `\n`; `main` trims it, folds it to
> uppercase, and classifies it:
> 1. `1990` is ASCII digits (`isascii()` and `isdigit()`). `to_roman(1990)` walks
>    the table: `M` leaves 990, `CM` leaves 90, `XC` leaves 0, so it prints
>    `MCMXC`.
> 2. `IIII` is all numeral letters. `_canonical` parses it to 4 and renders 4 back
>    as `IV`, which differs from the line, so it prints
>    `error: not a canonical numeral: IIII`.
> 3. `0042` is digits: `int` gives 42, and `to_roman(42)` is `XLII`.
> 4. `mcmxc` folds to `MCMXC`, which is canonical, so it prints `1990`.
>
> The shell holds nothing between lines: each output depends on its line alone. The
> only pure work is `to_roman` and `from_roman`; every read and print is in `main`.
> (`python/solution.py`; SPEC §3.)

## Trade-offs

### 2. Both directions sit in one program. Why does the render table define canonical form, and not the greedy parse?

> [!answer]-
> Rendering puts every rule in data. The table's thirteen rows, the six subtractive
> pairs included, *are* the algorithm, and `to_roman` is a three-line `divmod` walk
> over them, so getting the rows right is the whole drill. The greedy parse puts the
> subtractive rule in one symbol of lookahead (subtract when the next symbol is
> larger), which is shorter to state but can't tell canonical input from junk: it
> parses `IM` to 999 without complaint. Either half alone is half a boundary. Render
> is the half that defines canonical form because its table also serves as the
> validator (question 3). (`python/notes.md` §Shapes chosen and rejected.)

### 3. `from_roman` accepts `IIII`. Why validate by rendering the parse back rather than with a canonical-form regex or a stricter parser?

> [!answer]-
> The round-trip law, `to_roman(from_roman(s)) == s`, uses the table that already
> defines canonical form, so there is one definition of "canonical" in the program.
> A regex such as `M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})`, which
> also matches the empty string and so needs a nonempty check beside it, is a
> second statement of the same grammar, and the two can drift apart. A stricter parser is
> the "parsing drill for another day" in the notes. The law costs one render per
> numeral line, at most fifteen symbols. It also has a precondition: the parse must
> land in 1–3999, or `to_roman` raises, so `_canonical` treats that `ValueError` as
> "not canonical" (question 5). (`python/notes.md`; `_canonical` in
> `python/solution.py`; SPEC §1.)

### 4. The shell strips and upper-cases the line. What else must it check, and what goes wrong without each check?

> [!answer]-
> The conveniences aren't the risk; what they feed into is. Without its checks:
> - an empty line isn't digits, so it would go to `from_roman("")` and print `0`;
> - `MMMM` would print `4000`, a number outside the domain, if nothing checked
>   canonical form;
> - `٤٢` (Arabic-Indic digits) passes `str.isdigit`, and `int` reads it as 42, so it
>   would print `XLII`;
> - `0` raises `ValueError` and `hello` raises `KeyError`, each ending the program
>   with a traceback if uncaught.
>
> So the shell trims and folds, because ` mcmxc ` at a terminal means `MCMXC`, but
> an empty line is refused, a number must also be `isascii()`, every numeral passes
> the round trip, and every refusal is an `error:` line instead of a traceback. A
> strict reader, nothing folded and at most four digits or fifteen letters, would
> let C and Rust print the same bytes on every line; SPEC instead leaves that
> reading to each implementation and fixes only the numerals. (`python/notes.md`
> §Shapes chosen and rejected; SPEC §2.)

## Adversarial

### 5. Feed it `MMMMMMMMMMMMMMM`. What does it print, and what would a shell that called `to_roman(from_roman(s))` unguarded do?

> [!answer]-
> It prints `error: not a canonical numeral: MMMMMMMMMMMMMMM`. The line is all
> numeral letters, so it reaches `_canonical`. `from_roman` adds fifteen `M`s to
> 15000, and `to_roman(15000)` raises `out of range: 15000`, which `_canonical`
> catches and reports as `False`. Unguarded, the `ValueError` would escape `main`
> and end the program with a traceback and exit status 1. `MMMM` takes the same
> path, at 4000, and so does a line of a thousand `M`s: the Python version caps no
> length, and its `int` grows as needed. (A thousand-digit *number* also gets
> through `int`; past 4,300 digits `int` itself raises `ValueError`, which the
> shell reports as out of range would be.)
> (`_canonical` in `python/solution.py`; SPEC §1–§2.)

## Scale

### 6. Where does this parser–renderer pair reappear at a larger size?

> [!answer]-
> In a Lisp interpreter, built on **parser / renderer separation (reader and
> printer)**: the reader turns text into data and the printer turns data back into
> text, at the size of a language with integers, strings, symbols, and nested lists.
> In a key-value store's persistence the round trip becomes load-bearing. When its
> append-only log is stored in the wire protocol (RESP, say), the log format is the
> wire format, and replay at startup parses what the renderer wrote. Here a
> disagreement between the halves is a rejected line; there it loses data.
> (`python/notes.md` §Scales up to.)

## Across languages

### 7. Each implementation reads a line its own way. How do the C and Rust ports turn a line into a number, and what does each accept that the others don't?

> [!answer]-
> **The table and the round-trip check are the same in all three; reading the line
> is each language's habit.**
> - **Python** trims with `strip()`, folds with `upper()`, and takes a number only
>   when it is ASCII digits, so `+12` is refused; `int` takes any length.
> - **Rust** trims with `trim()`, folds with `to_ascii_uppercase()`, and calls
>   `line.parse::<i64>()`. `parse` accepts a sign, so `+12` is `XII` and `-1` is
>   out of range, and a number too big for `i64` is refused as not a number. The
>   whole program works in `i64`, the parser's signed total included, so there is
>   no conversion between the parse and the render.
> - **C** reads with `fgets` into a 64-byte buffer and drops the line end with
>   `strcspn(line, "\r\n")`, so a `\r\n` terminal works. It folds with
>   `toupper` and reads a number with `strtol`, which skips leading spaces, takes
>   a sign, and clamps a huge number to `LONG_MAX`, out of range. A line too long
>   for the buffer is drained and refused once. `to_roman`
>   still writes into a buffer the caller owns, declared
>   `char out[static NUMERAL_MAX + 1]`, and nothing touches the heap.
>
> All three answer SPEC §4's plain lines the same way, which is all it asks.
> (`c/notes.md` and `rust/notes.md`.)
