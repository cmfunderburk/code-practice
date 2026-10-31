# Hangman — Functional Core

The rules of Hangman, as a set of functions. The secret is a word of lowercase
letters `a`–`z`, and the player guesses one letter at a time. A guessed letter that
is in the secret reveals every place it occurs; a letter that is not counts as a
miss. The player may make **6 wrong guesses** (a different number can be set when
the game is created), and reaching that many misses loses the game. `masked` shows
the secret with `_` in place of each letter not yet guessed, and the game is won
when every letter of the secret has been guessed. Guessing a letter that was
**already guessed**, whether it was a hit or a miss, raises `ValueError`, and so
does guessing after the game is over: a move the rules don't allow is refused, not
ignored.

## Examples

```
secret "banana": guess a -> masked "_a_a_a" (hit)
                 guess x -> wrong count 1  (miss)
                 guess n, b -> masked "banana", status "won"
6 misses -> status "lost"; any further guess raises ValueError
```

Constraints: the secret is a nonempty word of lowercase letters `a`–`z`; each
guess is one lowercase letter.

## Functional Core

The core is an immutable state value, and functions over it that only compute:
they change nothing and do no input or output.

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

`guess` returns a new state and never changes the one it is given. `masked`,
`wrong_count`, and `status` compute their answers from the state each time they
are called; none of them is stored. These functions are handed letters; only
`main` reads lines with `input()`.

Around the core sit the imports, `WORDS`, and `main()` with its
`if __name__ == "__main__"` call. `main()` picks the secret with
`random.choice(WORDS)`, creates the first state, and passes each state returned
by `guess` on to the next turn. Each turn, it prints
`<mask>  wrong: <misses>/<max_wrong>`, then reads a line with `input()`, removing
surrounding spaces and converting it to lowercase; at end of input it prints
`you quit! the word was <secret>` and returns. A line that is not one letter
`a`-`z` gets `one letter a-z, please`, and a `ValueError` from `guess` is printed
as is. The game ends by printing `you <status>! the word was <secret>`. The full
game is in `SPEC.md`.
