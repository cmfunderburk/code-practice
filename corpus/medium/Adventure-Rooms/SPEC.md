# Adventure Rooms — SPEC

The adventure every implementation plays, in any language. The Python version
(`python/problem.md`) adds the API and the design. Each implementation is its
language's natural program: how it describes a room, how it words a refusal, and
how it reads a line are its own. The **world** (§1) and the **rules** (§3) are
not, and §5 fixes the few output facts all of them share.

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
with `north`. Which other whitespace is trimmed, and whether `LOOK` or `go North`
is understood, is the implementation's choice.

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

## 4. A session (one implementation)

The Python version's shell prints this; other implementations may describe rooms, and word
their answers, their own way.

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

## 5. Fixed output

These are the only output facts every implementation keeps fixed; all other
wording is each implementation's own:
- End of input ends the session without another word, so the answer to a line is
  whatever the session prints past the lines before it.
- A description names its room (`hall`, `library`, `cellar`, `attic`, `garden`) as
  a word, and no other room. It names every item the room holds.
- An `inventory` answer names every item carried and no other item.
- Only a description names a room, unless the line itself named one (Python's
  `take hall` answers `There is no hall here.`).
- Every line up to and including `quit` is answered with at least one line.
