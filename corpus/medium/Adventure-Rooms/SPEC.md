# Adventure Rooms — SPEC

This document specifies a small text adventure: five rooms, a few items, and a
player who walks between the rooms, picks items up, and puts them down. There are
three versions of it, in Python, C, and Rust, and each is written the way a
programmer in that language would usually write it. All three must agree on the
**world** (§1) and on what each command does (§3). They may differ in how they
describe a room, how they word a refusal, and how they read a line.

The Python version's API is in `python/problem.md`. Each version has its own tests,
and all three also run the shared tests in `test_program.py`, which check only
the facts in §5.

## 1. The world

Five rooms. The player starts in the hall with nothing.

| Room | Exits | Items at the start |
| --- | --- | --- |
| hall | north → library, west → garden | `lamp` |
| library | north → attic, south → hall, west → cellar | `book` |
| cellar | east → library | `key` |
| attic | south → library | none |
| garden | east → hall | `rose`, `spade` |

Each room keeps its items as an ordered list. A taken item leaves its room's list,
and a dropped item goes on the end of the current room's list. The inventory is
also an ordered list: taking an item puts it on the end, and dropping one removes it.

## 2. Playing

The program is used at a terminal, one command per line, on stdin and stdout.
When the session starts it describes the hall. A line is a **verb** and an
optional **argument**, split at the first space after surrounding spaces are
removed; spaces around the argument are removed too, so `  go   north ` is `go`
with `north`. Each version decides for itself which other whitespace it removes
(tabs, carriage returns, no-break spaces) and whether it understands `LOOK` or
`go North`.

The session ends after `quit`, or at end of input. Lines after `quit` are not read.
The exit status is 0 whenever input is well formed UTF-8 text.

## 3. Commands

| Command | Effect | Answer |
| --- | --- | --- |
| `look` (argument ignored) | none | the current room's description |
| `go <direction>` | moves through the current room's exit that way | the new room's description |
| `take <item>` | moves the item from the room to the inventory | a line |
| `drop <item>` | moves the item from the inventory to the room | a line |
| `inventory` (argument ignored) | none | the inventory, in order |
| `quit` (argument ignored) | ends the session | a line |

A room's **description** names the room, lists its exits in the order north,
south, east, west, and lists the items it holds in order.

A command that can't be carried out is refused and changes nothing: `go` with no
argument or toward a direction with no exit, `take` of an item not in the room,
`drop` of an item not carried, `take` or `drop` with no argument, and any other
verb, an empty line included.

## 4. A sample session (the Python version)

The Python version prints this. The C and Rust versions happen to print the same
words, but SPEC does not require it: a version may describe rooms and word its
answers its own way, as long as it keeps the facts in §5.

```
You are in a dusty entrance hall.
Exits: north, west.
You see: lamp.
> take lamp
Taken.
> go north
You are in a book-lined library.
Exits: north, south, west.
You see: book.
> take sword
There is no sword here.
> dance
unknown verb: dance
> inventory
You are carrying: lamp.
> quit
Goodbye.
```

(`> ` marks the user's lines, which a terminal echoes; the program prints no
prompt.)

## 5. What the shared tests check

These are the only facts about the output that every version must share:
- At end of input the program stops without printing anything more. So the
  answer to a line is whatever the session prints after the output of the lines
  before it.
- A description names its room (`hall`, `library`, `cellar`, `attic`, `garden`)
  as a word, and no other room. It names every item the room holds.
- An `inventory` answer names every item carried and no other item.
- Only a description names a room, unless the line itself named one (the Python
  version answers `take hall` with `There is no hall here.`).
- Every line up to and including `quit` is answered with at least one line.
