# Adventure Rooms — Verb Dispatch

A tiny text adventure: five rooms, a handful of items, and a player who
walks, takes, and drops. The engine is one function,
`execute(state, line) -> (state, output)`, driving a fixed world:

- `go <dir>` moves through an exit (`north`/`south`/`east`/`west`) and
  returns the new room's description; `look` re-describes the current
  room;
- `take <item>` / `drop <item>` move an item between the room and your
  inventory; `inventory` lists what you carry, in acquisition order;
- `quit` says `Goodbye.` and ends the game.

In-fiction failures are ordinary outputs — `You can't go that way.`,
`There is no sword here.`, `You are not carrying lamp.`, `Go where?` —
but an unknown verb raises `ValueError`, and ANY command after `quit`
raises `ValueError`: the game is over. `look` output is pinned: the
description line, an `Exits:` line listing directions in
north/south/east/west order, and a `You see:` line only when items are
present.

## Examples

```
look        -> You are in a dusty entrance hall.
               Exits: north, west.
               You see: lamp.
take lamp   -> Taken.
go north    -> (the library's look text)
go up       -> You can't go that way.
inventory   -> You are carrying: lamp.
quit        -> Goodbye.          (anything after this raises ValueError)
```

The world: hall (lamp; north→library, west→garden), library (book;
south→hall, north→attic, west→cellar), cellar (key; east→library),
attic (empty; south→library), garden (rose, spade; east→hall). The game
starts in the hall.

## Verb Dispatch

The engine is a dispatch table:

```python
def _look(state: State) -> str
# handlers: _do_look, _do_go, _do_take, _do_drop, _do_inventory, _do_quit
#   each (state, arg) -> tuple[State, str]
VERBS: dict[str, Callable[[State, str], tuple[State, str]]]
def execute(state: State, line: str) -> tuple[State, str]
```

`execute` guards the terminal state, splits the verb, and looks it up
in `VERBS` **at call time**, so a brand-new verb registered into the
table at run time is found like the rest. Each handler owns one
verb's whole behavior, prompts (`Go where?`) included.

Around the verb-dispatch engine sits the representative `main()` composition
root. `main()` creates one state, prints its initial description, then reads
lines with `input()` until the state is over,
stopping without writing anything when `input()` raises `EOFError` at end of
input. It hands each line to `execute` unchanged, threads each successful
`(state, output)` result, and prints the output. When an unknown verb raises
before mutation, it prints the message and keeps the prior binding. Catching an
exception cannot roll back a dynamically registered handler that mutates and then
raises. The world constants and `new_game` build the fixed world and its
starting state. The world and its rules are `SPEC.md`.
