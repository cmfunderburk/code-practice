// Editor Buffer: whole program.

#include <stdckdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <uchar.h>

static const char HELP[] = "i <pos> <text> | d <pos> <n> | u | r | p | q";

typedef struct {
    char32_t *chars;
    size_t len, capacity;
} Text;

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

typedef struct {
    Text text;
    History undo, redo;
} Editor;

typedef struct {
    char *bytes;
    size_t len, capacity;
} Line;

typedef struct {
    char verb;
    size_t pos, n;
    const char *text;
    size_t text_len;
} Request;

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

static void perform(Editor *editor, Command command) {
    apply(&command, &editor->text);
    push(&editor->undo, command);
    clear(&editor->redo);
}

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
    free(line.bytes);
    editor_free(&editor);
    return 0;
}
