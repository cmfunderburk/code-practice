# Adventure Rooms

Run a five-room text adventure over stdin and stdout, one command per line. The
player starts in the hall with nothing.

| Room | Exits | Items at the start |
| --- | --- | --- |
| hall | north → library, west → garden | `lamp` |
| library | north → attic, south → hall, west → cellar | `book` |
| cellar | east → library | `key` |
| attic | south → library | none |
| garden | east → hall | `rose`, `spade` |

- On start, describe the hall. Then answer each line until `quit` or the end of
  input, which ends the session without another word.
- A line is a verb and an optional argument, split at the first space after
  surrounding whitespace is trimmed; the argument is trimmed too.
- The verbs are `look`, `go <direction>`, `take <item>`, `drop <item>`,
  `inventory`, and `quit`. A taken item leaves the room for the end of the
  inventory; a dropped item goes on the end of the room's list.
- A room's description names the room, lists its exits in the order north,
  south, east, west, and lists the items it holds. `inventory` lists what you
  carry, in order.
- A command that can't be carried out (no such exit, item, or verb) is answered
  and changes nothing.

The world and its rules are the program's `SPEC.md`. Descriptions and wording
are each implementation's own; SPEC §5 fixes little more than the room and item
names an answer contains.

## A session

```text
You are in a dusty entrance hall.
Exits: north, west.
You see: lamp.
> take lamp
Taken.
> go north
You are in a book-lined library.
Exits: north, south, west.
You see: book.
> dance
unknown verb: dance
> inventory
You are carrying: lamp.
> quit
Goodbye.
```

(`> ` marks the user's lines.)

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
struct Room {
    name: &'static str,
    description: &'static str,
    exits: &'static [(&'static str, &'static str)],
    items: &'static [&'static str],
}
const ROOMS: [Room; 5]; // hall, library, cellar, attic, garden, in that order

struct State {
    room: usize,                   // an index into ROOMS
    inventory: Vec<&'static str>,
    items: Vec<Vec<&'static str>>, // each room's items, indexed like ROOMS
    over: bool,
}

fn new_game() -> State
fn look(state: &State) -> String
fn execute(state: &mut State, line: &str) -> Result<String, String>
```

`execute` runs one line and returns the answer to print, or an `Err` for an
unknown verb or any line after `quit`, with the state unchanged.

Differences from the Python implementation:
- Handlers change the state through `&mut State` and return only the text,
  where Python returns `(state, output)`.
- The verb table is fixed at compile time; nothing registers a verb at run time.
