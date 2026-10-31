# Adventure Rooms — Verb Dispatch

A small text adventure: five rooms, a few items, and a player who walks between
the rooms, picks items up, and puts them down. One function,
`execute(state, line) -> (state, output)`, runs each command the player types
against a fixed world:

- `go <dir>` moves through an exit (`north`, `south`, `east`, or `west`) and
  returns the new room's description; `look` describes the current room again;
- `take <item>` and `drop <item>` move an item between the room and the player's
  inventory; `inventory` lists what the player carries, in the order the items
  were taken;
- `quit` answers `Goodbye.` and ends the game.

When the game refuses a command, the refusal is an ordinary answer:
`You can't go that way.`, `There is no sword here.`, `You are not carrying lamp.`,
`Go where?`. But an unknown verb raises `ValueError`, and so does any command
after `quit`, because the game is over. A room's description has a fixed form: the
line `You are in <description>.`, an `Exits:` line listing the directions in the
order north, south, east, west, and a `You see:` line only when the room holds
items.

## Examples

```
look        -> You are in a dusty entrance hall.
               Exits: north, west.
               You see: lamp.
take lamp   -> Taken.
go north    -> (the library's description)
go up       -> You can't go that way.
inventory   -> You are carrying: lamp.
quit        -> Goodbye.          (anything after this raises ValueError)
```

The world: hall (lamp; north→library, west→garden), library (book;
south→hall, north→attic, west→cellar), cellar (key; east→library),
attic (empty; south→library), garden (rose, spade; east→hall). The game
starts in the hall.

## Verb Dispatch

`execute` uses a dispatch table: `VERBS`, a dictionary from each command word to
the function that handles it.

```python
def _look(state: State) -> str
# handlers: _do_look, _do_go, _do_take, _do_drop, _do_inventory, _do_quit
#   each (state, arg) -> tuple[State, str]
VERBS: dict[str, Callable[[State, str], tuple[State, str]]]
def execute(state: State, line: str) -> tuple[State, str]
```

`execute` refuses any command once the game is over, splits off the verb, and
looks it up in `VERBS` **each time it is called**, so a brand-new verb added to
the table while the program runs is found like the rest. Each handler does all of
one command's work, including its refusals (`Go where?`).

Around the handlers, `VERBS`, and `execute` sit the world constants, `new_game`,
and `main()`. `main()` creates one state, prints its description, then reads
lines with `input()` until the state is over, stopping without printing anything
when `input()` raises `EOFError` at end of input. It hands each line to `execute`
unchanged, keeps the state `execute` returns, and prints the output. When an
unknown verb raises `ValueError`, `main` prints the message and keeps its old
state. The world and its rules are `SPEC.md`.
