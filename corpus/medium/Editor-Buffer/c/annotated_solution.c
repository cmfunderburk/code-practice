// Editor Buffer: whole program.
// From Python:
// 1. The command objects survive: Python's frozen `Insert` and `Delete` become
//    one `Command` struct with a `Kind` tag, a position, and the text it
//    inserts or removed. `apply` switches on the tag, and `inverse` flips it,
//    which is all Python's two `invert` methods do. [approach]
// 2. Python's `Delete` keeps the removed text so it can be undone, and C does
//    the same: `editor_delete` copies the characters it is about to remove into
//    the command before `perform` cuts them out. [approach]
// 3. Python's `str` is a sequence of code points, so `text[:pos]` counts
//    characters for free. C decodes each inserted line from UTF-8 into
//    `char32_t` code points, so a position indexes the array directly, and
//    `p` encodes them back. [text]
// 4. Python's `str` is immutable, so every edit builds a new string. Here the
//    text is one growable array, and an edit moves its tail with `memmove`.
//    [types]
// 5. Each command owns its `chars` array. A command moves between the undo and
//    redo stacks by struct copy, so exactly one stack holds it at a time, and
//    `clear` frees the arrays of the redo history it drops. Python's garbage
//    collector does this for `self._redo.clear()`. [types]
// 6. Python raises `ValueError` with the message, and `main` prints it. C's
//    editor functions return `false`, and `main` writes the message for the
//    verb it ran. [errors]
// 7. Python's `str.partition` and `split(" ")` build new strings. `parse`
//    finds the spaces with `memchr` and keeps pointers into the line: the text
//    of an insert is copied only once, when it is decoded. [library]
// 8. Python's `int` never overflows. Here a number is accumulated with C23's
//    `ckd_mul` and `ckd_add`, so one too big for `size_t` is not a command,
//    and `editor_delete` compares `n` with `len - pos` so it never adds them
//    at all. [types]
// 9. Python's `input()` becomes a `getchar` loop into a growable line, since
//    an insert's text has no natural limit. A `\r` before the `\n` stays in
//    the line, as it does in Python. [io]

// `ckd_add` and `ckd_mul` from `<stdckdint.h>`.
#include <stdckdint.h>
// `fputs`, `getchar`, `printf`, `putchar`, and `puts` from `<stdio.h>`.
#include <stdio.h>
// `exit`, `free`, and `realloc` from `<stdlib.h>`.
#include <stdlib.h>
// `memchr`, `memcpy`, and `memmove` from `<string.h>`.
#include <string.h>
// `char32_t`, C's type for one Unicode code point, from `<uchar.h>`.
#include <uchar.h>

static const char HELP[] = "i <pos> <text> | d <pos> <n> | u | r | p | q";

typedef struct {
    char32_t *chars;
    size_t len, capacity;
} Text;

// Python's two classes become one struct with a tag.
typedef enum { INSERT, DELETE } Kind;

typedef struct {
    Kind kind;
    size_t pos;
    Text text;
} Command;

typedef struct {
    Command *items;
    size_t len, capacity;
} History;

// Two stacks of commands, as in Python's `_undo` and `_redo` lists.
typedef struct {
    Text text;
    History undo, redo;
} Editor;

typedef struct {
    char *bytes;
    size_t len, capacity;
} Line;

// Python's `_command` returns a verb and a tuple of arguments. Here
// `verb` is the command's letter, or 0 for a malformed line, and `text`
// points into the line just read.
typedef struct {
    char verb;
    size_t pos, n;
    const char *text;
    size_t text_len;
} Request;

// Every allocation goes through here: a failure ends the program.
static void *xrealloc(void *block, size_t count, size_t size) {
    size_t bytes = 0;
    void *grown = ckd_mul(&bytes, count, size) ? nullptr : realloc(block, bytes);
    if (grown == nullptr) {
        fputs("out of memory\n", stderr);
        exit(EXIT_FAILURE);
    }
    return grown;
}

