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

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
const MAX_WRONG: usize = 6;
const WORDS: [&str; 8] = [/* lowercase words */];

#[derive(Clone)]
struct Game {
    secret: String,
    guessed: BTreeSet<char>,
}

#[derive(Debug, PartialEq)]
enum Status { Playing, Won, Lost }

impl Game {
    fn new(secret: &str) -> Game
    fn wrong_count(&self) -> usize
    fn masked(&self) -> String
    fn status(&self) -> Status
    fn guess(&self, letter: char) -> Result<Game, String>
}

fn letter_of(line: &str) -> Option<char> // a guess line's lowercase letter
```

`guess` returns `Err` for a letter already guessed or a finished game. The word
comes from the `rand` crate (`IndexedRandom::choose`), the program's one
dependency.

Differences from the Python version:
- The budget is a constant, not a field, and `status` returns an enum, not a
  string.
- `guess` is a method that borrows the game and returns `Result`, not a
  `ValueError`.
- Turning a line into a letter is its own function, `letter_of`.
