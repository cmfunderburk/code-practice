// Logo Interpreter: whole program.
// From Python:
// 1. Commands are still values, but Python's tree of frozen `Command` values
//    becomes one flat array in preorder. A `REPEAT` records its `span`,
//    the number of commands in its body, nested ones included, so its body is
//    the next `span` entries, and `run` steps over a command and its body with
//    `i += 1 + span`. A parse never builds a pointer. [approach]
// 2. Python's undo entry is `Restore(before)`, a whole previous `Drawing`. Here
//    an entry is a 32-byte `Turtle`: position, heading, pen, and how many
//    segments existed. Commands only ever append segments, so every earlier
//    drawing is a prefix of the current one, and restoring the count drops
//    exactly what the undone command drew. Undo copies no segments. [approach]
// 3. Python's frozen `Drawing` builds a new value per command, and its
//    `segments` tuple grows by concatenation. C changes one `Logo` in place
//    and appends segments to a growable array. [types]
// 4. Python raises `ValueError` from deep in the recursive parser, and `main`
//    prints it. C's parser returns `false` up the recursion and leaves
//    the message, and the token it blames, in the `Parser`. Nothing runs
//    before the whole line has parsed, as in Python. [errors]
// 5. Python spaces out the brackets, upper-cases the line, and calls
//    `split()`. `tokenize` makes each bracket a token of its own, splits at
//    `isspace`, C's whitespace, and keeps pointers into the line; `is` compares
//    through `toupper`, so nothing is upper-cased in place. [text]
// 6. Python's `int` reads a number. C's is `strtoll`, which takes a sign and
//    leading zeros as `int` does but not `int`'s `_` separators, so `1_000` is
//    an error here, and reports a value past `int64_t` through `errno`. [library]
// 7. Python's integers never overflow. Coordinates are `int64_t`, and `apply`
//    moves the turtle with `ckd_mul` and `ckd_add`, which report an overflow
//    instead of performing it (signed overflow is undefined behavior in C). A
//    line that would overflow is an error, and `logo_execute` undoes all of it.
//    [integers]
// 8. Python reads with `input()`, which raises `EOFError` at end of input.
//    `read_line` grows its buffer with `getchar` until the newline, so a line of
//    any length arrives whole, and returns `false` at end of input. [io]

// `isspace` and `toupper` from `<ctype.h>`.
#include <ctype.h>
// `errno` and `ERANGE` from `<errno.h>`.
#include <errno.h>
// `PRId64` from `<inttypes.h>`.
#include <inttypes.h>
// `ckd_add` and `ckd_mul` from `<stdckdint.h>`.
#include <stdckdint.h>
// `int64_t` from `<stdint.h>`.
#include <stdint.h>
// `fputs`, `getchar`, `printf`, `putchar`, and `puts` from `<stdio.h>`.
#include <stdio.h>
// `exit`, `free`, `realloc`, and `strtoll` from `<stdlib.h>`.
#include <stdlib.h>
// `strlen` from `<string.h>`.
#include <string.h>

typedef enum { FORWARD, LEFT, RIGHT, PENUP, PENDOWN, REPEAT } Op;

// `arg` is a distance or a repeat count; `span` is zero except for
// `REPEAT`.
typedef struct {
    Op op;
    int64_t arg;
    size_t span;
} Command;

typedef struct {
    Command *items;
    size_t len, capacity;
} Program;

typedef struct {
    int64_t x1, y1, x2, y2;
} Segment;

// Everything about the drawing except the segments themselves: the
// current state and each undo entry are the same type.
typedef struct {
    int64_t x, y;
    int heading;
    bool pen_down;
    size_t segments;
} Turtle;

// `turtle.segments` counts the entries of `segments` in the drawing;
// entries past it belong to undone commands, and the next segment drawn
// overwrites them.
typedef struct {
    Turtle turtle;
    Segment *segments;
    size_t capacity;
    Turtle *undo;
    size_t undo_len, undo_capacity;
} Logo;

typedef struct {
    const char *text;
    size_t len;
} Token;

typedef struct {
    Token *items;
    size_t len, capacity;
} Tokens;

typedef struct {
    const Token *tokens;
    size_t count, pos;
    Program *program;
    const char *error;
    Token detail;
} Parser;

typedef struct {
    char *bytes;
    size_t len, capacity;
} Line;

static const struct {
    int dx, dy;
} VECTORS[] = {{1, 0}, {0, 1}, {-1, 0}, {0, -1}};
static const char HEADINGS[] = "ENWS";

static void *xrealloc(void *block, size_t count, size_t size) {
    size_t bytes = 0;
    void *grown = ckd_mul(&bytes, count, size) ? nullptr : realloc(block, bytes);
    if (grown == nullptr) {
        fputs("out of memory\n", stderr);
        exit(EXIT_FAILURE);
    }
    return grown;
}

