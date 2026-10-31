//! Hangman: whole program.
// From Python:
// 1. Python's frozen dataclass becomes a `Game` that is never changed in place:
//    `guess` borrows it as `&self`, which can't modify it, and returns a changed
//    clone. [mutation]
// 2. Python's status strings become `enum Status`, so a misspelled status is a
//    compile error rather than a silent mismatch (Rust Book 6.1). [types]
// 3. Python raises `ValueError` for a repeated guess. `guess` returns
//    `Result<Game, String>`, and `main` matches on it (Rust Book 9.2). [errors]
// 4. Python's `random.choice(WORDS)` becomes `WORDS.choose(&mut rand::rng())`:
//    std has no random numbers, so the `rand` crate supplies them (Rust Book 2,
//    "Generating a Random Number"). [library]
// 5. Python's `input()` raising `EOFError` becomes `lines.next()` returning
//    `None`; a line that isn't UTF-8 comes back as `Some(Err(_))`. [io]
// 6. Python's `main` checks for one letter inside its loop. Here `letter_of`
//    returns `Option`, and `let…else` handles the absent case first (Rust Book
//    6.3). [absence]

// Python's `frozenset` of guesses, as an ordered set (std: BTreeSet).
use std::collections::BTreeSet;
use std::io;

// The trait that gives a slice `choose`; it must be in scope to call it.
use rand::seq::IndexedRandom;

const MAX_WRONG: usize = 6;
// An array of string slices that live for the whole program (`&'static str`).
const WORDS: [&str; 8] = [
    "banana", "jigsaw", "kayak", "oxygen", "puzzle", "python", "rhythm", "wizard",
];

// `Clone` lets `guess` copy the game. Python never copies: it builds a new
// frozen value.
#[derive(Clone)]
struct Game {
    secret: String,
    guessed: BTreeSet<char>,
}

// `PartialEq` allows `game.status() == Status::Playing`; `Debug` lets a status
// print with `{:?}`, as a failing `assert_eq!` needs.
#[derive(Debug, PartialEq)]
enum Status {
    Playing,
    Won,
    Lost,
}

impl Game {
    fn new(secret: &str) -> Game {
        Game {
            secret: secret.to_string(),
            guessed: BTreeSet::new(),
        }
    }

    fn wrong_count(&self) -> usize {
        self.guessed
            .iter()
            // Python's `state.guessed - set(state.secret)`, counted. The closure gets
            // `&&char`, and the pattern `&&ch` unwraps both references (Rust Book 19.1).
            .filter(|&&ch| !self.secret.contains(ch))
            .count()
    }

    fn masked(&self) -> String {
        self.secret
            .chars()
            .map(|ch| if self.guessed.contains(&ch) { ch } else { '_' })
            .collect()
    }

    fn status(&self) -> Status {
        if self.secret.chars().all(|ch| self.guessed.contains(&ch)) {
            Status::Won
        } else if self.wrong_count() >= MAX_WRONG {
            Status::Lost
        } else {
            Status::Playing
        }
    }

    // Python's `guess` builds a new state. Here `self` is borrowed, and a changed
    // clone comes back in `Ok`.
    fn guess(&self, letter: char) -> Result<Game, String> {
        if self.status() != Status::Playing {
            return Err("the game is over".to_string());
        }
        if self.guessed.contains(&letter) {
            return Err(format!("already guessed: {letter}"));
        }
        let mut next = self.clone();
        next.guessed.insert(letter);
        Ok(next)
    }
}

fn letter_of(line: &str) -> Option<char> {
    let mut chars = line.trim().chars();
    // One letter means a first `char` and no second: Python's `len(letter) == 1`
    // without counting the whole line.
    match (chars.next(), chars.next()) {
        (Some(ch), None) if ch.is_ascii_alphabetic() => Some(ch.to_ascii_lowercase()),
        _ => None,
    }
}

fn main() {
    // `rand::rng()` is a generator seeded from the operating system, like
    // Python's `random`. `choose` returns `None` only for an empty slice.
    let secret = WORDS.choose(&mut rand::rng()).expect("WORDS is not empty");
    let mut game = Game::new(secret);
    let mut lines = io::stdin().lines();
    while game.status() == Status::Playing {
        println!(
            "{}  wrong: {}/{MAX_WRONG}",
            game.masked(),
            game.wrong_count()
        );
        // End of input, or a line that isn't UTF-8, ends the game.
        let Some(Ok(line)) = lines.next() else {
            println!("you quit! the word was {secret}");
            return;
        };
        let Some(letter) = letter_of(&line) else {
            println!("one letter a-z, please");
            continue;
        };
        match game.guess(letter) {
            // Python's `state = guess(state, letter)`.
            Ok(next) => game = next,
            Err(message) => println!("{message}"),
        }
    }
    let outcome = if game.status() == Status::Won {
        "won"
    } else {
        "lost"
    };
    println!("you {outcome}! the word was {secret}");
}
