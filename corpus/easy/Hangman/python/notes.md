## Functional Core — worked example

**Intuition.** Hangman's entire state is three values: the secret, the set
of guessed letters, the budget. Everything else — the mask, the miss count,
won/lost — is DERIVED, so the natural implementation stores nothing it
can compute: `HangmanState` is a frozen value, `guess` returns a new state,
and `status`/`masked`/`wrong_count` are pure views. Nothing can ever
disagree with anything, and the purity check (`guess` twice from one state,
equal results, input untouched) is only expressible in this implementation.
The guards stay: illegal transitions (repeat letter, game over) raise
`ValueError` — a terminal guard, enforced in a pure function.

Worked check: `"banana"` after guesses a, x, n → masked `"_anana"`, one
wrong, still playing; then b → `"banana"`, won.

**Complexity.**
- Time: $O(n)$ over the secret per view; Space: $O(g)$ guessed letters per
  state.

**Discussed, not drilled.** `dataclasses.replace(state, guessed=...)` would
do the copy; spelling the constructor out keeps all three fields visible at
this size. An OO version stores `status` and must flip it at exactly the
right moment — an ordering obligation that simply doesn't exist here.

**The drilled composition root.** `main()` owns everything effectful: it picks the
secret with `random.choice(WORDS)`, reads each guess with `input()`, filters junk
lines itself, and catches the core's `ValueError` to report repeats. The state is transparent: the shell reads
`state.max_wrong` straight off the value, where an OO shell would talk to an
encapsulated machine. The important line is `state = guess(...)`. The shell must
retain the returned value and explicitly thread it into the next turn.

## Shapes chosen and rejected

- **Functional core (chosen)** over an **OO state machine**. An OO version
  stores `status` and must flip it at exactly the right moment inside `guess`.
  Here status is derived on demand, so no field can disagree with the guesses.
- **The shell picks the word with `random.choice`.** Taking the secret from the
  first stdin line instead would let one exact transcript cover Python, C, and
  Rust alike, but it teaches porting byte for byte rather than how each language
  writes Hangman: each implementation picks from its own word list with its own
  random source. The core doesn't care, because `new_game` is handed the secret;
  only the shell's source of it would change.
- **A word list with two different letters per word.** A one-letter word such as
  `aaa` would let a single guess win; ruling it out means a game is still going
  when its first guess is repeated.
- **Line-by-line reading.** The shell reads one line per turn rather than all of
  stdin at once, so a person can play at a terminal. Reading everything up front
  would wait for end of input before printing the first status line.

## Scales up to

The functional core / imperative shell split is the skeleton of most larger
programs. The nearest here is Game of Life (`corpus/medium/Game-of-Life`): a pure
`step`, with all I/O in `main`. The turn loop is a small version of a Lisp REPL,
which reads stdin line by line in one persistent session and ends at end of input.
It threads an environment where this loop threads a `HangmanState`.