static void reserve(Text *text, size_t needed) {
    if (needed <= text->capacity) return;
    size_t capacity = text->capacity ? text->capacity : 16;
    while (capacity < needed) capacity *= 2;
    text->chars = xrealloc(text->chars, capacity, sizeof text->chars[0]);
    text->capacity = capacity;
}

// The lead byte says how many continuation bytes follow; each adds six
// bits. There is no validation: bytes that aren't UTF-8 decode to whatever
// code points they spell. SPEC does not say what to do with such input.
static void decode(const char bytes[], size_t len, Text *out) {
    for (size_t i = 0; i < len;) {
        unsigned char lead = (unsigned char)bytes[i++];
        int extra = lead < 0x80 ? 0 : lead < 0xE0 ? 1 : lead < 0xF0 ? 2 : 3;
        char32_t code = extra == 0 ? lead : lead & (0x3Fu >> extra);
        for (; extra > 0 && i < len; extra--)
            code = code << 6 | ((unsigned char)bytes[i++] & 0x3Fu);
        reserve(out, out->len + 1);
        out->chars[out->len++] = code;
    }
}

static void put_utf8(char32_t code) {
    if (code < 0x80) {
        putchar((int)code);
    } else if (code < 0x800) {
        putchar((int)(0xC0 | code >> 6));
        putchar((int)(0x80 | (code & 0x3F)));
    } else if (code < 0x10000) {
        putchar((int)(0xE0 | code >> 12));
        putchar((int)(0x80 | (code >> 6 & 0x3F)));
        putchar((int)(0x80 | (code & 0x3F)));
    } else {
        putchar((int)(0xF0 | code >> 18));
        putchar((int)(0x80 | (code >> 12 & 0x3F)));
        putchar((int)(0x80 | (code >> 6 & 0x3F)));
        putchar((int)(0x80 | (code & 0x3F)));
    }
}

// Python's `text[:pos] + s + text[pos:]`, in place. The early return keeps
// an empty insert from doing arithmetic on a null `chars`.
static void splice_in(Text *text, size_t pos, const Text *piece) {
    if (piece->len == 0) return;
    reserve(text, text->len + piece->len);
    memmove(text->chars + pos + piece->len, text->chars + pos,
            (text->len - pos) * sizeof text->chars[0]);
    memcpy(text->chars + pos, piece->chars, piece->len * sizeof text->chars[0]);
    text->len += piece->len;
}

static void splice_out(Text *text, size_t pos, size_t len) {
    if (len == 0) return;
    memmove(text->chars + pos, text->chars + pos + len,
            (text->len - pos - len) * sizeof text->chars[0]);
    text->len -= len;
}

static void apply(const Command *command, Text *text) {
    if (command->kind == INSERT) {
        splice_in(text, command->pos, &command->text);
    } else {
        splice_out(text, command->pos, command->text.len);
    }
}

// The copy shares `chars` with the original: it is applied once and
// dropped, never stored.
static Command inverse(Command command) {
    command.kind = command.kind == INSERT ? DELETE : INSERT;
    return command;
}

static void push(History *history, Command command) {
    if (history->len == history->capacity) {
        history->capacity = history->capacity ? history->capacity * 2 : 16;
        history->items = xrealloc(history->items, history->capacity, sizeof history->items[0]);
    }
    history->items[history->len++] = command;
}

static void clear(History *history) {
    for (size_t i = 0; i < history->len; i++) free(history->items[i].text.chars);
    history->len = 0;
}

// Python's `_do`: apply, remember, and drop the redo history.
static void perform(Editor *editor, Command command) {
    apply(&command, &editor->text);
    push(&editor->undo, command);
    clear(&editor->redo);
}

// The range check comes first, so a rejected insert allocates nothing.
static bool editor_insert(Editor *editor, size_t pos, const char utf8[], size_t bytes) {
    if (pos > editor->text.len) return false;
    Command command = {.kind = INSERT, .pos = pos};
    decode(utf8, bytes, &command.text);
    perform(editor, command);
    return true;
}

