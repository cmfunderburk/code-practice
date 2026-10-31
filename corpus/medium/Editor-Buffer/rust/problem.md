# Editor Buffer

Edit one text buffer, which starts empty, with unlimited undo and redo, one
command per stdin line.

- Positions and counts are in **characters** (Unicode code points), not bytes.
  Insert at `p` puts text before the character at index `p`, for `p` from 0 to
  the length. Delete of `n` characters at `p` needs `n ≥ 1` and `p + n` at most
  the length. Undo reverses the latest edit not yet undone; redo reapplies the
  latest undone one. Every successful insert or delete clears the redo history;
  a refused command changes nothing.
- The commands are `i <pos> <text>`, `d <pos> <n>`, `u`, `r`, `p`, and `q`, with
  fields separated by one space and decimal numbers. `<text>` is everything
  after the space that follows `<pos>`; it may be empty or contain spaces.
- Answers:
  - `p`: the whole text on one line between two `"`, with no escaping;
  - a successful edit, undo, or redo: nothing;
  - a line that isn't a command, a refused edit, or an undo or redo with
    nothing to do: one line.
- No prompt and no banner. The session ends after `q` or at end of input.

The editor is the program's `SPEC.md`. What `p` shows is the same in every
version; how you word a refusal, and which unusual lines (a sign, a huge number, a
`\r` at the end of a line) you accept, are up to you.

## A session

```text
> i 0 hello
> i 5  world
> d 0 6
> p
"world"
> u
> u
> p
"hello"
> r
> i 11 !
> r
nothing to redo
> x
i <pos> <text> | d <pos> <n> | u | r | p | q
> p
"hello world!"
```

(`> ` marks the user's lines.)

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
#[derive(Default)]
struct EditorBuffer {
    text: Vec<char>,
    // and the undo and redo stacks
}

impl EditorBuffer {
    fn insert(&mut self, pos: usize, text: &str) -> Result<(), String>
    fn delete(&mut self, pos: usize, n: usize) -> Result<(), String>
    fn undo(&mut self) -> Result<(), String>
    fn redo(&mut self) -> Result<(), String>
}

enum Command<'a> {
    Insert(usize, &'a str),
    Delete(usize, usize),
    Undo,
    Redo,
    Print,
    Quit,
}

fn command(line: &str) -> Option<Command<'_>>
```

Each buffer method returns `Err` with its refusal and changes nothing; `command`
is `None` for a line that isn't a command.

Differences from the Python version:
- Errors are `Result<(), String>` where Python raises `ValueError`.
