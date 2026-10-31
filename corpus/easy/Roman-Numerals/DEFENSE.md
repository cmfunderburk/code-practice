# Roman Numerals — oral defense

Seven questions about the design of the Roman numeral converter, for practising
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
> *You are examining a student on a small Roman numeral converter, specified in
> SPEC.md and implemented in solution.py. Ask the questions from DEFENSE.md one at a
> time, in order. After each answer, ask follow-up questions about anything vague:
> ask for the specific function, input, or line of SPEC. Don't accept "it's
> cleaner" without the reason. Keep a list of claims that contradict SPEC.md or the
> code, and read it back at the end. Don't show the answers unless the student
> gives up.*

## Following a line through the program

### 1. Trace four input lines through the program

The user types these four lines, one after another: `1990`, `IIII`, `0042`, and
`mcmxc`. For each line, say which functions it passes through, which branch of the
`if` statement in `main` handles it, and what the program prints.

> [!answer]-
> `input()` returns each line without its `\n`. `main` removes surrounding spaces
> with `strip()`, converts the line to uppercase with `upper()`, and then tests it
> in order: is it ASCII digits, is it empty or does it contain a letter outside
> `VALUES`, is it canonical (`_canonical`), or else it is not canonical.
> 1. `1990` is ASCII digits (`isascii()` and `isdigit()` are both true).
>    `to_roman(1990)` walks the table: `M` leaves 990, `CM` leaves 90, `XC`
>    leaves 0, so `main` prints `MCMXC`.
> 2. `IIII` is all numeral letters, so it reaches `_canonical`. `from_roman`
>    gives 4, and `to_roman(4)` gives `IV`, which is not the line, so `main`
>    prints `error: not a canonical numeral: IIII`.
> 3. `0042` is ASCII digits. `int` gives 42, and `to_roman(42)` is `XLII`.
> 4. `mcmxc` becomes `MCMXC` after `upper()`. It is canonical, so `main` prints
>    `from_roman("MCMXC")`, which is `1990`.
>
> `main` keeps nothing from one line to the next, so each output depends only on
> its own line. `to_roman` and `from_roman` only compute; every `input()` and
> `print()` call is in `main`. (`python/solution.py`; SPEC §3.)

## Design choices

### 2. A table or a rule: two ways to handle IV, XC, and CM

The program converts in both directions: from a number to a numeral
(*rendering*) and from a numeral to a number (*parsing*). Both have to handle the
subtractive pairs such as IV, XC, and CM.

`to_roman` handles them with a table: `CM`, `CD`, `XC`, and the rest are rows of
their own, next to `M`, `D`, and `C`. `from_roman` handles them with a rule
applied while scanning: read left to right, and subtract a symbol's
value when the symbol after it is larger.

Compare the two. Where does each one keep the knowledge of which pairs are
allowed? What does each do when given a string that isn't a valid numeral, such as
`IM`?

> [!answer]-
> **`to_roman` keeps it in data; `from_roman` doesn't keep it at all.**
> - `ROMAN_TABLE` lists exactly the six allowed pairs (`CM`, `CD`, `XC`, `XL`,
>   `IX`, `IV`), and `to_roman` can only write what the table contains. It never
>   writes `IM`, because `IM` is not a row. Adding or removing a pair would be a
>   change to the table, not to the loop, which is three lines.
> - `from_roman`'s rule, "subtract when the next symbol is larger", is shorter
>   than a list, but it never says which pairs are allowed, so it accepts pairs
>   that aren't. Given `IM`, it subtracts 1, adds 1000, and returns 999 with no
>   complaint. Given `IIII`, it returns 4. It gives the right answer only for input
>   that is already a valid numeral.
>
> So the input question has two different answers. `to_roman` can't be given an
> invalid numeral (its input is a number), and it raises `ValueError` for a number
> outside 1–3999. `from_roman` can be given one, and quietly returns a wrong
> number. That is why the program checks a numeral before trusting `from_roman`'s
> answer (question 3). (`python/solution.py`; SPEC §1.)

### 3. How the program decides that a numeral is valid

`from_roman` returns a number for any string of numeral letters, valid or not:
`IIII` gives 4. Yet the program refuses `IIII`. The function `_canonical` makes
that decision. It calls `from_roman` on the line, calls
`to_roman` on the result, and checks whether it got the original line back. Call
this the *round-trip check*.

