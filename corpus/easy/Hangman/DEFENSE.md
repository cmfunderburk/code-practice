# Hangman — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or the
code. The last compares the C and Rust ports; attach their `solution` files to the
committee prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small Hangman program, specified in SPEC.md and
> implemented in solution.py. Ask the questions from DEFENSE.md one at a time, in
> order. After each answer, press on anything vague: demand the specific structure,
> failure mode, or line of SPEC. Don't accept "it's cleaner" without the mechanism.
> Keep a list of claims that contradict SPEC.md or the code, and read it back at the
> end. Don't reveal the answer callouts unless the candidate concedes.*

## Lifecycle

### 1. Trace a game of `jigsaw` through `e`, `I`, `i`, `7`

Name each function the input passes through, which ones are pure, and what the shell
holds between turns.

> [!answer]-
> 1. `random.choice(WORDS)` picks `jigsaw`, and `new_game("jigsaw")` makes the first
>    state value. The core never sees the random source.
> 2. Each turn, the shell prints `masked` and `wrong_count`, reads a line with
>    `input()`, strips and lowercases it, and calls `guess`. `guess` returns a
>    **new** state, which the shell rebinds.
> 3. `e` is a miss. `I` becomes `i`, a hit. The second `i` makes `guess` raise
>    `already guessed: i`, which the shell prints. `7` is not a letter, so the shell
>    answers `one letter a-z, please` without calling the core.
>
> Between turns the shell holds one value, `state`. `guess`, `masked`,
> `wrong_count`, and `status` are pure, and every read, print, and random pick is in
> `main`. (`python/solution.py`; SPEC §3.)

## Trade-offs

### 2. Why derive `status` instead of storing it, as an OO state machine would?

> [!answer]-
> A stored status is a second copy of a fact the guesses already determine, so it
> can disagree with them. An OO version that keeps `_status` must update it at
> exactly the right point in `guess`, after adding the letter. Here `status`
> recomputes won or lost from `secret`, `guessed`, and `max_wrong`, so no ordering
> obligation exists. The cost is recomputing over the secret on each call, trivial
> at this size. (`python/notes.md` §Shapes chosen and rejected.)

### 3. `main` calls `random.choice`. Why is the core still deterministic, and how would you script a game with a known word?

> [!answer]-
> The core is **handed** the secret: `new_game(secret)` takes it as an argument, and
> nothing below `main` touches `random`. So every rule can be checked with plain
> values, such as `new_game("banana")`, with no seeding or patching. Only the shell
> is random, and a script replaces `random.choice` with a function that returns a
> chosen word. Taking the secret from stdin instead would let one byte-exact
> transcript cover Python, C, and Rust, but it moves randomness out of the program
> to serve the transcript, not the design. (`python/notes.md` §Shapes chosen and
> rejected; SPEC §1.)

### 4. Where are illegal moves rejected, and why there and not in the shell?

> [!answer]-
> In the core: `guess` raises `ValueError` for a repeated letter or a finished game.
> The core owns the rules, so any shell, a GUI or a test, gets them for free. The
> shell's job is to report the error and keep the old state, which it does by
> catching the error and not rebinding. Input *format* (one letter `a`-`z`, after
> stripping and lowercasing) is the shell's job, because the core is handed
> letters, not lines. (`python/solution.py`; SPEC §2.)

## Adversarial

### 5. Input ends in the middle of a game. What happens, and what if `main` had no `except EOFError`?

> [!answer]-
> `input()` raises `EOFError`; the shell catches it, prints
> `you quit! the word was <secret>`, and returns, so the program exits 0 (SPEC §2).
> Without the handler the program would die with a traceback and exit status 1,
> and a piped game that ran out of guesses would be indistinguishable from a crash.
> (`main` in `python/solution.py`.)

## Scale

### 6. How does this loop relate to a Lisp REPL?

> [!answer]-
> It is the same shape, at a smaller size. Both read stdin line by line, thread one
> piece of session state through a pure-ish core, report errors without ending the
> session, and stop at end of input. Hangman threads a frozen `HangmanState`, while
> a Lisp REPL threads a mutable global environment and must also handle input that
> spans lines (an incomplete form waits for more) and garbage collection of
> discarded results. (`python/notes.md` §Scales up to.)

## Across languages

### 7. Python freezes `HangmanState`. How do the C and Rust ports keep `guess` from changing the game it was given, and where does each get its word?

> [!answer]-
> **All three keep the functional core and pick the word in the shell, each from its
> language's ordinary source.**
> - **Python** checks at run time. Assigning to a frozen dataclass's field raises
>   `FrozenInstanceError`, and `guess` builds a new state around a new `frozenset`.
>   The word is `random.choice(WORDS)`.
> - **C** relies on value semantics. `Game` is a `const char *secret` and
>   `bool guessed[26]`, so passing it by value copies the 26 flags and the
>   pointer. Every copy shares one secret, which is safe because it points at a
>   string literal that no one can write through. `guess` changes its own copy and
>   writes it through `next`. The word is `WORDS[(size_t)rand() % WORD_COUNT]`,
>   after seeding `rand()` once with `srand(time(nullptr))`.
> - **Rust** checks at compile time. `guess` takes `&self`, a shared borrow that
>   can't modify the game, so it clones the game and inserts into the clone. std
>   has no random numbers, so the word is `WORDS.choose(&mut rand::rng())` from the
>   `rand` crate, which returns `Option` in case the list is empty.
>
> C never touches the heap. Rust's clone allocates a new `String` and `BTreeSet` per
> guess, a few dozen allocations in a whole game. Each keeps only SPEC §4's fixed
> output, so their wording may differ. (`c/notes.md` and `rust/notes.md`.)
