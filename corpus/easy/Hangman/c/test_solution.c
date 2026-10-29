// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main hangman_main
#include "solution.c"
#undef main

static Game guessed(Game game, const char *letters) {
    for (const char *ch = letters; *ch; ch++) assert(guess(game, *ch, &game));
    return game;
}

static bool mask_is(const Game *game, const char *expected) {
    char mask[SECRET_MAX + 1];
    masked(game, mask);
    return strcmp(mask, expected) == 0;
}

int main(void) {
    // A hit reveals every occurrence; a miss counts against the budget.
    Game game = new_game("banana");
    assert(mask_is(&game, "______") && playing(&game));
    game = guessed(game, "a");
    assert(mask_is(&game, "_a_a_a") && wrong_count(&game) == 0);
    game = guessed(game, "xn");
    assert(mask_is(&game, "_anana") && wrong_count(&game) == 1);
    game = guessed(game, "b");
    assert(mask_is(&game, "banana") && won(&game) && !playing(&game));

    // The sixth miss loses, not the fifth.
    game = guessed(new_game("banana"), "cdefg");
    assert(wrong_count(&game) == 5 && playing(&game));
    game = guessed(game, "h");
    assert(wrong_count(&game) == 6 && !won(&game) && !playing(&game));

    // A repeated guess is refused, hit or miss, and leaves *next alone.
    game = guessed(new_game("banana"), "az");
    Game untouched = new_game("io");
    assert(!guess(game, 'a', &untouched) && !guess(game, 'z', &untouched));
    assert(untouched.secret[0] == 'i' && !untouched.guessed[0]);

    // A finished game refuses every guess.
    game = guessed(new_game("io"), "io");
    assert(won(&game) && !guess(game, 'z', &game));
    game = guessed(new_game("io"), "abcdef");
    assert(!playing(&game) && !guess(game, 'i', &game));

    // The caller's game is a copy: guessing never changes it.
    Game before = new_game("banana");
    guessed(before, "a");
    assert(!before.guessed['a' - 'a']);

    // Every built-in word fits the mask and has two different letters.
    for (size_t i = 0; i < WORD_COUNT; i++) {
        size_t len = strlen(WORDS[i]);
        assert(len >= 2 && len <= SECRET_MAX);
        assert(strspn(WORDS[i], "abcdefghijklmnopqrstuvwxyz") == len);
        assert(strspn(WORDS[i], (char[]){WORDS[i][0], '\0'}) < len);
    }

    puts("all tests passed");
    return 0;
}