static size_t grown(size_t capacity) { return capacity ? capacity * 2 : 16; }

static bool is_bracket(char ch) { return ch == '[' || ch == ']'; }

// A bracket ends the token before it and is a token by itself.
static void tokenize(const char line[], size_t len, Tokens *tokens) {
    tokens->len = 0;
    for (size_t i = 0; i < len;) {
        if (isspace((unsigned char)line[i])) {
            i++;
            continue;
        }
        size_t start = i++;
        if (!is_bracket(line[start]))
            while (i < len && !isspace((unsigned char)line[i]) && !is_bracket(line[i])) i++;
        if (tokens->len == tokens->capacity) {
            tokens->capacity = grown(tokens->capacity);
            tokens->items = xrealloc(tokens->items, tokens->capacity, sizeof tokens->items[0]);
        }
        tokens->items[tokens->len++] = (Token){line + start, i - start};
    }
}

static bool is(Token token, const char word[]) {
    if (token.len != strlen(word)) return false;
    for (size_t i = 0; i < token.len; i++) {
        if (toupper((unsigned char)token.text[i]) != word[i]) return false;
    }
    return true;
}

// `strtoll` reads an optional sign and decimal digits and stops at the first
// other character, which must be the token's end. The line is NUL-terminated,
// so it never reads past the line.
static bool number(Token token, int64_t *value) {
    char *end = nullptr;
    errno = 0;
    int64_t parsed = strtoll(token.text, &end, 10);
    if (end != token.text + token.len || errno == ERANGE) return false;
    *value = parsed;
    return true;
}

static bool fail(Parser *p, const char error[], Token detail) {
    p->error = error;
    p->detail = detail;
    return false;
}

static bool positive(Parser *p, Token token, int64_t *value) {
    if (!number(token, value)) return fail(p, "expected a positive integer, got", token);
    if (*value < 1) return fail(p, "counts and distances must be positive", (Token){});
    return true;
}

static void append(Program *program, Command command) {
    if (program->len == program->capacity) {
        program->capacity = grown(program->capacity);
        program->items = xrealloc(program->items, program->capacity, sizeof program->items[0]);
    }
    program->items[program->len++] = command;
}

// Python's `_parse`, writing into `p->program` instead of returning a
// tuple. A nested call returns after its `]`.
static bool parse_block(Parser *p, bool nested) {
    while (p->pos < p->count) {
        Token op = p->tokens[p->pos++];
        int64_t arg = 0;
        if (is(op, "]")) {
            return nested || fail(p, "unexpected ]", (Token){});
        } else if (is(op, "FORWARD")) {
            if (p->pos == p->count) return fail(p, "FORWARD needs a distance", (Token){});
            if (!positive(p, p->tokens[p->pos++], &arg)) return false;
            append(p->program, (Command){.op = FORWARD, .arg = arg});
        } else if (is(op, "LEFT")) {
            append(p->program, (Command){.op = LEFT});
        } else if (is(op, "RIGHT")) {
            append(p->program, (Command){.op = RIGHT});
        } else if (is(op, "PENUP")) {
            append(p->program, (Command){.op = PENUP});
        } else if (is(op, "PENDOWN")) {
            append(p->program, (Command){.op = PENDOWN});
        } else if (is(op, "REPEAT")) {
            if (p->pos + 1 >= p->count || !is(p->tokens[p->pos + 1], "["))
                return fail(p, "REPEAT needs a count and [ block ]", (Token){});
            if (!positive(p, p->tokens[p->pos], &arg)) return false;
            p->pos += 2;
            size_t at = p->program->len;
            append(p->program, (Command){.op = REPEAT, .arg = arg});
            if (!parse_block(p, true)) return false;
            // Everything appended since the `REPEAT` itself is its body.
            p->program->items[at].span = p->program->len - at - 1;
        } else {
            return fail(p, "unknown command:", op);
        }
    }
    return !nested || fail(p, "missing ]", (Token){});
}

static void add_segment(Logo *logo, Segment segment) {
    if (logo->turtle.segments == logo->capacity) {
        logo->capacity = grown(logo->capacity);
        logo->segments = xrealloc(logo->segments, logo->capacity, sizeof logo->segments[0]);
    }
    logo->segments[logo->turtle.segments++] = segment;
}

static bool run(Logo *logo, const Command program[], size_t len);

