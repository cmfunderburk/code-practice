# Hangman — oral defense

Seven questions about the design of the Hangman program, for practising explaining
it aloud. Answer each question with its answer closed, then open the answer to
check yourself. Each answer starts with the main point and names the file that
settles it: `SPEC.md`, `python/solution.py`, or `python/notes.md`.

Question 7 compares the Python version with the C and Rust versions, which are in
`c/` and `rust/`.

> [!note]- Examiner prompt
> Paste this into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached (for question 7, attach the C and Rust
> `solution` files too):
>
> *You are examining a student on a small Hangman program, specified in SPEC.md and
> implemented in solution.py. Ask the questions from DEFENSE.md one at a time, in
> order. After each answer, ask follow-up questions about anything vague: ask for
> the specific function, input, or line of SPEC. Don't accept "it's cleaner"
> without the reason. Keep a list of claims that contradict SPEC.md or the code,
> and read it back at the end. Don't show the answers unless the student gives up.*

## Following a game through the program

### 1. Trace four guesses through the program

`random.choice` picks `jigsaw`, and the player types these lines, one after
another: `e`, `I`, `i`, and `7`. For each line, say which functions it passes
through, what the program prints, and what `main`'s variable `state` holds
afterwards. Then say which of the functions you named read input, print, or use
the random source.

> [!answer]-
> **`main` holds one value, `state`, and replaces it only when `guess` returns a
> new one.** Before the first guess, `main` calls `new_game("jigsaw")`, which
> returns a state with nothing guessed, and prints `______  wrong: 0/6`. Each turn
> `main` reads a line with `input()`, removes surrounding spaces with `strip()`,
> converts it to lowercase with `lower()`, and checks that it is one letter `a`–`z`.
> 1. `e` is a letter, so `main` calls `guess(state, "e")`, which returns a new
>    state with `e` in `guessed`, and `main` assigns it to `state`. `e` is not in
>    `jigsaw`, so `wrong_count` gives 1 and `main` prints `______  wrong: 1/6`.
> 2. `I` becomes `i`. `guess` returns a state with `e` and `i` guessed, `masked`
>    gives `_i____`, and `main` prints `_i____  wrong: 1/6`.
> 3. `i` again: `guess` raises `ValueError("already guessed: i")`. `main` catches
>    it, prints `already guessed: i`, and keeps the old state, so it prints
>    `_i____  wrong: 1/6` again.
> 4. `7` is not a letter, so `main` prints `one letter a-z, please` and starts the
>    next turn without calling `guess`.
>
> Only `main` reads input, prints, or calls `random.choice`. `new_game`, `guess`,
> `masked`, `wrong_count`, and `status` only compute a value from their arguments.
> (`python/solution.py`; SPEC §3.)

## Design choices

### 2. Storing the game's status, or computing it

`HangmanState` holds three fields: `secret`, `guessed`, and `max_wrong`. The
function `status` works out whether the game is `"playing"`, `"won"`, or `"lost"`
from those fields each time it is called.

Another design would add a fourth field, `status`, and have `guess` set it
whenever a guess wins or loses the game. Compare the two designs. What must
`guess` get right in the second design that it doesn't have to think about in the
first? Give one mistake that is possible only in the second design, and say what
the player would see.

> [!answer]-
> **A stored status is a second record of something the guesses already decide,
> so it can disagree with them; a computed one can't.**
>
> In the second design, `guess` must update the field on every path that can end
> the game, and must do it after adding the letter, because the new letter is what
> decides the new status. Suppose `guess` checked for a win before adding the
> letter. The guess that completes the word would leave the field at `"playing"`,
> so the player would see the whole word (for example `jigsaw  wrong: 1/6`) and be
> asked for another guess.
>
> In the first design, `status` compares `set(state.secret)` with `state.guessed`
> and calls `wrong_count` each time, so its answer always matches the fields, and
> `masked` and `wrong_count` work the same way. There is no update for `guess` to
> forget or to do in the wrong order. The only extra work is going over the word
> again on every call, which takes no noticeable time for a word of a few letters.
> (`status` in `python/solution.py`; `python/notes.md`
> §Design choices.)

### 3. Where the random choice happens

