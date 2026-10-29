// Hangman: whole program.

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

constexpr int MAX_WRONG = 6;
constexpr size_t SECRET_MAX = 32;

static const char *const WORDS[] = {"banana", "jigsaw", "kayak",  "oxygen",
                                    "puzzle", "python", "rhythm", "wizard"};
constexpr size_t WORD_COUNT = sizeof WORDS / sizeof WORDS[0];

typedef struct {
    const char *secret;
    bool guessed[26];
} Game;

static Game new_game(const char *secret) { return (Game){.secret = secret}; }

static bool in_secret(const Game *game, int letter) {
    for (const char *ch = game->secret; *ch; ch++)
        if (*ch - 'a' == letter) return true;
    return false;
}

static int wrong_count(const Game *game) {
    int wrong = 0;
    for (int letter = 0; letter < 26; letter++)
        if (game->guessed[letter] && !in_secret(game, letter)) wrong++;
    return wrong;
}

static bool won(const Game *game) {
    for (const char *ch = game->secret; *ch; ch++)
        if (!game->guessed[*ch - 'a']) return false;
    return true;
}

static bool playing(const Game *game) { return !won(game) && wrong_count(game) < MAX_WRONG; }

static void masked(const Game *game, char mask[static SECRET_MAX + 1]) {
    size_t i = 0;
    for (; game->secret[i]; i++) {
        char ch = game->secret[i];
        mask[i] = game->guessed[ch - 'a'] ? ch : '_';
    }
    mask[i] = '\0';
}

static bool guess(Game game, char letter, Game *next) {
    if (!playing(&game) || game.guessed[letter - 'a']) return false;
    game.guessed[letter - 'a'] = true;
    *next = game;
    return true;
}

int main(void) {
    srand((unsigned)time(nullptr));
    Game game = new_game(WORDS[(size_t)rand() % WORD_COUNT]);
    char line[64];
    while (playing(&game)) {
        char mask[SECRET_MAX + 1];
        masked(&game, mask);
        printf("%s  wrong: %d/%d\n", mask, wrong_count(&game), MAX_WRONG);
        if (fgets(line, sizeof line, stdin) == nullptr) {
            printf("you quit! the word was %s\n", game.secret);
            return 0;
        }
        line[strcspn(line, "\r\n")] = '\0';
        if (strlen(line) != 1 || !isalpha((unsigned char)line[0])) {
            puts("one letter a-z, please");
            continue;
        }
        char letter = (char)tolower((unsigned char)line[0]);
        if (!guess(game, letter, &game)) printf("already guessed: %c\n", letter);
    }
    printf("you %s! the word was %s\n", won(&game) ? "won" : "lost", game.secret);
    return 0;
}
