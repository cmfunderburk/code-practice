# Hangman

Play Hangman at a terminal, on stdin and stdout. The program picks a secret word
at random from its own built-in list (lowercase `a`–`z`, each word with at least
two different letters). The player guesses one letter per line, with a budget
of 6 wrong guesses: the game is won when every letter of the secret is guessed,
and lost on the sixth miss.

Playing:
- Pick the word with the language's ordinary random source.
- Before each guess show the secret with unguessed letters hidden, and the
  misses used out of 6.
- A guess is one letter; uppercase counts as lowercase. Answer any other line
  with a reminder of what a guess is; it costs nothing.
- A letter already guessed is answered and costs nothing.
- When the game ends, print one line containing `won` or `lost` that ends with
  the secret word, and stop. If input ends first, stop.

The game is the program's `SPEC.md`. Wording is yours; only the ending line is
fixed.

## A session

```text
______  wrong: 0/6
> e
______  wrong: 1/6
> I
_i____  wrong: 1/6
> i
already guessed: i
_i____  wrong: 1/6
> 7
one letter a-z, please
_i____  wrong: 1/6
```

(`> ` marks the player's lines.)

## C contract

A whole program, `int main(void)`, with this core above it:

```c
constexpr int MAX_WRONG = 6;
constexpr size_t SECRET_MAX = 32;

typedef struct {
    const char *secret; // lowercase a-z, at most SECRET_MAX letters
    bool guessed[26];
} Game;

static Game new_game(const char *secret);
static int wrong_count(const Game *game);
static bool won(const Game *game);
static bool playing(const Game *game);
static void masked(const Game *game, char mask[static SECRET_MAX + 1]);
static bool guess(Game game, char letter, Game *next); // letter a-z
```

`guess` writes the next game through `next` and returns `true`, or returns
`false` for a letter already guessed or a finished game. The words are
`WORDS`, an array of `WORD_COUNT` string literals.

Differences from the Python version:
- The budget is a constant, not a field, and status is two predicates, `won`
  and `playing`, instead of a string.
- `masked` fills the caller's array instead of returning a string.
- `guess` reports a refused guess by returning `false`, not by raising.
