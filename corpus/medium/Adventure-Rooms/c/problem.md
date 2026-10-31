# Adventure Rooms

Run a five-room text adventure over stdin and stdout, one command per line. The
player starts in the hall with nothing.

| Room | Exits | Items at the start |
| --- | --- | --- |
| hall | north → library, west → garden | `lamp` |
| library | north → attic, south → hall, west → cellar | `book` |
| cellar | east → library | `key` |
| attic | south → library | none |
| garden | east → hall | `rose`, `spade` |

- On start, describe the hall. Then answer each line until `quit` or the end of
  input, which ends the session without another word.
- A line is a verb and an optional argument, split at the first space after
  surrounding whitespace is trimmed; the argument is trimmed too.
- The verbs are `look`, `go <direction>`, `take <item>`, `drop <item>`,
  `inventory`, and `quit`. A taken item leaves the room for the end of the
  inventory; a dropped item goes on the end of the room's list.
- A room's description names the room, lists its exits in the order north,
  south, east, west, and lists the items it holds. `inventory` lists what you
  carry, in order.
- A command that can't be carried out (no such exit, item, or verb) is answered
  and changes nothing.

The world and its rules are the program's `SPEC.md`. Descriptions and wording
are each version's own; SPEC §5 fixes little more than the room and item
names an answer contains.

## A session

```text
You are in a dusty entrance hall.
Exits: north, west.
You see: lamp.
> take lamp
Taken.
> go north
You are in a book-lined library.
Exits: north, south, west.
You see: book.
> dance
unknown verb: dance
> inventory
You are carrying: lamp.
> quit
Goodbye.
```

(`> ` marks the user's lines.)

## C contract

A whole program, `int main(void)`, with this core above it:

```c
typedef enum { HALL, LIBRARY, CELLAR, ATTIC, GARDEN, ROOM_COUNT } Room;
typedef enum { LAMP, BOOK, KEY, ROSE, SPADE, ITEM_COUNT } Item;

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

static State new_game(void);
static void execute(State *state, const char *line);
```

`execute` runs one line, printing its answer, and changes `*state` as the rules
say; a refused command prints its answer and changes nothing.

Differences from the Python version:
- Handlers change the state through a pointer and print their own lines, where
  Python's handlers return `(state, output)`; an unknown verb prints instead of
  raising.
- The verb table is fixed when the program compiles; nothing can add a verb
  while the program runs.
