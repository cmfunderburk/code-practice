# Writing for the reader

How to write the documents and cues in this corpus: `SPEC.md`, `DEFENSE.md`, each
language's `problem.md` and `notes.md`, the cues in `sections.toml`, comments in
`annotated_solution.*`, and docstrings, comments, and test names in the code (a
failing test's name is printed to whoever runs it).

## The reader

The reader is a novice-to-intermediate programmer. They have read the program's
`SPEC.md` and `problem.md`, and studied or written its code. They have not read
anything else: not the history of the program, not other versions of it, and not
other programs in the corpus.

Every sentence must make sense to that person. For a DEFENSE question, the test is
an exam: would a student sitting this question in a university exam know what is
being asked, and how to start answering it?

## Rules

### 1. Name who acts

A person or a named function does each thing. "Rendering puts every rule in data"
has no actor; "`to_roman` reads every rule from `ROMAN_TABLE`" has one. Languages,
programs, halves, and lines do not decide, choose, cost, or buy anything. A
programmer writing in C chooses; `strtol` skips leading spaces.

### 2. Define a term or don't use it

Ordinary programming vocabulary (function, parser, buffer, stdin, exit status,
test) needs no definition. A term that only makes sense to someone who built the
corpus does, and usually has a plain replacement: "the Python version", not "the
Python telling"; "`main`", not "the shell"; "the reference implementation" or "a
check", not "the oracle". A term the program itself defines (Roman Numerals'
*canonical numeral*) is fine once it is defined, used exactly as defined. A word
used as a label in an example (`Blinker (5x5)`) is not a definition.

### 3. A question builds its frame, then asks one thing

Before asking, a question states what the reader needs to orient: which functions,
which inputs, which two designs are being compared. Then it asks for something
specific and says what kind of answer is wanted (a trace, a comparison, an output,
a failure case). If the answer is the first place the question's setting is
explained, the question is too short.

### 4. Ask about the program

A question is about what the program does and why its code is shaped as it is,
never about how the corpus was assembled.

### 5. No history

No dates, no earlier versions, no "now", "no longer", or "until". If an earlier
version's bug teaches something, state it as a property of a design: "A `main` that
trusts `str.isdigit` would read `٤٢` as 42."

### 6. Everything needed is on the page

A question is answerable from `SPEC.md`, the code, the program's own documents, and
the question itself. Another program or project appears only with enough said
about it, where it appears, that a reader who has never seen it can follow.

### 7. Plain sentences, not aphorisms

"Either half alone is half a boundary" and "the log format is the wire format" are
summaries for someone who already understands. Say the thing they summarize.
Avoid "what does it cost, and what does it buy?": name what is traded instead, such
as lines of code, a class of bug ruled out, a test that becomes possible, or work
done twice.

### 8. Answers check; they don't teach the setting

An answer leads with the decisive point, then gives the evidence: the line of
`SPEC.md`, the function, the branch, the output. It cites the file that settles it,
and is roughly as long as a good spoken answer.

### 9. Name the function, not the learner's part

The app drills the whole program, and readers may study it in other ways too. So
documents never say "your `to_roman`" or "the provided `from_roman`". They name the
function.

### 10. Cues say what the unit does

A cue is the sentence or two the learner recalls a unit's code from. It says what
the unit does, in plain words, with the names, exact messages, and edge cases
needed to write the code without dictating it. No role labels ("Composition
root:", "Derived view:"), and no phrases the learner would have to decode first.

## An example

Before (Roman Numerals DEFENSE, question 2):

> Both directions sit in one program. Why does the render table define canonical
> form, and not the greedy parse?

It assumes the reader already knows what "the render table" and "the greedy parse"
are and how they differ, so the answer has to explain the setting.

After:

> The program converts in both directions: from a number to a numeral
> (*rendering*) and from a numeral to a number (*parsing*). Both have to handle the
> subtractive pairs such as IV, XC, and CM.
>
> `to_roman` handles them with a table: `CM`, `CD`, `XC`, and the rest are rows of
> their own, next to `M`, `D`, and `C`. `from_roman` handles them with a rule
> applied while scanning: read left to right, and subtract a symbol's value when
> the symbol after it is larger.
>
> Compare the two. Where does each one keep the knowledge of which pairs are
> allowed? What does each do when given a string that isn't a valid numeral, such
> as `IM`?