Two other ways to check a numeral would be a regular expression that matches
exactly the valid numerals, or a stricter `from_roman` that rejects invalid input
as it scans. What does the round-trip check have that those two lack? And why does
`_canonical` catch `ValueError`?

> [!answer]-
> **The round-trip check reuses `ROMAN_TABLE`, so the program has one definition of
> a valid numeral instead of two.** `to_roman` writes only valid numerals. If it
> writes back exactly the line it was given, the line is valid; if it writes
> anything else, the line wasn't. (`IIII` parses to 4, and 4 renders as `IV`.)
>
> A regular expression such as
> `M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})` describes the same rules
> a second time, in a different notation. Anyone who changed one would have to
> remember to change the other. (This one also matches the empty string, so it
> needs a separate check that the line isn't empty.) A stricter `from_roman` would
> spread the same rules through its loop and its conditions, and would be more
> code to write and test. The round-trip check does one extra `to_roman` call per
> numeral line, on at most fifteen letters.
>
> `_canonical` catches `ValueError` because `to_roman` raises it for a number
> outside 1–3999, and `from_roman` can produce such a number: `MMMM` parses to
> 4000. A number with no numeral has no valid numeral, so `_canonical` returns
> `False` (question 5). (`_canonical` in `python/solution.py`; SPEC §1.)

### 4. What `main` should do with a line it can't convert

Here is a simpler `main` that removes spaces and converts to uppercase as the real
one does, but then trusts every line:

```python
def main() -> None:
    while True:
        try:
            line = input().strip().upper()
        except EOFError:
            return
        if line.isdigit():
            print(to_roman(int(line)))
        else:
            print(from_roman(line))
```

What would this `main` do with each of these five lines: an empty line, `MMMM`,
`٤٢` (42 written in Arabic-Indic digits), `0`, and `hello`? For each, which check
in the real `main` prevents the problem?

> [!answer]-
> **Every problem comes from trusting a line before checking it.** Removing spaces
> and converting to uppercase are not the problem: someone who types ` mcmxc ` at a
> terminal means `MCMXC`, so the real `main` does both too.
> - **Empty line:** `"".isdigit()` is false, so it goes to `from_roman("")`, which
>   adds nothing and prints `0`. The real `main` refuses it with `not line`.
> - **`MMMM`:** `from_roman` prints `4000`, a number outside the program's range,
>   because nothing checks the numeral. The real `main` sends every numeral through
>   `_canonical`, where `to_roman(4000)` raises and the line is refused as not
>   canonical.
> - **`٤٢`:** `str.isdigit` is true for digits in any script, and `int` reads
>   these as 42, so it prints `XLII`. The real `main` also requires `isascii()`, so
>   the line falls through and is refused, because `٤` is not in `VALUES`.
> - **`0`:** `to_roman(0)` raises `ValueError`. Nothing catches it, so the program
>   stops with a traceback and exit status 1. The real `main` wraps the call in
>   `try`/`except ValueError` and prints `error: out of range: 0`.
> - **`hello`:** `from_roman` looks up `H` in `VALUES` and raises `KeyError`,
>   another traceback. The real `main` refuses any line containing a letter
>   outside `VALUES` before it calls `from_roman`.
>
> In the real `main`, every refusal is one `error:` line and the program goes on to
> the next line, as SPEC §2 requires. (`python/solution.py`;
> `python/notes.md` §Design choices; SPEC §2.)

## Unusual input

### 5. A very long string of `M`s

The user types `MMMMMMMMMMMMMMM` (fifteen `M`s). What does the program print, and
which functions does the line pass through to get there? Then suppose `_canonical`
had no `try`/`except` and simply returned
`to_roman(from_roman(numeral)) == numeral`. What would happen instead?

> [!answer]-
> **It prints `error: not a canonical numeral: MMMMMMMMMMMMMMM`.** The line is all
> numeral letters, so `main` passes it to `_canonical`. `from_roman` adds fifteen
> 1000s to get 15000, and `to_roman(15000)` raises `ValueError("out of range:
> 15000")`. `_canonical` catches it and returns `False`, so `main` takes its last
> branch.
>
> Without the `try`/`except`, the `ValueError` would pass up through `_canonical`
> and out of `main`, which doesn't catch it there, and the program would stop with
> a traceback and exit status 1. `MMMM` (4000) takes the same path. So would a line
> of a thousand `M`s: the Python version puts no limit on line length, and
> Python's `int` grows as large as it needs to.
> (`_canonical` in `python/solution.py`;
> `test_non_canonical_numerals_are_refused` in `test_program.py`; SPEC §1–§2.)

## Beyond this program

### 6. Other programs where a parser and a renderer must agree

In this program, `from_roman` is a *parser*: it turns text into a value. `to_roman`
is a *renderer*: it turns a value back into text. The round-trip check depends on
the two agreeing, so that rendering what was parsed gives back the original text.

Name two other kinds of program that have both a parser and a renderer for the
same text or file format. For each, say what goes wrong when the two disagree.
Then compare: if `to_roman` had a wrong row, what would the user of this program
see, and when?

> [!answer]-
> **Anything that both writes and reads the same format needs the two to agree, and
> the more it stores, the more a disagreement costs.** Three common kinds:
> - **An interpreter's reader and printer.** A Lisp interpreter's *reader* turns
>   source text into lists, symbols, and strings, and its *printer* turns values
>   back into text. If the printer writes a string containing `"` without a
>   backslash before the quote, reading that output back gives a different value
>   or a syntax error. So a careful printer writes strings with the same
>   backslash escapes its reader understands.
> - **Save and load.** A program that saves its data to a file renders on save
>   and parses on load. The Todo Store program in this track has `save` and
>   `load` commands. If the two disagree, the data that comes back is not the data
>   that was saved, and the user may not notice until long after.
> - **A network protocol.** A server and its clients render messages to bytes and
>   parse bytes back into messages. A key-value store such as Redis can also write
>   every change to a log file in the same format it uses on the network (Redis's
>   append-only file is written in its RESP protocol), and rebuild its data at
>   startup by parsing that log. If its parser and renderer disagree, stored data
>   is lost.
>
> Here, a wrong row in `to_roman` would show up at once. Numbers would get wrong
> numerals, and the round-trip check would refuse correct numerals. Both happen at
> the terminal, in the user's next answer, and nothing is stored. In a save file or
> a log, the wrong text is written to disk and the mistake is found later, when the
> data is read back. (`python/notes.md` §Where this shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions read a line

All three versions use the same table and the same round-trip check, but each
reads its input with its own language's usual tools. For each version, say how it
turns a line into a number. Then find one line that one version reads as a number
or numeral while another refuses it.

> [!answer]-
> **The table and the round-trip check are the same in all three; how a line is
> read is each language's usual way.**
> - **Python** removes surrounding spaces with `strip()`, converts to uppercase
>   with `upper()`, and takes a line as a number only when it is ASCII digits.
>   `int` reads a number of any length.
> - **Rust** removes surrounding spaces with `trim()`, converts with
>   `to_ascii_uppercase()`, and reads a number with `line.parse::<i64>()`.
>   `parse` accepts a sign, so `+12` is a number. A number too large for `i64`
>   fails to parse and is refused as neither a number nor a numeral. Every number
>   in the Rust version is an `i64`, including `from_roman`'s running total, which
>   must be signed because it can go below zero partway through (`IV` starts at
>   −1). Using one type throughout means no conversion between the parser and the
>   renderer.
> - **C** reads each line with `fgets` into a 64-byte buffer and removes the line
>   ending with `strcspn(line, "\r\n")`, so a `\r\n` line ending works. It converts
>   to uppercase with `toupper` and reads a number with `strtol`, which skips
>   spaces before the number, accepts a sign, and turns a huge number into
>   `LONG_MAX`, which is then out of range. It removes no other spaces. A line too
>   long for the buffer is read to its end and refused once. `to_roman` writes into
>   a buffer the caller owns, declared `char out[static NUMERAL_MAX + 1]`, so the
>   program never allocates memory on the heap.
>
> Examples where they differ: `+12` is `XII` in C and Rust, but Python refuses it.
> ` XII` (with a leading space) is 12 in Python and Rust, but C refuses it, and C
> refuses `12 ` (with a trailing space) too. A twenty-digit number is out of range
> in Python and C, but Rust says it is not a number at all. All three give the
> same answers on the plain lines the shared tests send, which is all SPEC §4
> requires. (`notes.md` and `solution.*` in `c/` and `rust/`.)
