// Adventure Rooms: whole program.
// From Python:
// 1. Python's world is dicts keyed by room name, and its state a dict of lists
//    of item names. Only five rooms and five items ever exist, so C numbers them
//    with `enum`s: the world is arrays indexed by room, and each room's items
//    and the inventory are fixed lists of item numbers. Nothing in the game
//    touches the heap. [approach]
// 2. Python's handlers return `(state, output)`, and `main` prints the output.
//    C handlers change the state through a pointer and print their own lines,
//    since returning text would need an allocation. [mutation]
// 3. Python's `execute` raises `ValueError` for an unknown verb, and `main`
//    prints it. C prints `unknown verb: ...` itself and changes nothing.
//    [errors]
// 4. Python's `input()` and `line.strip()` become `fgets` into a fixed buffer
//    and a `trim` over `isspace`, which covers the ASCII whitespace but not
//    U+00A0 and the other Unicode spaces Python also strips. [text]
// 5. Python's `partition(" ")` becomes `strchr` for the first space and a
//    `'\0'` written over it, so the verb and the argument are both C strings
//    inside one copy of the line. [text]

// `isspace` from `<ctype.h>`.
#include <ctype.h>
// `fgets`, `fputs`, `getchar`, `printf`, `puts`, and `snprintf` from `<stdio.h>`.
#include <stdio.h>
// `memmove`, `strchr`, `strcmp`, `strcspn`, and `strlen` from `<string.h>`.
#include <string.h>

// Python's room and item names become numbers (Beej 22). `NOWHERE` marks a
// missing exit.
typedef enum { HALL, LIBRARY, CELLAR, ATTIC, GARDEN, ROOM_COUNT } Room;
typedef enum { LAMP, BOOK, KEY, ROSE, SPADE, ITEM_COUNT } Item;
constexpr int NOWHERE = -1;
// A command is a few words; a longer line is refused whole.
constexpr size_t LINE_CAP = 256;

static const char *const DESCRIPTIONS[ROOM_COUNT] = {
    [HALL] = "a dusty entrance hall", [LIBRARY] = "a book-lined library",
    [CELLAR] = "a damp stone cellar", [ATTIC] = "a cramped attic",
    [GARDEN] = "an overgrown garden",
};
static const char *const ITEM_NAMES[ITEM_COUNT] = {"lamp", "book", "key", "rose", "spade"};

// Python's `DIRECTIONS`, in the order the look text lists exits.
static const char *const DIRECTIONS[] = {"north", "south", "east", "west"};
constexpr int DIRECTION_COUNT = 4;

// Python's `EXITS`: for each room, where each direction leads.
static const int EXITS[ROOM_COUNT][DIRECTION_COUNT] = {
    [HALL] = {LIBRARY, NOWHERE, NOWHERE, GARDEN},    [LIBRARY] = {ATTIC, HALL, NOWHERE, CELLAR},
    [CELLAR] = {NOWHERE, NOWHERE, LIBRARY, NOWHERE}, [ATTIC] = {NOWHERE, LIBRARY, NOWHERE, NOWHERE},
    [GARDEN] = {NOWHERE, NOWHERE, HALL, NOWHERE},
};

// An ordered list of items. Five items exist, so five slots always suffice.
typedef struct {
    Item items[ITEM_COUNT];
    int count;
} ItemList;

// Python's state dict.
typedef struct {
    Room room;
    ItemList inventory;
    ItemList here[ROOM_COUNT];
    bool over;
} State;

// Python's `new_game`, with `START_ITEMS` as designated initializers (Beej 8.2).
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

// Python's `list.remove`: close the gap so the order is kept.
static void remove_at(ItemList *list, int i) {
    memmove(&list->items[i], &list->items[i + 1], (size_t)(list->count - i - 1) * sizeof(Item));
    list->count--;
}

// The index in `list` of the item named `name`, or -1.
static int find(const ItemList *list, const char *name) {
    for (int i = 0; i < list->count; i++)
        if (strcmp(name, ITEM_NAMES[list->items[i]]) == 0) return i;
    return -1;
}

// Python's `", ".join(names)`, then `.` and a newline.
static void print_items(const ItemList *list) {
    for (int i = 0; i < list->count; i++)
        printf("%s%s", i > 0 ? ", " : "", ITEM_NAMES[list->items[i]]);
    puts(".");
}

// Python's `_look`, printed line by line rather than joined.
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

// The type of every verb handler, so the table below can hold them (Beej 23.7).
// Handlers that ignore the argument leave its parameters unnamed (C23).
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

// Python's `VERBS` dict, as an array of an untagged struct type (Beej 20.2).
static const struct {
    const char *verb;
    Command *run;
} VERBS[] = {
    {"look", do_look},           {"go", do_go},     {"take", do_take}, {"drop", do_drop},
    {"inventory", do_inventory}, {"quit", do_quit},
};

// Python's `text.strip()`, for the ASCII whitespace `isspace` knows: skip it at
// the front, and cut it at the back with a `'\0'`.
static char *trim(char *text) {
    while (isspace((unsigned char)*text)) text++;
    char *end = text + strlen(text);
    while (end > text && isspace((unsigned char)end[-1])) end--;
    *end = '\0';
    return text;
}

// Python's `execute`: trim, split at the first space, trim the argument, and
// run the verb's handler. The line is copied first, so a caller's string is
// never written to.
static void execute(State *state, const char *line) {
    char copy[LINE_CAP];
    snprintf(copy, sizeof copy, "%s", line);
    char *verb = trim(copy);
    // Python's `partition(" ")`: with no space, the argument is the empty string
    // at the verb's end.
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

// Python's `input()` loop. A line too long for the buffer has no `\n`: the
// rest is read and dropped, and the line refused once. `strcspn` cuts the `\n`.
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
