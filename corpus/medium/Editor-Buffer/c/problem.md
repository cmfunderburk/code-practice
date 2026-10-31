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

## C contract

A whole program, `int main(void)`, with this core above it:

```c
typedef struct {
    char32_t *chars;
    size_t len, capacity;
} Text;

typedef struct {
    Text text;
    // and the undo and redo stacks
} Editor;

typedef struct {
    char verb;  // 'i', 'd', 'u', 'r', 'p', 'q', or 0 for a line that isn't a command
    size_t pos, n;
    const char *text;  // an insert's text, pointing into the line
    size_t text_len;
} Request;

static bool editor_insert(Editor *editor, size_t pos, const char utf8[], size_t bytes);
static bool editor_delete(Editor *editor, size_t pos, size_t n);
static bool editor_undo(Editor *editor);
static bool editor_redo(Editor *editor);
static void editor_free(Editor *editor);
static Request parse(const char line[], size_t len);
```

An `Editor` starts as `(Editor){}`. Each editor function returns `false` and
changes nothing when it refuses.

Differences from the Python version:
- Input is UTF-8 and positions count characters, so the program decodes what it
  inserts and encodes what it prints.
- Lines can be any length, and the text can grow without limit.
