// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main calculator_main
#include "solution.c"
#undef main

static Value value_of(const char *text) {
    Value value = {};
    const char *error = nullptr;
    assert(calculate(text, strlen(text), &value, &error));
    return value;
}

static bool is_integer(const char *text, int64_t expected) {
    Value value = value_of(text);
    return !value.is_float && value.integer == expected;
}

static bool is_real(const char *text, double expected) {
    Value value = value_of(text);
    double diff = value.real - expected;
    return value.is_float && diff < 1e-12 && diff > -1e-12;
}

static bool fails(const char *text) {
    Value value = {};
    const char *error = nullptr;
    return !calculate(text, strlen(text), &value, &error) && error != nullptr;
}

int main(void) {
    // Precedence, parentheses, and left associativity.
    assert(is_integer("2+3*4", 14) && is_integer("(2+3)*4", 20));
    assert(is_integer("20-5-3", 12) && is_integer("2-3+4", 3));
    assert(is_real("100/5/2", 10.0));

    // Unary minus nests and binds tighter than any binary operator.
    assert(is_integer("--3", 3) && is_integer("2*-3", -6) && is_integer("-(2+3)", -5));
    assert(is_integer("2--3", 5));

    // Integers stay integers; `/` is true division and makes a float.
    assert(is_real("7/2", 3.5) && is_real("8/2", 4.0) && is_real("1/3", 1.0 / 3.0));
    assert(is_real("7/2*2", 7.0));

    // Spaces and tabs are ignored; leading zeros are allowed.
    assert(is_integer("  2 +\t3 ", 5) && is_integer("007+1", 8));

    // Division by zero, integer or float, is an error.
    assert(fails("1/0") && fails("0/0") && fails("1/(1/2-1/2)"));

    // Lines outside the grammar are errors.
    const char *malformed[] = {"",    "   ", "2+", "(2",   "2)*3", "1 2",
                               "2^3", "*3",  "()", "2//3", "2\r",  "2 + x"};
    for (size_t i = 0; i < sizeof malformed / sizeof malformed[0]; i++) assert(fails(malformed[i]));

    // `int64_t` overflow is reported, not undefined.
    assert(is_integer("9223372036854775807", INT64_MAX));
    assert(fails("9223372036854775808"));
    assert(fails("9223372036854775807+1") && fails("-9223372036854775807-2"));

    puts("all tests passed");
    return 0;
}
