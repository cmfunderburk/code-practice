// Adventure Rooms: whole program.

#include <ctype.h>
#include <stdio.h>
#include <string.h>

typedef enum { HALL, LIBRARY, CELLAR, ATTIC, GARDEN, ROOM_COUNT } Room;
typedef enum { LAMP, BOOK, KEY, ROSE, SPADE, ITEM_COUNT } Item;
constexpr int NOWHERE = -1;
constexpr size_t LINE_CAP = 256;

static const char *const DESCRIPTIONS[ROOM_COUNT] = {
    [HALL] = "a dusty entrance hall", [LIBRARY] = "a book-lined library",
    [CELLAR] = "a damp stone cellar", [ATTIC] = "a cramped attic",
    [GARDEN] = "an overgrown garden",
};
static const char *const ITEM_NAMES[ITEM_COUNT] = {"lamp", "book", "key", "rose", "spade"};

static const char *const DIRECTIONS[] = {"north", "south", "east", "west"};
constexpr int DIRECTION_COUNT = 4;

static const int EXITS[ROOM_COUNT][DIRECTION_COUNT] = {
    [HALL] = {LIBRARY, NOWHERE, NOWHERE, GARDEN},    [LIBRARY] = {ATTIC, HALL, NOWHERE, CELLAR},
    [CELLAR] = {NOWHERE, NOWHERE, LIBRARY, NOWHERE}, [ATTIC] = {NOWHERE, LIBRARY, NOWHERE, NOWHERE},
    [GARDEN] = {NOWHERE, NOWHERE, HALL, NOWHERE},
};

typedef struct {
    Item items[ITEM_COUNT];
    int count;
} ItemList;

typedef struct {
    Room room;
    ItemList inventory;
    ItemList here[ROOM_COUNT];
    bool over;
} State;

static State new_game(void) {
    return (State){
        .room = HALL,
        .here =
            {
                [HALL] = {{LAMP}, 1},
                [LIBRARY] = {{BOOK}, 1},
                [CELLAR] = {{KEY}, 1},
                [GARDEN] = {{ROSE, SPADE}, 2},
            },
    };
}

static void append(ItemList *list, Item item) { list->items[list->count++] = item; }

static void remove_at(ItemList *list, int i) {
    memmove(&list->items[i], &list->items[i + 1], (size_t)(list->count - i - 1) * sizeof(Item));
    list->count--;
}

static int find(const ItemList *list, const char *name) {
    for (int i = 0; i < list->count; i++)
        if (strcmp(name, ITEM_NAMES[list->items[i]]) == 0) return i;
    return -1;
}

static void print_items(const ItemList *list) {
    for (int i = 0; i < list->count; i++)
        printf("%s%s", i > 0 ? ", " : "", ITEM_NAMES[list->items[i]]);
    puts(".");
}

static void look(const State *state) {
    printf("You are in %s.\nExits: ", DESCRIPTIONS[state->room]);
    const char *sep = "";
    for (int d = 0; d < DIRECTION_COUNT; d++) {
        if (EXITS[state->room][d] != NOWHERE) {
            printf("%s%s", sep, DIRECTIONS[d]);
            sep = ", ";
        }
    }
    puts(".");
    if (state->here[state->room].count > 0) {
        fputs("You see: ", stdout);
        print_items(&state->here[state->room]);
    }
}

typedef void Command(State *state, const char *arg);

static void do_look(State *state, const char *) { look(state); }

static void do_go(State *state, const char *arg) {
    if (*arg == '\0') {
        puts("Go where?");
        return;
    }
    for (int d = 0; d < DIRECTION_COUNT; d++) {
        if (strcmp(arg, DIRECTIONS[d]) == 0 && EXITS[state->room][d] != NOWHERE) {
            state->room = (Room)EXITS[state->room][d];
            look(state);
            return;
        }
    }
    puts("You can't go that way.");
}

static void do_take(State *state, const char *arg) {
    if (*arg == '\0') {
        puts("Take what?");
        return;
    }
    ItemList *here = &state->here[state->room];
    int i = find(here, arg);
    if (i < 0) {
        printf("There is no %s here.\n", arg);
        return;
    }
    append(&state->inventory, here->items[i]);
    remove_at(here, i);
    puts("Taken.");
}

static void do_drop(State *state, const char *arg) {
    if (*arg == '\0') {
        puts("Drop what?");
        return;
    }
    int i = find(&state->inventory, arg);
    if (i < 0) {
        printf("You are not carrying %s.\n", arg);
        return;
    }
    append(&state->here[state->room], state->inventory.items[i]);
    remove_at(&state->inventory, i);
    puts("Dropped.");
}

static void do_inventory(State *state, const char *) {
    if (state->inventory.count == 0) {
        puts("You are carrying nothing.");
        return;
    }
    fputs("You are carrying: ", stdout);
    print_items(&state->inventory);
}

static void do_quit(State *state, const char *) {
    state->over = true;
    puts("Goodbye.");
}

static const struct {
    const char *verb;
    Command *run;
} VERBS[] = {
    {"look", do_look},           {"go", do_go},     {"take", do_take}, {"drop", do_drop},
    {"inventory", do_inventory}, {"quit", do_quit},
};

static char *trim(char *text) {
    while (isspace((unsigned char)*text)) text++;
    char *end = text + strlen(text);
    while (end > text && isspace((unsigned char)end[-1])) end--;
    *end = '\0';
    return text;
}

static void execute(State *state, const char *line) {
    char copy[LINE_CAP];
    snprintf(copy, sizeof copy, "%s", line);
    char *verb = trim(copy);
    char *arg = strchr(verb, ' ');
    if (arg != nullptr) {
        *arg++ = '\0';
    } else {
        arg = verb + strlen(verb);
    }
    arg = trim(arg);
    for (size_t i = 0; i < sizeof VERBS / sizeof VERBS[0]; i++) {
        if (strcmp(verb, VERBS[i].verb) == 0) {
            VERBS[i].run(state, arg);
            return;
        }
    }
    printf("unknown verb: %s\n", verb);
}

int main(void) {
    State state = new_game();
    look(&state);
    char line[LINE_CAP];
    while (!state.over && fgets(line, sizeof line, stdin) != nullptr) {
        if (strchr(line, '\n') == nullptr && !feof(stdin)) {
            int ch;
            while ((ch = getchar()) != '\n' && ch != EOF) continue;
            puts("That's too long to understand.");
            continue;
        }
        line[strcspn(line, "\n")] = '\0';
        execute(&state, line);
    }
    return 0;
}
