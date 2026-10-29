## Verb Dispatch — worked example

**Intuition.** The dispatch table is the natural implementation for a
verb-driven game: the program IS a mapping from words to behaviors, so
say it as one. `VERBS` maps each
verb to a handler `(state, arg) -> (state, output)`, and `execute`
shrinks to guard + split + table lookup. Adding `sing` to this game is
one function and one entry; the engine never changes. The seam shows
behaviorally: register `xyzzy` into `VERBS` and the engine finds it,
because it consults the table at call time, not a copy taken at import.

Worked check: `go north` in the hall — `execute` looks up `_do_go`,
which rejects a missing arg (`Go where?`), rejects a non-exit
(`You can't go that way.`), or moves the player and returns the new
room's `_look`.

**Complexity.**
- Time: $O(1)$ verb lookup + handler work; Space: a six-entry table.

**Discussed, not drilled.** The contrast with an if/elif ladder is the lesson:
same six behaviors, but here verb *selection* is data while verb
*behavior* stays code. `functools.singledispatch` and class-based
command objects are the stdlib and OO flavors of the same seam. The
next size up — per-verb argument parsing, per-verb help text — hangs
naturally off the table as richer entry values, none of which touches
`execute`.

**The drilled representative composition root.** `main()` turns the shared
`(state, line) -> (state, output)` API into a conversation: it prints the opening
look, then reads stdin a line at a time with `input()`.
Successful calls replace the current state and print their output, while an
exception preserves the prior binding when the failing operation did not mutate
it. The built-in unknown-verb and terminal guards fail before mutation, but
`main()` cannot undo a custom handler that mutates and then raises. The loop ends
when `quit` sets the terminal flag, or silently when `input()` raises `EOFError`
at end of input. Each line goes
to `execute` untouched: trimming and splitting are the engine's job.

Successful state-changing commands (`go`, `take`, `drop`, `quit`) mutate the
session dict in place and return it. `look` and `inventory` only observe it;
rejected built-in operations return it unchanged or raise before mutation.

**Reversal pressures.** For a closed six-verb game, the ladder can be the
stronger design: selection and behavior stay together in one locally readable
function, while dispatch adds handler and table indirection. For one fixed
five-room world, module constants can likewise be stronger than one `WORLD` value,
which adds a trusted schema convention and copies every room's item list per session.
Growing verbs favors dispatch; growing or replaceable content favors world data.

## Shapes chosen and rejected

- **A verb table (chosen)** over an **if/elif ladder**. Both hold the same six
  behaviors. The table makes verb selection data, so a new verb is a handler and
  an entry and `execute` never changes; registering `xyzzy` at run time shows
  it. The ladder keeps selection and behavior in one locally readable function,
  which is the stronger shape only while the verb set is closed.
- **Module constants (chosen)** over **one `WORLD` value**. With one fixed
  five-room world, three constants read directly. The data version turns the
  engine into an interpreter for any world, at the cost of a trusted schema and
  a copy of every room's item list per session. It wins once content grows or
  must be replaceable.
- **In-fiction failures are output; only caller mistakes raise.** `Go where?`
  and `There is no sword here.` are answers the game gives, so handlers return
  them. A verb outside the table, or any command after `quit`, is the caller's
  mistake, so `execute` raises. The shell never sends a line after `quit`, and it
  prints an unknown verb's message. Both reach stdout the same way, so the Python
  version never writes `error:`; SPEC leaves a refusal's wording to each
  implementation.
- **Line-by-line reading with a silent end.** The shell reads one line per
  command, so a person can play at a terminal, and end of input ends the session
  with no message. An `input("> ")` shell would print a prompt into every
  transcript and die at end of input with `EOFError` and exit status 1. This one
  reads with plain `input()` and catches the `EOFError`.
- **Trimming is Python's.** The drilled `execute` trims with `str.strip()`,
  which removes 29 Unicode whitespace characters, among them `\t`, `\r`, and
  U+00A0. SPEC fixes only the space and leaves the rest to each implementation,
  rather than ruling out every other whitespace character so that a port
  trimming spaces would print the same bytes: Rust's
  `trim()` removes Unicode whitespace much as Python does, and C's `isspace`
  trims the ASCII ones.
- **The world and rules are the shared part.** The map, the items, and what each
  command does are SPEC §1 and §3 in every implementation; a room's description
  and a refusal's wording are each implementation's own. The fixed output (SPEC
  §5) is little more than the room and item names an answer contains.

## Scales up to

A Unix shell keeps a *dispatch table* for its builtins: the first word of a
parsed line is looked up among `cd`, `exit`, and `export`, as a verb is looked
up in `VERBS`, and `exit` ends the loop as `quit` does here. Its interactive mode has this program's
ending too: EOF exits. Two things change at that size. A word that misses the
table is not an error: a shell's archetype is programs running programs, through
`fork`, `exec`, and `wait`. And the line must first be tokenized with quoting and
expanded, where this engine only splits at the first space.
