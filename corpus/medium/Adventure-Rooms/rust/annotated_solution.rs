//! Adventure Rooms: whole program.

// From Python:
// 1. Python's `VERBS` dict becomes a `const` array of `(name, handler)` pairs,
//    each handler a function pointer of one type (Rust Book 20.4, "Function
//    Pointers"; 20.3 for the `Handler` alias). [dispatch]
// 2. Python's handlers return `(state, output)`. Here they change the state
//    through `&mut State` and return only the text (Rust Book 4.2). [borrowing]
// 3. Python's world dicts become `const` data: an array of `Room`s whose exits
//    and items are `&'static` slices (Rust Book 10.3, "The Static Lifetime").
//    [data]
// 4. Python's `execute` raises `ValueError` for an unknown verb. Here it returns
//    `Err`, and `main` prints either side the same way (Rust Book 9.2, 19.3).
//    [errors]
// 5. Python's `input()` loop becomes `io::stdin().lines()`, and `str.strip()`
//    becomes `trim()`, which removes Unicode whitespace much as Python's does.
//    [text]

// `io::stdin().lines()` yields each line without its line end.
use std::io;

const DIRECTIONS: [&str; 4] = ["north", "south", "east", "west"];

// One row of SPEC §1's table. Exits and items are borrowed from the program's
// own constants for its whole run, hence `&'static`.
struct Room {
    name: &'static str,
    description: &'static str,
    exits: &'static [(&'static str, &'static str)],
    items: &'static [&'static str],
}

const ROOMS: [Room; 5] = [
    Room {
        name: "hall",
        description: "a dusty entrance hall",
        exits: &[("north", "library"), ("west", "garden")],
        items: &["lamp"],
    },
    Room {
        name: "library",
        description: "a book-lined library",
        exits: &[("south", "hall"), ("north", "attic"), ("west", "cellar")],
        items: &["book"],
    },
    Room {
        name: "cellar",
        description: "a damp stone cellar",
        exits: &[("east", "library")],
        items: &["key"],
    },
    Room {
        name: "attic",
        description: "a cramped attic",
        exits: &[("south", "library")],
        items: &[],
    },
    Room {
        name: "garden",
        description: "an overgrown garden",
        exits: &[("east", "hall")],
        items: &["rose", "spade"],
    },
];

// Only what play changes: the current room, the inventory, each room's items.
struct State {
    room: usize,
    inventory: Vec<&'static str>,
    items: Vec<Vec<&'static str>>,
    over: bool,
}

fn new_game() -> State {
    State {
        room: 0,
        inventory: Vec::new(),
        items: ROOMS.iter().map(|room| room.items.to_vec()).collect(),
        over: false,
    }
}

// `?` on an `Option` returns `None` when the room has no such exit (Rust Book
// 9.2, "Where to Use the ? Operator").
fn exit(room: usize, direction: &str) -> Option<usize> {
    let (_, to) = ROOMS[room]
        .exits
        .iter()
        .find(|(way, _)| *way == direction)?;
    ROOMS.iter().position(|room| room.name == *to)
}

fn look(state: &State) -> String {
    let room = &ROOMS[state.room];
    // Walking `DIRECTIONS` puts the exits in north, south, east, west order,
    // whatever order the data lists them in.
    let exits: Vec<&str> = DIRECTIONS
        .into_iter()
        .filter(|&direction| exit(state.room, direction).is_some())
        .collect();
    let mut text = format!(
        "You are in {}.\nExits: {}.",
        room.description,
        exits.join(", ")
    );
    let items = &state.items[state.room];
    if !items.is_empty() {
        text += &format!("\nYou see: {}.", items.join(", "));
    }
    text
}

// `fn` is the type of a function pointer: every handler below has this type,
// so they can share one array.
type Handler = fn(&mut State, &str) -> String;

fn do_look(state: &mut State, _arg: &str) -> String {
    look(state)
}

fn do_go(state: &mut State, arg: &str) -> String {
    if arg.is_empty() {
        return "Go where?".to_string();
    }
    let Some(to) = exit(state.room, arg) else {
        return "You can't go that way.".to_string();
    };
    state.room = to;
    look(state)
}

fn do_take(state: &mut State, arg: &str) -> String {
    if arg.is_empty() {
        return "Take what?".to_string();
    }
    let here = &mut state.items[state.room];
    let Some(index) = here.iter().position(|&item| item == arg) else {
        return format!("There is no {arg} here.");
    };
    // `Vec::remove` returns the item it takes out (Rust Book 8.1).
    state.inventory.push(here.remove(index));
    "Taken.".to_string()
}

fn do_drop(state: &mut State, arg: &str) -> String {
    if arg.is_empty() {
        return "Drop what?".to_string();
    }
    let Some(index) = state.inventory.iter().position(|&item| item == arg) else {
        return format!("You are not carrying {arg}.");
    };
    let item = state.inventory.remove(index);
    state.items[state.room].push(item);
    "Dropped.".to_string()
}

fn do_inventory(state: &mut State, _arg: &str) -> String {
    if state.inventory.is_empty() {
        return "You are carrying nothing.".to_string();
    }
    format!("You are carrying: {}.", state.inventory.join(", "))
}

fn do_quit(state: &mut State, _arg: &str) -> String {
    state.over = true;
    "Goodbye.".to_string()
}

// The table is fixed at compile time. Adding a verb is one more entry;
// `execute` doesn't change.
const VERBS: [(&str, Handler); 6] = [
    ("look", do_look),
    ("go", do_go),
    ("take", do_take),
    ("drop", do_drop),
    ("inventory", do_inventory),
    ("quit", do_quit),
];

fn execute(state: &mut State, line: &str) -> Result<String, String> {
    if state.over {
        return Err("the game is over".to_string());
    }
    let line = line.trim();
    // Python's `partition(" ")`: split at the first space, or the whole line
    // and an empty argument.
    let (verb, arg) = line.split_once(' ').unwrap_or((line, ""));
    let Some((_, handler)) = VERBS.iter().find(|(name, _)| *name == verb) else {
        return Err(format!("unknown verb: {verb}"));
    };
    Ok(handler(state, arg.trim()))
}

fn main() {
    let mut state = new_game();
    println!("{}", look(&state));
    // Python's `input()` loop: `lines()` drops each line end, and
    // `map_while(Result::ok)` stops at a read error, such as a line that isn't
    // UTF-8, as end of input does.
    for line in io::stdin().lines().map_while(Result::ok) {
        match execute(&mut state, &line) {
            // Both arms bind a `String` named `output`, so one `|` pattern prints
            // either (Rust Book 19.3, "Matching Multiple Patterns").
            Ok(output) | Err(output) => println!("{output}"),
        }
        // After `quit`, no later line is read.
        if state.over {
            break;
        }
    }
}
