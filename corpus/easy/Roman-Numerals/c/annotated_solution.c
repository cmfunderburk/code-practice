// Roman Numerals: whole program.
// From Python:
// 1. The table is the algorithm in both languages: thirteen value/symbol rows,
//    descending, with the subtractive pairs as rows of their own. Python's
//    tuple of pairs becomes an array of an untagged struct, and the walk is
//    the same greedy walk. [approach]
// 2. Python's `divmod` and `symbol * count` build each place's text, and
//    `"".join` glues the parts. C subtracts the value while it still fits and
//    copies the symbol into a buffer the caller owns. The longest numeral has
//    15 letters, so 16 bytes always suffice and nothing touches the heap.
//    [types]
// 3. Python's `to_roman` raises `ValueError("out of range: n")`, and the shell
//    prints the exception's text. C's returns `false`, and `answer` writes the
//    refusal itself. [errors]
// 4. Python's `VALUES` dictionary becomes a `switch` in `letter_value`, which
//    returns 0 for any other byte. That one function is both the parser's
//    lookup and the "is it a numeral letter" test. [library]
// 5. The canonical test is Python's round trip, `to_roman(from_roman(s)) == s`.
//    Python catches the `ValueError` for a value past 3999; here `to_roman`'s
//    `false` short-circuits the comparison. [approach]
// 6. Python's `input().strip().upper()` and `int(line)` become `fgets`,
//    `toupper`, and `strtol`, C's own reading of a line: `strtol` skips leading
//    spaces and takes a sign, and clamps a huge number to `LONG_MAX`. [text]

// `toupper` from `<ctype.h>`.
#include <ctype.h>
// `fgets`, `getchar`, `printf`, and `puts` from `<stdio.h>`.
#include <stdio.h>
// `strtol` from `<stdlib.h>`.
#include <stdlib.h>
// `memcpy`, `strchr`, `strcmp`, `strcspn`, and `strlen` from `<string.h>`.
#include <string.h>

constexpr size_t NUMERAL_MAX = 15;

static const struct {
    int value;
    const char *symbol;
} ROMAN_TABLE[] = {
    {1000, "M"}, {900, "CM"}, {500, "D"}, {400, "CD"}, {100, "C"}, {90, "XC"}, {50, "L"},
    {40, "XL"},  {10, "X"},   {9, "IX"},  {5, "V"},    {4, "IV"},  {1, "I"},
};

// `static NUMERAL_MAX + 1` in the parameter promises the caller passes at
// least 16 bytes, room for the longest numeral and its terminator.
static bool to_roman(long n, char out[static NUMERAL_MAX + 1]) {
    if (n < 1 || n > 3999) return false;
    size_t len = 0;
    for (size_t i = 0; i < sizeof ROMAN_TABLE / sizeof ROMAN_TABLE[0]; i++) {
        size_t width = strlen(ROMAN_TABLE[i].symbol);
        for (; n >= ROMAN_TABLE[i].value; n -= ROMAN_TABLE[i].value) {
            memcpy(out + len, ROMAN_TABLE[i].symbol, width);
            len += width;
        }
    }
    out[len] = '\0';
    return true;
}

static int letter_value(char ch) {
    switch (ch) {
    case 'I':
        return 1;
    case 'V':
        return 5;
    case 'X':
        return 10;
    case 'L':
        return 50;
    case 'C':
        return 100;
    case 'D':
        return 500;
    case 'M':
        return 1000;
    default:
        return 0;
    }
}

// A letter smaller than the next one is subtracted. At the last letter the
// next byte is the terminator, worth 0, so the last letter always adds. On
// non-canonical input the total can be anything a line's letters add up to.
static long from_roman(const char *numeral) {
    long total = 0;
    for (size_t i = 0; numeral[i]; i++) {
        int value = letter_value(numeral[i]);
        if (value < letter_value(numeral[i + 1])) {
            total -= value;
        } else {
            total += value;
        }
    }
    return total;
}

// Only numeral letters can be canonical; the round trip decides the rest.
static bool canonical(const char *numeral) {
    for (const char *ch = numeral; *ch; ch++)
        if (letter_value(*ch) == 0) return false;
    char rendered[NUMERAL_MAX + 1];
    return to_roman(from_roman(numeral), rendered) && strcmp(rendered, numeral) == 0;
}

// `end` stops at the first byte `strtol` didn't read: a number is a line it
// read to the end. Out of range, `strtol` returns `LONG_MAX` or `LONG_MIN`,
// which `to_roman` refuses like any other number past 3999.
static bool number(const char *line, long *value) {
    char *end = nullptr;
    *value = strtol(line, &end, 10);
    return end != line && *end == '\0';
}

// Python's shell for one line, folded to uppercase in place.
static void answer(char *line) {
    for (char *ch = line; *ch; ch++) *ch = (char)toupper((unsigned char)*ch);
    char numeral[NUMERAL_MAX + 1];
    long value = 0;
    if (number(line, &value)) {
        if (to_roman(value, numeral)) {
            puts(numeral);
        } else {
            puts("error: out of range (1-3999)");
        }
    } else if (canonical(line)) {
        printf("%ld\n", from_roman(line));
    } else {
        printf("error: not a number or a canonical numeral: %s\n", line);
    }
}

// Python's `input()` loop. A line longer than the buffer has no `\n` in it:
// the rest is read and dropped, and the line refused once. `strcspn` cuts the
// line end, `\r\n` included.
int main(void) {
    char line[64];
    while (fgets(line, sizeof line, stdin) != nullptr) {
        if (strchr(line, '\n') == nullptr && !feof(stdin)) {
            int ch;
            while ((ch = getchar()) != '\n' && ch != EOF) continue;
            puts("error: line too long");
            continue;
        }
        line[strcspn(line, "\r\n")] = '\0';
        answer(line);
    }
    return 0;
}