`main` picks the secret with `random.choice(WORDS)` and passes it to `new_game`.
Nothing else in the program uses `random`.

Explain why this makes `new_game`, `guess`, `masked`, `wrong_count`, and `status`
easy to test, and how a test of `main` can still make the game use a known word.
Then consider a different design, in which the program reads the secret word from
the first line of input. What would that change for testing, and for the player?

> [!answer]-
> **Every function except `main` receives the word as an argument, so a test just
> passes in the word it wants.** A test of the rules calls `new_game("banana")`
> and then `guess`, and knows exactly what each call must return. There is nothing
> to seed or replace, and the same calls give the same results every time.
>
> `main` is the only function that uses randomness, so only its tests need to
> control it. They replace `random.choice` with a function that returns a chosen
> word and checks that it was asked to choose from `WORDS` (`_secret` in
> `python/test_solution.py`). The shared tests in `test_program.py` don't
> control the word at all: they check only facts that hold for every word, such as
> how guessing `a` to `z` in order must end.
>
> Reading the secret from the first line would make every run predictable from its
> input, so a single exact transcript could test the whole program. But nobody
> could play alone: someone else would have to type the word, and the terminal
> would show it. That design makes testing easier by giving up the game.
> (`main` in `python/solution.py`; SPEC §1.)

### 4. Two kinds of bad input, checked in two places

The player can type two kinds of line that the program must refuse. Some are not a
guess at all, such as `7`, `ab`, or an empty line. Others are a proper letter that
the rules don't allow, such as a letter already guessed.

For each kind, which function detects it, and how does `main` respond? Then
explain why each check sits where it does: why doesn't `main` check for repeated
letters, and why doesn't `guess` check for lines such as `ab`?

> [!answer]-
> **`main` checks that a line is a letter; `guess` checks that the rules allow the
> letter.**
> - After `strip()` and `lower()`, `main` refuses anything that is not exactly one
>   character of `string.ascii_lowercase`, prints `one letter a-z, please`, and
>   starts the next turn. `guess` never sees such a line. Lines are `main`'s job
>   because `main` is the only function that reads them; `guess` takes a letter,
>   not a line.
> - `guess` raises `ValueError` for a letter already guessed (`already guessed: i`)
>   and for any guess after the game has ended (`game is over: won`). `main`
>   catches the error, prints its message, and assigns nothing to `state`, so the
>   old state stays and the guess changes nothing.
>
> The rules are in `guess` so that every caller gets them, not just this `main`:
> the tests call `guess` directly and rely on it to refuse. In this `main` the
> `game is over` error never actually happens, because the `while` loop stops as
> soon as `status` is no longer `"playing"`. `guess` checks anyway, because another
> caller might not have that loop. (`python/solution.py`; SPEC §1–§2.)

## Unusual input

### 5. Input ends in the middle of a game

Input can end before the game does: the player presses Ctrl-D at the terminal, or a
file of guesses piped into the program runs out. What does `input()` do then, what
does `main` print, and what exit status does the program return? Then suppose
`main` had no `except EOFError` around its `input()` call. What would happen
instead, and why would that matter to a script that runs the program?

> [!answer]-
> **`input()` raises `EOFError`; `main` catches it, prints
> `you quit! the word was <secret>`, and returns, so the program exits with status
> 0.** SPEC §2 allows this: if input ends first, the program stops, and it may show
> the word.
>
> Without the `except EOFError`, the error would pass out of `main` uncaught.
> Python would print a traceback ending in `EOFError: EOF when reading a line` and
> exit with status 1. A script that checks the exit status could then no longer
> tell a player who stopped early from a program that crashed. The shared test
> `test_end_of_input_stops_cleanly` runs the program on input that ends early, and
> its `run_program` fixture checks for exit status 0;
> `test_main_reports_a_quit_at_end_of_input` in `python/test_solution.py`
> checks the message. (`main` in `python/solution.py`; SPEC §2.)

## Beyond this program

### 6. The same loop in an interactive interpreter

`main` is a loop: read a line, compute a new state from it, print something, and
repeat until input ends or the game is over. A refused line is reported, and the
loop goes on.

