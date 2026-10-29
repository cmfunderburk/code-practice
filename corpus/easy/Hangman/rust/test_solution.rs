use super::*;

fn guessed(game: &Game, letters: &str) -> Game {
    letters.chars().fold(game.clone(), |game, letter| {
        game.guess(letter).expect("a new guess in a live game")
    })
}

#[test]
fn a_hit_reveals_every_occurrence_and_a_miss_counts() {
    let game = Game::new("banana");
    assert_eq!(
        (game.masked(), game.status()),
        ("______".to_string(), Status::Playing)
    );
    let game = guessed(&game, "a");
    assert_eq!(
        (game.masked(), game.wrong_count()),
        ("_a_a_a".to_string(), 0)
    );
    let game = guessed(&game, "xn");
    assert_eq!(
        (game.masked(), game.wrong_count()),
        ("_anana".to_string(), 1)
    );
    let game = guessed(&game, "b");
    assert_eq!(
        (game.masked(), game.status()),
        ("banana".to_string(), Status::Won)
    );
}

#[test]
fn the_sixth_miss_loses() {
    let game = guessed(&Game::new("banana"), "cdefg");
    assert_eq!((game.wrong_count(), game.status()), (5, Status::Playing));
    let game = guessed(&game, "h");
    assert_eq!((game.wrong_count(), game.status()), (6, Status::Lost));
}

#[test]
fn a_repeated_guess_is_refused_hit_or_miss() {
    let game = guessed(&Game::new("banana"), "az");
    assert!(game.guess('a').is_err());
    assert!(game.guess('z').is_err());
}

#[test]
fn a_finished_game_refuses_every_guess() {
    assert!(guessed(&Game::new("io"), "io").guess('z').is_err());
    assert!(guessed(&Game::new("io"), "abcdef").guess('i').is_err());
}

#[test]
fn guessing_leaves_the_old_game_alone() {
    let before = Game::new("banana");
    let after = guessed(&before, "a");
    assert_eq!(
        (before.masked(), after.masked()),
        ("______".to_string(), "_a_a_a".to_string())
    );
}

#[test]
fn a_guess_line_is_one_ascii_letter() {
    assert_eq!(letter_of("q"), Some('q'));
    assert_eq!(letter_of("Q"), Some('q'));
    assert_eq!(letter_of(" q "), Some('q'));
    for line in ["", "ab", "7", "é", "?"] {
        assert_eq!(letter_of(line), None, "{line:?}");
    }
}

#[test]
fn every_word_is_lowercase_with_two_different_letters() {
    for word in WORDS {
        assert!(word.bytes().all(|b| b.is_ascii_lowercase()), "{word}");
        assert!(word.chars().any(|ch| !word.starts_with(ch)), "{word}");
    }
}
