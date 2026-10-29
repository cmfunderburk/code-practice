# Hangman — Functional Core

The guessing engine for Hangman. The secret is a lowercase `a-z` word; the
player guesses one letter at a time. A guessed letter in the secret reveals
every occurrence; a miss counts toward the budget of **6 wrong guesses**
(configurable), and reaching it loses. `masked` renders the secret with `_`
for each unrevealed letter; the game is won when every letter of the secret
has been guessed. Guessing a letter that was **already guessed** — hit or
miss — raises `ValueError`, as does guessing after the game is over:
illegal transitions are rejected, not ignored.

## Examples

```
secret "banana": guess a -> masked "_a_a_a" (hit)
                 guess x -> wrong count 1  (miss)
                 guess n, b -> masked "banana", status "won"
6 misses -> status "lost"; any further guess raises ValueError
```

Constraints: the secret is nonempty lowercase a-z; guesses are single
lowercase letters.

## Functional Core

The core is an immutable state value and pure functions over it:

```python
@dataclass(frozen=True)
class HangmanState:
    secret: str
    guessed: frozenset[str]
    max_wrong: int

def new_game(secret: str, max_wrong: int = 6) -> HangmanState
def guess(state: HangmanState, letter: str) -> HangmanState   # raises ValueError
def masked(state: HangmanState) -> str
def wrong_count(state: HangmanState) -> int
def status(state: HangmanState) -> str    # "playing" | "won" | "lost"
```

`guess` returns a NEW state and never mutates its input; `masked`,
`wrong_count`, and `status` are derived views, stored nowhere. The core is
handed letters; only the shell loops on `input()`.

Around the core sit the imports, `WORDS`, and the `main()` composition root with
its guarded call. `main()` picks the secret with `random.choice(WORDS)`, creates
one immutable state, and threads each state returned by `guess` into the next
turn. Each turn, it prints
`<mask>  wrong: <misses>/<max_wrong>`, then reads a line with `input()`, stripped
and lowercased; at end of input it prints `you quit! the word was <secret>` and
returns. A line that is not one letter `a`-`z` gets `one letter a-z, please`, and
the core's `ValueError` is printed as is. The game ends by printing
`you <status>! the word was <secret>`. The game itself is `SPEC.md`.