static bool editor_delete(Editor *editor, size_t pos, size_t n) {
    if (n < 1 || pos > editor->text.len || n > editor->text.len - pos) return false;
    Command command = {.kind = DELETE, .pos = pos};
    reserve(&command.text, n);
    memcpy(command.text.chars, editor->text.chars + pos, n * sizeof command.text.chars[0]);
    command.text.len = n;
    perform(editor, command);
    return true;
}

// Undo applies the inverse, and the command itself moves to the redo
// stack, as in Python.
static bool editor_undo(Editor *editor) {
    if (editor->undo.len == 0) return false;
    Command command = editor->undo.items[--editor->undo.len];
    Command undoing = inverse(command);
    apply(&undoing, &editor->text);
    push(&editor->redo, command);
    return true;
}

static bool editor_redo(Editor *editor) {
    if (editor->redo.len == 0) return false;
    Command command = editor->redo.items[--editor->redo.len];
    apply(&command, &editor->text);
    push(&editor->undo, command);
    return true;
}

static void editor_free(Editor *editor) {
    clear(&editor->undo);
    clear(&editor->redo);
    free(editor->undo.items);
    free(editor->redo.items);
    free(editor->text.chars);
}

static bool read_line(Line *line) {
    int ch = getchar();
    if (ch == EOF) return false;
    line->len = 0;
    for (; ch != EOF && ch != '\n'; ch = getchar()) {
        if (line->len == line->capacity) {
            line->capacity = line->capacity ? line->capacity * 2 : 64;
            line->bytes = xrealloc(line->bytes, line->capacity, 1);
        }
        line->bytes[line->len++] = (char)ch;
    }
    return true;
}

// ASCII digits by hand: `strtoul` would also take a sign or spaces, and it
// clamps a number too big for its type where this refuses it.
static bool number(const char text[], size_t len, size_t *value) {
    if (len < 1) return false;
    *value = 0;
    for (size_t i = 0; i < len; i++) {
        if (text[i] < '0' || text[i] > '9') return false;
        if (ckd_mul(value, *value, 10) || ckd_add(value, *value, (size_t)(text[i] - '0')))
            return false;
    }
    return true;
}

static Request parse(const char line[], size_t len) {
    Request request = {};
    if (len == 1 && memchr("urpq", line[0], 4) != nullptr) {
        request.verb = line[0];
        return request;
    }
    // Past the one-letter verbs, only `i <pos> ...` and `d <pos> <n>` remain,
    // and both have a verb letter, a space, and a number before the next space.
    if (len < 2 || line[1] != ' ') return request;
    const char *rest = line + 2;
    const char *end = line + len;
    const char *space = memchr(rest, ' ', (size_t)(end - rest));
    if (space == nullptr || !number(rest, (size_t)(space - rest), &request.pos)) return request;
    const char *after = space + 1;
    if (line[0] == 'i') {
        request.verb = 'i';
        request.text = after;
        request.text_len = (size_t)(end - after);
    } else if (line[0] == 'd' && number(after, (size_t)(end - after), &request.n)) {
        request.verb = 'd';
    }
    return request;
}

static void print_text(const Text *text) {
    putchar('"');
    for (size_t i = 0; i < text->len; i++) put_utf8(text->chars[i]);
    puts("\"");
}

int main(void) {
    Editor editor = {};
    Line line = {};
    while (read_line(&line)) {
        Request request = parse(line.bytes, line.len);
        // `q` reads no further line, so it leaves the loop.
        if (request.verb == 'q') break;
        switch (request.verb) {
        case 'i':
            if (!editor_insert(&editor, request.pos, request.text, request.text_len))
                printf("insert out of range: %zu\n", request.pos);
            break;
        case 'd':
            if (!editor_delete(&editor, request.pos, request.n))
                printf("delete out of range: %zu+%zu\n", request.pos, request.n);
            break;
        case 'u':
            if (!editor_undo(&editor)) puts("nothing to undo");
            break;
        case 'r':
            if (!editor_redo(&editor)) puts("nothing to redo");
            break;
        case 'p':
            print_text(&editor.text);
            break;
        default:
            puts(HELP);
        }
    }
    // LeakSanitizer checks this under ASan.
    free(line.bytes);
    editor_free(&editor);
    return 0;
}
