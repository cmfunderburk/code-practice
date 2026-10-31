// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main logo_main
#include "solution.c"
#undef main

static Logo logo = {.turtle = {.pen_down = true}};
static Tokens tokens;
static Program program;

// One program line, as main runs it: false if it fails to parse or overflows.
static bool execute(const char *line) {
    tokenize(line, strlen(line), &tokens);
    program.len = 0;
    Parser parser = {.tokens = tokens.items, .count = tokens.len, .program = &program};
    return parse_block(&parser, false) && logo_execute(&logo, &program);
}

static bool at(int64_t x, int64_t y, char heading, bool pen_down, size_t segments) {
    const Turtle *t = &logo.turtle;
    return t->x == x && t->y == y && HEADINGS[t->heading] == heading && t->pen_down == pen_down &&
           t->segments == segments;
}

static bool segment(size_t i, int64_t x1, int64_t y1, int64_t x2, int64_t y2) {
    Segment s = logo.segments[i];
    return s.x1 == x1 && s.y1 == y1 && s.x2 == x2 && s.y2 == y2;
}

static void reset(void) {
    logo.turtle = (Turtle){.pen_down = true};
    logo.undo_len = 0;
}

int main(void) {
    // A square is four segments and one history entry.
    assert(execute("REPEAT 4 [ FORWARD 2 LEFT ]") && at(0, 0, 'E', true, 4));
    assert(segment(0, 0, 0, 2, 0) && segment(1, 2, 0, 2, 2) && segment(2, 2, 2, 0, 2) &&
           segment(3, 0, 2, 0, 0));
    assert(logo_undo(&logo) && at(0, 0, 'E', true, 0) && !logo_undo(&logo));

    // Each top-level command is its own entry.
    assert(execute("FORWARD 2 RIGHT FORWARD 3") && at(2, -3, 'S', true, 2));
    assert(logo_undo(&logo) && at(2, 0, 'S', true, 1));
    assert(logo_undo(&logo) && at(2, 0, 'E', true, 1));
    assert(logo_undo(&logo) && at(0, 0, 'E', true, 0));

    // The pen up moves without drawing; undo restores the pen too.
    assert(execute("PENUP FORWARD 3 LEFT FORWARD 2 PENDOWN RIGHT FORWARD 1"));
    assert(at(4, 2, 'E', true, 1) && segment(0, 3, 2, 4, 2));
    assert(logo_undo(&logo) && at(3, 2, 'E', true, 0));
    reset();

    // Case, bracket spacing, and whitespace do not matter; blocks nest and may be empty.
    assert(execute("repeat 2[forward 1 left repeat 2[forward 1 right]]"));
    assert(at(3, -1, 'W', true, 6));
    assert(execute("\tREPEAT 3 [ ]\r") && logo.undo_len == 2 && at(3, -1, 'W', true, 6));
    reset();

    // strtoll's numbers: a sign and leading zeros, but no underscores.
    assert(execute("FORWARD +3 FORWARD 007") && at(10, 0, 'E', true, 2));
    reset();

    // A bad line changes nothing and adds no history.
    const char *bad[] = {"FORWARD",           "FORWARD 0",
                         "FORWARD -2",        "FORWARD 1_0",
                         "FORWARD x",         "FORWARD 3.0",
                         "FORWARD 1 SPIN",    "]",
                         "[ LEFT ]",          "REPEAT 2 FORWARD 1",
                         "REPEAT 0 [ LEFT ]", "REPEAT 2 [ LEFT",
                         "UNDO UNDO",         "FORWARD 99999999999999999999"};
    assert(execute("FORWARD 2 LEFT"));
    for (size_t i = 0; i < sizeof bad / sizeof bad[0]; i++) {
        assert(!execute(bad[i]));
        assert(at(2, 0, 'N', true, 1) && logo.undo_len == 2);
    }

    // A line that would overflow int64_t is refused whole, even its first commands.
    reset();
    assert(execute("FORWARD 9223372036854775000"));
    assert(!execute("FORWARD 1 LEFT REPEAT 2 [ RIGHT FORWARD 9000 ]"));
    assert(at(9223372036854775000, 0, 'E', true, 1) && logo.undo_len == 1);
    assert(execute("LEFT LEFT FORWARD 9223372036854775000") && at(0, 0, 'W', true, 2));

    free(tokens.items);
    free(program.items);
    free(logo.segments);
    free(logo.undo);
    puts("all tests passed");
    return 0;
}