// `false` when a coordinate would overflow `int64_t`.
static bool apply(Logo *logo, const Command *command) {
    Turtle *turtle = &logo->turtle;
    switch (command->op) {
    case FORWARD: {
        int64_t dx = 0, dy = 0, x = 0, y = 0;
        if (ckd_mul(&dx, VECTORS[turtle->heading].dx, command->arg) ||
            ckd_mul(&dy, VECTORS[turtle->heading].dy, command->arg) || ckd_add(&x, turtle->x, dx) ||
            ckd_add(&y, turtle->y, dy))
            return false;
        if (turtle->pen_down) add_segment(logo, (Segment){turtle->x, turtle->y, x, y});
        turtle->x = x;
        turtle->y = y;
        break;
    }
    case LEFT:
        turtle->heading = (turtle->heading + 1) % 4;
        break;
    case RIGHT:
        turtle->heading = (turtle->heading + 3) % 4;
        break;
    case PENUP:
    case PENDOWN:
        turtle->pen_down = command->op == PENDOWN;
        break;
    // Python's loop over `body`, running the body's slice of the array.
    case REPEAT:
        for (int64_t i = 0; i < command->arg; i++)
            if (!run(logo, command + 1, command->span)) return false;
        break;
    }
    return true;
}

static bool run(Logo *logo, const Command program[], size_t len) {
    for (size_t i = 0; i < len; i += 1 + program[i].span)
        if (!apply(logo, &program[i])) return false;
    return true;
}

// One undo entry per top-level command, as Python appends one `Restore`. An
// overflow puts back the first entry pushed for the line, so a failing line
// changes nothing, segments included.
static bool logo_execute(Logo *logo, const Program *program) {
    size_t start = logo->undo_len;
    for (size_t i = 0; i < program->len; i += 1 + program->items[i].span) {
        if (logo->undo_len == logo->undo_capacity) {
            logo->undo_capacity = grown(logo->undo_capacity);
            logo->undo = xrealloc(logo->undo, logo->undo_capacity, sizeof logo->undo[0]);
        }
        logo->undo[logo->undo_len++] = logo->turtle;
        if (!apply(logo, &program->items[i])) {
            logo->turtle = logo->undo[start];
            logo->undo_len = start;
            return false;
        }
    }
    return true;
}

// Python's `Restore.apply`: the saved turtle replaces the current one.
static bool logo_undo(Logo *logo) {
    if (logo->undo_len == 0) return false;
    logo->turtle = logo->undo[--logo->undo_len];
    return true;
}

static void report(const Logo *logo) {
    const Turtle *turtle = &logo->turtle;
    printf("x=%" PRId64 " y=%" PRId64 " heading=%c pen=%s segments=%zu\n", turtle->x, turtle->y,
           HEADINGS[turtle->heading], turtle->pen_down ? "down" : "up", turtle->segments);
    for (size_t i = 0; i < turtle->segments; i++) {
        Segment s = logo->segments[i];
        printf("%" PRId64 ",%" PRId64 " -> %" PRId64 ",%" PRId64 "\n", s.x1, s.y1, s.x2, s.y2);
    }
}

// One line of any length, NUL-terminated, without its newline: a REPEAT
// program can outgrow any fixed `fgets` buffer.
static bool read_line(Line *line) {
    int ch = getchar();
    if (ch == EOF) return false;
    line->len = 0;
    for (;; ch = getchar()) {
        if (line->len + 1 >= line->capacity) {
            line->capacity = line->capacity ? line->capacity * 2 : 64;
            line->bytes = xrealloc(line->bytes, line->capacity, 1);
        }
        if (ch == EOF || ch == '\n') break;
        line->bytes[line->len++] = (char)ch;
    }
    line->bytes[line->len] = '\0';
    return true;
}

int main(void) {
    Logo logo = {.turtle = {.pen_down = true}};
    Line line = {};
    Tokens tokens = {};
    Program program = {};
    while (read_line(&line)) {
        tokenize(line.bytes, line.len, &tokens);
        // A lone `UNDO` token has no bracket in it, so splitting at brackets
        // agrees with Python's plain `split()` here.
        if (tokens.len == 1 && is(tokens.items[0], "UNDO")) {
            if (!logo_undo(&logo)) {
                puts("error: nothing to undo");
                continue;
            }
        } else {
            program.len = 0;
            Parser parser = {.tokens = tokens.items, .count = tokens.len, .program = &program};
            if (!parse_block(&parser, false)) {
                printf("error: %s", parser.error);
                if (parser.detail.len > 0)
                    printf(" %.*s", (int)parser.detail.len, parser.detail.text);
                putchar('\n');
                continue;
            }
            if (!logo_execute(&logo, &program)) {
                puts("error: the turtle would leave the 64-bit grid");
                continue;
            }
        }
        report(&logo);
    }
    free(line.bytes);
    free(tokens.items);
    free(program.items);
    free(logo.segments);
    free(logo.undo);
    return 0;
}
