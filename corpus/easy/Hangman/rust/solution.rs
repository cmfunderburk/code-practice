//! Hangman: whole program.

use std::collections::BTreeSet;
use std::io;

use rand::seq::IndexedRandom;

const MAX_WRONG: usize = 6;
const WORDS: [&str; 8] = [
    "banana", "jigsaw", "kayak", "oxygen", "puzzle", "python", "rhythm", "wizard",
];

#[derive(Clone)]
struct Game {
    secret: String,
    guessed: BTreeSet<char>,
}

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
    match (chars.next(), chars.next()) {
        (Some(ch), None) if ch.is_ascii_alphabetic() => Some(ch.to_ascii_lowercase()),
        _ => None,
    }
}

fn main() {
    let secret = WORDS.choose(&mut rand::rng()).expect("WORDS is not empty");
    let mut game = Game::new(secret);
    let mut lines = io::stdin().lines();
    while game.status() == Status::Playing {
        println!(
            "{}  wrong: {}/{MAX_WRONG}",
            game.masked(),
            game.wrong_count()
        );
        let Some(Ok(line)) = lines.next() else {
            println!("you quit! the word was {secret}");
            return;
        };
        let Some(letter) = letter_of(&line) else {
            println!("one letter a-z, please");
            continue;
        };
        match game.guess(letter) {
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
