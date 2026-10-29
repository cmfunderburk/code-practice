use super::*;

const HALL: &str = "You are in a dusty entrance hall.\nExits: north, west.\nYou see: lamp.";

fn run(state: &mut State, lines: &[&str]) -> Vec<String> {
    lines
        .iter()
        .map(|line| execute(state, line).unwrap())
        .collect()
}

fn room(state: &State) -> &'static str {
    ROOMS[state.room].name
}

#[test]
fn the_game_opens_in_the_hall() {
    let state = new_game();
    assert_eq!(look(&state), HALL);
    assert!(state.inventory.is_empty() && !state.over);
}

#[test]
fn every_exit_leads_where_the_map_says() {
    let mut state = new_game();
    for (way, to) in [
        ("west", "garden"),
        ("east", "hall"),
        ("north", "library"),
        ("west", "cellar"),
        ("east", "library"),
        ("north", "attic"),
        ("south", "library"),
        ("south", "hall"),
    ] {
        execute(&mut state, &format!("go {way}")).unwrap();
        assert_eq!(room(&state), to);
    }
}

#[test]
fn look_lists_exits_in_direction_order_and_items_only_when_present() {
    let mut state = new_game();
    let outs = run(&mut state, &["go north", "go west", "take key", "look"]);
    assert_eq!(
        outs[0],
        "You are in a book-lined library.\nExits: north, south, west.\nYou see: book."
    );
    assert_eq!(outs[3], "You are in a damp stone cellar.\nExits: east.");
}

#[test]
fn a_refused_go_stays_put() {
    let mut state = new_game();
    let outs = run(&mut state, &["go south", "go up", "go", "go North"]);
    assert_eq!(
        outs,
        [
            "You can't go that way.",
            "You can't go that way.",
            "Go where?",
            "You can't go that way."
        ]
    );
    assert_eq!(room(&state), "hall");
}

#[test]
fn take_and_drop_move_items_in_order() {
    let mut state = new_game();
    let outs = run(
        &mut state,
        &[
            "take lamp",
            "go west",
            "take spade",
            "take rose",
            "drop spade",
        ],
    );
    assert_eq!(outs[0], "Taken.");
    assert_eq!(outs[4], "Dropped.");
    assert_eq!(state.inventory, ["lamp", "rose"]);
    assert_eq!(state.items[4], ["spade"]);
    assert_eq!(
        execute(&mut state, "inventory").unwrap(),
        "You are carrying: lamp, rose."
    );
}

#[test]
fn take_and_drop_refusals_change_nothing() {
    let mut state = new_game();
    let outs = run(&mut state, &["take", "take sword", "drop", "drop lamp"]);
    assert_eq!(
        outs,
        [
            "Take what?",
            "There is no sword here.",
            "Drop what?",
            "You are not carrying lamp."
        ]
    );
    assert!(state.inventory.is_empty());
    assert_eq!(state.items[0], ["lamp"]);
}

#[test]
fn surrounding_whitespace_is_trimmed() {
    let mut state = new_game();
    run(&mut state, &["  go   north ", "\ttake book\r"]);
    assert_eq!(room(&state), "library");
    assert_eq!(state.inventory, ["book"]);
}

#[test]
fn an_unknown_verb_is_an_err_and_changes_nothing() {
    let mut state = new_game();
    assert_eq!(
        execute(&mut state, "dance"),
        Err("unknown verb: dance".to_string())
    );
    assert!(execute(&mut state, "").is_err());
    assert!(execute(&mut state, "LOOK").is_err());
    assert_eq!(room(&state), "hall");
}

#[test]
fn quit_ends_the_game() {
    let mut state = new_game();
    assert_eq!(execute(&mut state, "quit").unwrap(), "Goodbye.");
    assert!(state.over);
    assert!(execute(&mut state, "look").is_err());
}