An interactive interpreter has the same shape. The `>>>` prompt you get by running
`python3` with no arguments is one; it is called a REPL, for read, evaluate, print,
loop. Compare the two loops. What does each carry from one line to the next? Then
name two things a REPL has to handle that Hangman's loop does not.

> [!answer]-
> **Both read a line, update one piece of state, print, and stop at end of input;
> a REPL's state and input are far larger.**
> - Hangman carries one `HangmanState` value. Each accepted guess makes `guess`
>   return a new one, and `main` assigns it to `state`. Nothing is changed in
>   place.
> - Python's REPL carries the variables, functions, and imports defined so far.
>   Typing `x = 1` changes that collection in place, and every later line can use
>   `x`.
>
> Things a REPL handles that Hangman's loop doesn't:
> - **Input that spans several lines.** After `def f():`, there is nothing to
>   evaluate yet. The REPL prints a `...` prompt and keeps reading until the
>   definition is complete. In Hangman, every line is a complete guess or a
>   refusal.
> - **State that keeps growing.** Every definition adds to the REPL's state, and
>   values that nothing refers to any more must be freed, which Python does
>   automatically. Hangman's state never holds more than the word and 26 letters.
>
> A Lisp interpreter's REPL works the same way: it reads stdin line by line in one
> persistent environment of definitions, keeps reading while an expression is
> incomplete, reports an error and accepts new input, and stops at end of input.
> (`python/notes.md` §Where this shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions keep `guess` from changing the game it was given

In the Python version, `guess` never changes the state it is given: it returns a
new `HangmanState`, and `main` replaces its old state with the new one. The C and
Rust versions follow the same design, each with its own language's tools.

For each version, say what stops `guess` from changing the caller's game, and
whether a mistake would be caught when the program is compiled, when it runs, or
not at all. Then say how each version picks its word, and find one line of input
that one version accepts as a guess while another refuses it.

> [!answer]-
> **All three return a new game from `guess` and pick the word only in `main`; they
> differ in what enforces the rule and in how they read a line.**
> - **Python** checks while the program runs. `HangmanState` is a frozen
>   dataclass, so assigning to one of its fields raises `FrozenInstanceError`, and
>   `guessed` is a `frozenset`, which has no methods that change it. `guess` builds
>   a new state around `state.guessed | {letter}`, which is a new set. The word is
>   `random.choice(WORDS)`.
> - **C** relies on copying. `guess` takes its `Game` by value, so it receives a
>   copy of the 26 `guessed` flags and of the `secret` pointer. It sets a flag in
>   its copy and writes the copy out through `next`. Nothing stops `guess` from
>   changing its copy, but the caller's game can't be reached from it. Every copy
>   shares one secret, which is safe because `secret` is a `const char *` pointing
>   at a string literal, and the compiler rejects any write through it. The word is
>   `WORDS[(size_t)rand() % WORD_COUNT]`, after `main` seeds `rand` once with
>   `srand(time(nullptr))`. The seed is the time in whole seconds, so two games
>   started in the same second pick the same word.
> - **Rust** checks when the program is compiled. `guess` takes `&self`, a shared
>   borrow, and the compiler rejects any change to the game through it, so `guess`
>   clones the game and inserts the letter into the clone. Rust's standard library
>   has no random numbers, so the word is `WORDS.choose(&mut rand::rng())` from the
>   `rand` crate; `choose` returns an `Option` because the list could be empty.
>
> C never allocates memory on the heap. Rust's clone allocates a new `String` and
> new storage for the `BTreeSet` on every accepted guess, and Python builds a new
> state and a new set each time. For one game of a few guesses, none of this is
> noticeable.
>
> Lines are read differently. Python removes surrounding spaces with `strip()`,
> and Rust's `letter_of` with `trim()`, but C reads with `fgets` and removes only
> the line ending. So ` j ` (with spaces) is a guess of `j` in Python and Rust, and
> C answers `one letter a-z, please`. C also reads into a 64-byte buffer, so a
> longer line arrives in pieces that are answered one at a time: 63 `x`s followed
> by `j` on one line gets one reminder and then counts as a guess of `j`, where
> Python and Rust refuse the whole line once. All three give the same answers to
> the lines the shared tests send, which is all SPEC §4 requires.
> (`c/notes.md`, `rust/notes.md`, and each version's `solution` file.)
