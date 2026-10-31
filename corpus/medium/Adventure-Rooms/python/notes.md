## How it works

The program is a text adventure run by one function,
`execute(state, line) -> (state, output)`. The state is one dict with four keys:
the current `room`, the `inventory` list, `items` (each room's current list of
items), and `over`. `new_game` builds it, copying each room's list from
`START_ITEMS`, so two games never share a list.

`VERBS` is a *dispatch table*: a dictionary from each command word to the function
that handles it, its *handler*. Every handler has the same shape,
`(state, arg) -> (state, output)`. `execute` refuses any command after `quit`,
removes surrounding spaces, splits the line at the first space into a verb and an
argument, looks the verb up in `VERBS`, and calls the handler with the argument
stripped. `execute` itself knows nothing about rooms or items: adding a `sing`
command would be one new function and one new entry in `VERBS`, and `execute`
would not change. Because `execute` reads `VERBS` on every call, not a copy made
when the module was loaded, a verb added to the dictionary while the program runs
is found on the next call.

`_look` writes a room's description: `You are in <description>.`, then `Exits:`
and the room's exits, then `You see:` and the room's items, only when there are
any. It lists the exits by walking `DIRECTIONS`, not the room's entry in `EXITS`,
so they always come out in the order north, south, east, west.

Worked check: `go north` in the hall. `execute` splits the line into `go` and
`north` and calls `_do_go`. `_do_go` would answer `Go where?` for an empty argument
and `You can't go that way.` for a direction with no exit. `north` is an exit of
the hall, so it sets `room` to `library` and returns `_look` of the library.

**Complexity.** Splitting a line of n characters takes O(n) time. The verb lookup
is O(1), and each handler works on lists of at most five items.

## `main`

`main()` turns `execute` into a session at a terminal. It creates one state,
prints the opening description, and then reads one line at a time with `input()`
until the state's `over` flag is set. It hands each line to `execute` unchanged,
since removing spaces and splitting are `execute`'s job. After a successful line
it keeps the state `execute` returned and prints the output. When `execute` raises
`ValueError` for an unknown verb, `main` prints the message as it is and keeps its
old state. At end of input, `input()` raises `EOFError`, and `main` returns without
printing anything.

Keeping the old state after an error is safe for the program's own errors, because
`execute` raises them before it calls any handler. It is not an undo: a handler
that changed the state and then raised would leave its change behind.

Successful `go`, `take`, `drop`, and `quit` commands change the state dict in place
and return it. `look` and `inventory` only read it, and a refused command (`Go
where?`, `There is no sword here.`) returns it unchanged.

## Design choices

- **A table, not an `if`/`elif` chain.** The six commands could be six branches of
  one function. That keeps choosing a command and carrying it out in one place,
  which reads well while the set of commands never changes. The table separates
  the two: choosing a command is a dictionary lookup in `execute`, and carrying it
  out is the handler's job, so adding a command never touches `execute`.
- **The map in three constants, not one world value.** `DESCRIPTIONS`, `EXITS`,
  and `START_ITEMS` describe one fixed five-room world, and the handlers read them
  directly. Putting the whole map into one value passed to `new_game` would let the
  same code play any map, but then the program has to trust that the value has the
  right shape: every room with a description, exits, and items, and every exit
  leading to a room that exists. That is worth doing once the map grows or is
  loaded from a file, and then the program should check the map when it loads it.
- **Refusals are answers; mistakes by the caller raise.** `Go where?` and
  `There is no sword here.` are answers the game gives the player, so handlers
  return them. A verb that isn't in `VERBS`, or any command after `quit`, is a
  mistake by whoever called `execute`, so `execute` raises `ValueError`. `main`
  never sends a line after `quit`, and it prints an unknown verb's message like any
  other answer, so the player sees `unknown verb: dance` with no `error:` in front.
  SPEC leaves the wording of refusals to each version.
- **One line per command, and a silent end.** `main` reads one line per command,
  so a person can play at a terminal, and it prints no prompt. At end of input it
  catches `EOFError` and stops without a message. A `main` that read with
  `input("> ")` would print `> ` into every transcript, and one that didn't catch
  `EOFError` would end every session piped from a file with a traceback and exit
  status 1.
- **Trimming uses Python's `strip()`.** `execute` trims with `str.strip()`, which
  removes the 29 characters Python counts as whitespace, among them `\t`, `\r`,
  and the no-break space U+00A0. SPEC fixes only how ordinary spaces are handled
  and leaves other whitespace to each version. Rust's `trim()` removes the same
  characters as Python's `strip()` except four ASCII control characters
  (`\x1c` to `\x1f`); C's `isspace` covers only the six ASCII whitespace
  characters.
- **The world and the rules are shared; the wording is not.** The map, the items,
  and what each command does are SPEC §1 and §3 in every version. A room's
  description and a refusal's wording are each version's own. The shared tests read
  only which room and item names an answer contains.

## Where this shows up again

A Unix shell such as `sh` handles a few commands itself, called *builtins*: `cd`,
`exit`, and `export`. It looks the first word of each line up among them, as
`execute` looks a verb up in `VERBS`, and `exit` ends its loop as `quit` ends this
one. An interactive shell also ends at end of input, as this program does.

Two things change at that size. A word that isn't a builtin is not an error: the
shell runs the program with that name, starting it with `fork` and `exec` and
waiting for it with `wait`. And before it can find the first word, the shell must
split the line into words, respecting quotes, and replace variables such as
`$HOME` with their values, where `execute` only splits at the first space.
