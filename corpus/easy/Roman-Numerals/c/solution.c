// Roman Numerals: whole program.

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

constexpr size_t NUMERAL_MAX = 15;

static const struct {
    int value;
    const char *symbol;
} ROMAN_TABLE[] = {
    {1000, "M"}, {900, "CM"}, {500, "D"}, {400, "CD"}, {100, "C"}, {90, "XC"}, {50, "L"},
    {40, "XL"},  {10, "X"},   {9, "IX"},  {5, "V"},    {4, "IV"},  {1, "I"},
};

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

static bool canonical(const char *numeral) {
    for (const char *ch = numeral; *ch; ch++)
        if (letter_value(*ch) == 0) return false;
    char rendered[NUMERAL_MAX + 1];
    return to_roman(from_roman(numeral), rendered) && strcmp(rendered, numeral) == 0;
}

static bool number(const char *line, long *value) {
    char *end = nullptr;
    *value = strtol(line, &end, 10);
    return end != line && *end == '\0';
}

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
