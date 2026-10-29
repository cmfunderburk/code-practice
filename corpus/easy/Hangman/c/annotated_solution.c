// Hangman: whole program.
// From Python:
// 1. Python's `HangmanState` is a frozen dataclass holding a `frozenset` of
//    guesses. A C struct can't be frozen, but it can be copied: `guess` takes a
//    `Game` by value, changes its own copy, and writes the result out, so the
//    caller's value never changes underneath it. [mutation]
// 2. Python's `frozenset[str]` becomes `bool guessed[26]`, one flag per letter,
//    because the alphabet is fixed and tiny. [types]
// 3. Python raises `ValueError` for a repeated guess or a finished game, and
//    `main` catches it. C has no exceptions, so `guess` returns `false` and
//    leaves `*next` unwritten. [errors]
// 4. Python's `random.choice(WORDS)` picks from a generator seeded for you. C's
//    `rand()` must be seeded once with `srand`, conventionally from the clock,
//    and `rand() % WORD_COUNT` maps its range onto an index; the cast to
//    `size_t` keeps the arithmetic unsigned, like the count. [library]
// 5. Python's `input()` raises `EOFError` at end of input. `fgets` returns a
//    null pointer instead, and keeps the newline that `input()` drops. [io]
// 6. Python's `str.isalpha` and `str.lower` know Unicode. `<ctype.h>`'s
//    `isalpha` and `tolower` follow the C locale, which is ASCII until a
//    program calls `setlocale`, so `é` is two bytes and simply not one letter.
//    [text]

// `isalpha` and `tolower` from `<ctype.h>`.
#include <ctype.h>
// `fgets`, `printf`, and `puts` from `<stdio.h>`.
#include <stdio.h>
// `rand` and `srand` from `<stdlib.h>`.
#include <stdlib.h>
// `strcspn` and `strlen` from `<string.h>`.
#include <string.h>
// `time`, the seed, from `<time.h>`.
#include <time.h>

// `constexpr` names a compile-time constant (C23), like a module-level constant
// that the array sizes below can use.
constexpr int MAX_WRONG = 6;
constexpr size_t SECRET_MAX = 32;

// Python's `WORDS` tuple. String literals live for the whole run and must
// not be written to, so `const char *` points at them; the second `const`
// keeps the array itself from changing.
static const char *const WORDS[] = {"banana", "jigsaw", "kayak",  "oxygen",
                                    "puzzle", "python", "rhythm", "wizard"};
// `sizeof` the array over `sizeof` one element: Python's `len(WORDS)`, worked
// out at compile time.
constexpr size_t WORD_COUNT = sizeof WORDS / sizeof WORDS[0];

// Python's frozen `HangmanState`. `max_wrong` is the constant above, not a field.
// Copying a `Game` copies the pointer, not the letters, so copies share one
// secret. That is safe because no one can write through `const char *`.
typedef struct {
    const char *secret;
    bool guessed[26];
} Game;

// A compound literal zeroes every field it does not name: no guesses yet.
static Game new_game(const char *secret) { return (Game){.secret = secret}; }

// Python's `ch in set(state.secret)`, scanning the secret's letters.
// `const Game *` promises not to change the game (Beej 16.1.1).
static bool in_secret(const Game *game, int letter) {
    for (const char *ch = game->secret; *ch; ch++)
        if (*ch - 'a' == letter) return true;
    return false;
}

// Python's `len(state.guessed - set(state.secret))`: a guess that misses.
static int wrong_count(const Game *game) {
    int wrong = 0;
    for (int letter = 0; letter < 26; letter++)
        if (game->guessed[letter] && !in_secret(game, letter)) wrong++;
    return wrong;
}

// Python's `set(state.secret) <= state.guessed`.
static bool won(const Game *game) {
    for (const char *ch = game->secret; *ch; ch++)
        if (!game->guessed[*ch - 'a']) return false;
    return true;
}

// Python's `status(state) == "playing"`. Status is derived, never stored.
static bool playing(const Game *game) { return !won(game) && wrong_count(game) < MAX_WRONG; }

// Python's `masked` returns a new string. C writes into the caller's array;
// `[static SECRET_MAX + 1]` promises at least that many elements (Beej 33.2).
static void masked(const Game *game, char mask[static SECRET_MAX + 1]) {
    size_t i = 0;
    for (; game->secret[i]; i++) {
        char ch = game->secret[i];
        mask[i] = game->guessed[ch - 'a'] ? ch : '_';
    }
    mask[i] = '\0';
}

// `game` is a copy (Beej 8.5), so setting a flag here never touches the caller's
// value until the result is written through `next`.
static bool guess(Game game, char letter, Game *next) {
    if (!playing(&game) || game.guessed[letter - 'a']) return false;
    game.guessed[letter - 'a'] = true;
    *next = game;
    return true;
}

int main(void) {
    // Seeded once per run, so each game picks its own word.
    srand((unsigned)time(nullptr));
    Game game = new_game(WORDS[(size_t)rand() % WORD_COUNT]);
    // A guess fits; a longer line arrives in pieces, each one not a letter.
    char line[64];
    while (playing(&game)) {
        char mask[SECRET_MAX + 1];
        masked(&game, mask);
        printf("%s  wrong: %d/%d\n", mask, wrong_count(&game), MAX_WRONG);
        if (fgets(line, sizeof line, stdin) == nullptr) {
            printf("you quit! the word was %s\n", game.secret);
            return 0;
        }
        // Cut the newline, and a Windows `\r` before it.
        line[strcspn(line, "\r\n")] = '\0';
        // `<ctype.h>` takes an `unsigned char` value: a negative `char` such as
        // a byte of `é` would be undefined behavior.
        if (strlen(line) != 1 || !isalpha((unsigned char)line[0])) {
            puts("one letter a-z, please");
            continue;
        }
        char letter = (char)tolower((unsigned char)line[0]);
        // Python's `state = guess(state, letter)`. Passing `game` by value and
        // `&game` as the output is safe: the copy is made first.
        if (!guess(game, letter, &game)) printf("already guessed: %c\n", letter);
    }
    printf("you %s! the word was %s\n", won(&game) ? "won" : "lost", game.secret);
    return 0;
}
