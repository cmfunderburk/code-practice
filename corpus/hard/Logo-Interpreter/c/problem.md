# Logo Interpreter

An interpreter for a small drawing language in the style of Logo, with undo,
over stdin and stdout. A program steers a *turtle*, a point on a grid with a
heading and a pen, which draws a line segment when it moves with the pen down. The
turtle starts at `(0, 0)` heading east with its pen down; north increases y.

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
  its top-level commands (those not inside a `REPEAT` block) is one history
  entry, so a whole `REPEAT` is one entry.
- **Output.** After each line that succeeds, print a state line whose first two
  integers are x and y, then the drawing, one `x1,y1 -> x2,y2` line per segment,
  oldest first. A line that fails to parse, or an `UNDO` with no history, prints
  one line containing `error` and changes nothing; no command on a failing line
  runs.
- There is no prompt, and the session ends at end of input.

The language and the drawing are specified in the program's `SPEC.md`. The
state line's wording, error messages, number spellings, and how far the turtle
may travel are up to this version.

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

## C contract

A whole program, `int main(void)`, with this core above it:

```c
typedef struct {
    int64_t x, y;
    int heading; // an index into "ENWS"
    bool pen_down;
    size_t segments; // how many of the Logo's segments are drawn
} Turtle;

typedef struct {
    Turtle turtle;
    Segment *segments; // Segment is {int64_t x1, y1, x2, y2}
    size_t capacity;
    Turtle *undo;
    size_t undo_len, undo_capacity;
} Logo;

static void tokenize(const char line[], size_t len, Tokens *tokens);
static bool parse_block(Parser *p, bool nested);
static bool logo_execute(Logo *logo, const Program *program);
static bool logo_undo(Logo *logo);
```

`tokenize` splits a NUL-terminated line into `Token`s pointing into it, and
`parse_block` parses a `Parser`'s tokens into its `Program`, returning `false`
with a message on a syntax error. `logo_execute` runs a parsed program, pushing
one undo entry per top-level command, and returns `false`, with nothing changed,
if a coordinate would overflow. `logo_undo` returns `false` with no history.

Differences from the Python version:
- There is no `render`, and the parsed program is a flat array, not a tree of
  objects.
- Coordinates are `int64_t`, and a line that would overflow them is an error.
- Input lines can be any length, and the drawing can grow without limit.
