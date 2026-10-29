// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main adventure_main
#include "solution.c"
#undef main

static State played(const char *const lines[], size_t count) {
    State state = new_game();
    for (size_t i = 0; i < count; i++) execute(&state, lines[i]);
    return state;
}

static bool holds(const ItemList *list, const Item items[], int count) {
    if (list->count != count) return false;
    for (int i = 0; i < count; i++)
        if (list->items[i] != items[i]) return false;
    return true;
}

int main(void) {
    // The game opens in the hall with nothing carried.
    State state = new_game();
    assert(state.room == HALL && state.inventory.count == 0 && !state.over);
    assert(holds(&state.here[HALL], (Item[]){LAMP}, 1));
    assert(holds(&state.here[GARDEN], (Item[]){ROSE, SPADE}, 2));

    // Every exit leads where the map says.
    const char *const ways[] = {"go west", "go east",  "go north", "go west",
                                "go east", "go north", "go south", "go south"};
    const Room rooms[] = {GARDEN, HALL, LIBRARY, CELLAR, LIBRARY, ATTIC, LIBRARY, HALL};
    state = new_game();
    for (size_t i = 0; i < sizeof ways / sizeof ways[0]; i++) {
        execute(&state, ways[i]);
        assert(state.room == rooms[i]);
    }

    // A refused go stays put; so does an unknown verb or an empty line.
    state = played((const char *const[]){"go south", "go up", "go", "go North", "dance", ""}, 6);
    assert(state.room == HALL && !state.over);

    // Take and drop move items in order, and only where they are.
    state = played((const char *const[]){"take lamp", "take lamp", "go west", "take spade",
                                         "take rose", "drop spade", "take sword", "drop key"},
                   8);
    assert(holds(&state.inventory, (Item[]){LAMP, ROSE}, 2));
    assert(holds(&state.here[GARDEN], (Item[]){SPADE}, 1) && state.here[HALL].count == 0);

    // A dropped item stays where it was left, on the end of the room's list.
    state = played((const char *const[]){"take lamp", "go north", "drop lamp", "go south"}, 4);
    assert(holds(&state.here[LIBRARY], (Item[]){BOOK, LAMP}, 2) && state.inventory.count == 0);

    // Surrounding whitespace is trimmed, and only the first space splits.
    state = played((const char *const[]){"  go   north ", "\ttake book\r", "take  old book"}, 3);
    assert(state.room == LIBRARY && holds(&state.inventory, (Item[]){BOOK}, 1));

    // Quit ends the game.
    state = played((const char *const[]){"quit"}, 1);
    assert(state.over);

    puts("all tests passed");
    return 0;
}
