// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

#define main roman_main
#include "solution.c"
#undef main

// SPEC §1's place-value table, a different algorithm from the greedy walk.
static void positional(int n, char out[static NUMERAL_MAX + 1]) {
    static const char *const PLACES[4][10] = {
        {"", "M", "MM", "MMM"},
        {"", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"},
        {"", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"},
        {"", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"},
    };
    snprintf(out, NUMERAL_MAX + 1, "%s%s%s%s", PLACES[0][n / 1000], PLACES[1][n / 100 % 10],
             PLACES[2][n / 10 % 10], PLACES[3][n % 10]);
}

static bool reads_as(const char *line, long expected) {
    long value = 0;
    return number(line, &value) && value == expected;
}

int main(void) {
    // Every number both ways, and every numeral is canonical.
    for (int n = 1; n <= 3999; n++) {
        char expected[NUMERAL_MAX + 1], rendered[NUMERAL_MAX + 1];
        positional(n, expected);
        assert(to_roman(n, rendered) && strcmp(rendered, expected) == 0);
        assert(from_roman(expected) == n && canonical(expected));
    }

    // The render refuses numbers outside the domain.
    char out[NUMERAL_MAX + 1];
    assert(!to_roman(0, out) && !to_roman(4000, out) && !to_roman(-1, out));
    assert(!to_roman(LONG_MAX, out));

    // The scan totals any numeral letters; the round trip rejects the rest.
    assert(from_roman("IIII") == 4 && from_roman("IM") == 999);
    assert(from_roman("MMMMMMMMMMMMMMM") == 15000 && from_roman("") == 0);
    const char *not_canonical[] = {"IIII", "IC",  "VX",  "XM", "MMMM",
                                   "IXIX", "XLZ", "xiv", "",   "MMMMMMMMMMMMMMMMMMMM"};
    for (size_t i = 0; i < sizeof not_canonical / sizeof not_canonical[0]; i++)
        assert(!canonical(not_canonical[i]));

    // `strtol`'s reading of a number: a sign and leading spaces, nothing after.
    assert(reads_as("1990", 1990) && reads_as("0042", 42) && reads_as(" +12", 12));
    assert(reads_as("-1", -1) && reads_as("99999999999999999999", LONG_MAX));
    long value = 0;
    assert(!number("", &value) && !number("12X", &value) && !number("12 ", &value));
    assert(!number("XII", &value));

    puts("all tests passed");
    return 0;
}
