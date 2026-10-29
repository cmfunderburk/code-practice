# Logo Interpreter

A turtle-graphics interpreter with undo, over stdin and stdout. The turtle
starts at `(0, 0)` heading east with its pen down; north increases y.

| Command | Effect |
| --- | --- |
| `FORWARD n` | move `n` cells; with the pen down, draw a segment |
| `LEFT` / `RIGHT` | turn 90° counterclockwise / clockwise |
| `PENUP` / `PENDOWN` | lift / lower the pen |
| `REPEAT n [ ... ]` | run the block `n` times; blocks nest and may be empty |

- **Words.** Split at whitespace; `[` and `]` are always words of their own.
  Letters are case-insensitive. A count or distance is an integer of at least 1.
- **Lines.** A line whose only word is `UNDO` (any case) undoes the most recent
  history entry. Every other line, an empty one included, is a program; each of
  its top-level commands is one history entry, a whole `REPEAT` included.
- **Output.** After each line that succeeds, print a state line whose first two
  integers are x and y, then the drawing, one `x1,y1 -> x2,y2` line per segment,
  oldest first. A line that fails to parse, or an `UNDO` with no history, prints
  one line containing `error` and changes nothing; no command on a failing line
  runs.
- There is no prompt, and the session ends at end of input.

The language and the drawing are the program's `SPEC.md`. The state line's
wording, error messages, number spellings, and how far the turtle may travel are
the port's own.

## A session

```text
> FORWARD 2 LEFT
x=2 y=0 heading=N pen=down segments=1
0,0 -> 2,0
> penup REPEAT 2 [ FORWARD 1 RIGHT ]
x=3 y=1 heading=S pen=up segments=1
0,0 -> 2,0
> FORWARD 0
error: counts and distances must be positive
> UNDO
x=2 y=0 heading=N pen=up segments=1
0,0 -> 2,0
```

(`> ` marks the user's lines.)

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
type Segment = ((i64, i64), (i64, i64));

#[derive(Clone, Copy)]
struct Turtle {
    x: i64,
    y: i64,
    heading: usize, // an index into HEADINGS, ['E', 'N', 'W', 'S']
    pen_down: bool,
}

struct Logo {
    turtle: Turtle,
    segments: Vec<Segment>,
    undo: Vec<(Turtle, usize)>,
}

fn tokens(line: &str) -> Vec<String>
impl Logo {
    fn new() -> Logo
    fn execute(&mut self, tokens: &[String]) -> Result<(), String>
    fn undo(&mut self) -> Result<(), String>
}
```

`tokens` splits a line into upper-cased words with each bracket its own word.
`execute` parses the whole line, then runs it, pushing one undo entry per
top-level command; it returns `Err`, with nothing changed, on a syntax error or
if a coordinate would overflow `i64`. `undo` returns `Err` with no history.

Differences from the Python version:
- No `render`; a parsed `Command` is an enum, not a dataclass.
- Coordinates are `i64`, and a line that would overflow them is an error.
