## How it works

The whole state of a Hangman game is three values: the secret word, the set of
letters guessed so far, and the number of misses allowed. `HangmanState` is a
frozen dataclass holding exactly those three. Everything else the player sees is
computed from them when it is needed:
- `masked` writes the secret with `_` for each letter not yet guessed;
- `wrong_count` counts the guessed letters that are not in the secret;
- `status` returns `"won"` once every letter of the secret is guessed, `"lost"`
  once the misses reach `max_wrong`, and `"playing"` otherwise. It checks for a win
  first.

`guess` refuses a guess after the game has ended, or a letter already guessed, by
raising `ValueError`. Otherwise it returns a new state with the letter added, and
leaves the state it was given unchanged.

Worked check: `"banana"` after guesses a, x, n → masked `"_anana"`, one wrong,
still playing; then b → `"banana"`, won.

**Complexity.** `masked`, `wrong_count`, and `status` each take time $O(n)$ for a
secret of $n$ letters (at most 26 letters can be guessed). Each state holds at
most 26 guessed letters.

**Checking `guess`.** Because `guess` returns a new value instead of changing the
one it was given, a test can call it twice on the same state and compare.
`test_guess_leaves_its_input_alone_and_gives_the_same_result_twice` does exactly
that: both calls must return equal states, and the original state must still have
nothing guessed.

## `main`

`main()` does everything that touches the outside world. It picks the secret with
`random.choice(WORDS)` and creates the first state with `new_game`. Each turn it
prints `<mask>  wrong: <misses>/<max_wrong>`, reading `max_wrong` straight from the
state, then reads a line with `input()`, removes surrounding spaces, and converts
it to lowercase. A line that is not one letter `a`–`z` gets
`one letter a-z, please`. A letter goes to `guess`; if `guess` raises
`ValueError`, `main` prints the message and keeps the old state. At end of input
it prints `you quit! the word was <secret>` and returns. When the game ends it
prints `you won! the word was <secret>` or `you lost! the word was <secret>`.

The most important line is `state = guess(state, letter)`. `guess` changes
nothing, so if `main` called it without keeping the result, every guess would be
thrown away and the game would never move on.

## Design choices

- **Computing the status instead of storing it.** A `status` field would be a
  second record of what `guessed` already decides, and `guess` would have to
  update it at exactly the right moment, after adding the letter. Because the
  function `status` computes the answer from the fields each time, nothing can
  disagree with the guesses.
- **A new state for every guess.** An object that added letters to its own set
  would do the same job with one object. With a frozen value, `main` must assign
  the result of every `guess`, but every old state stays valid, so a test can
  call `guess` twice on the same state and compare the results. `guess` writes
  out the constructor call,
  `HangmanState(state.secret, state.guessed | {letter}, state.max_wrong)`.
  `dataclasses.replace(state, guessed=...)` would make the same copy; with only
  three fields, writing them out keeps all three in view.
- **Only `main` picks the word.** `main` picks it with `random.choice` and passes
  it to `new_game`, so every other function can be tested with a known word and no
  randomness. The tests of `main` replace `random.choice` with a function that
  returns a chosen word. Reading the word from input instead would let one exact
  transcript test the whole program, but nobody could play it alone.
- **Words with at least two different letters.** A word such as `aaa` would let a
  single guess win. Ruling it out lets the shared tests check that one letter
  guessed many times never ends a game.
- **Reading one line at a time.** `main` reads one line per turn rather than all
  of stdin at once, so a person can play at a terminal. Reading everything first
  would mean no guess got an answer until input ended.

## Where this shows up again

Splitting a program into functions that only compute (here `new_game`, `guess`,
`masked`, `wrong_count`, and `status`) and one function that does all the input,
output, and random choices (here `main`) is a common design. It is often called
*functional core, imperative shell*. Two larger examples:

- A Game of Life program can compute each generation with a function that takes a
  set of live cells and returns a new set, and keep all file reading, terminal
  output, and waiting between frames in `main`. Then every rule can be tested by
  comparing sets, with no terminal involved.
- An interactive interpreter, such as the `>>>` prompt of `python3`, has a REPL, a
  read-evaluate-print loop, that reads one line at a time in one session and stops
  at end of input, as `main` does here. It carries the definitions made so far from
  one line to the next, where this loop carries a `HangmanState`.
