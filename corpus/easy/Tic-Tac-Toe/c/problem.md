# Tic-Tac-Toe

Two players play Tic-Tac-Toe at one terminal, on stdin and stdout, one move per
line. The cells are numbered 0 to 8, row by row. `X` moves first and the turns
alternate; three in a row, column, or diagonal wins, and a full board with no
winner is a draw.

Playing:
- Before each move show the board and whose turn it is.
- A move is a cell number. Answer a line that is not a number, a number off the
  board, and a cell already marked; none costs the player the turn.
- When the game ends, show the final board, then a last line containing
  `X wins`, `O wins`, or `draw`, and stop. If input ends first, stop.

The game is the program's `SPEC.md`. Wording and the board's picture are yours;
only the cell numbers and the outcome line are fixed.

## A session

```text
. . .
. . .
. . .
X to move
> 4
. . .
. X .
. . .
O to move
> 4
illegal move: 4
. . .
. X .
. . .
O to move
> x
a cell 0-8, please
. . .
. X .
. . .
O to move
```

(`> ` marks the players' lines.)

## C contract

A whole program, `int main(void)`, with this core above it:

```c
typedef struct {
    char cells[9]; // 'X', 'O', or '\0' for empty
} Board;

static const int LINES[8][3];

static char to_move(Board board);
static char winner(Board board); // '\0' for nobody
static bool is_draw(Board board);
static bool play(Board board, int pos, Board *next);
static void render(Board board);
static bool cell_of(const char line[], int *pos); // a line's cell, 0-8
```

`play` writes the next board through `next` and returns `true`, or returns
`false` for a cell off the board, a marked cell, or a decided game. `Board
board = {}` is the empty board.

Differences from the Python implementation:
- No `legal_moves`: `play` checks the same conditions directly.
- `winner` returns `'\0'` rather than `None`, and `play` reports an illegal move
  by returning `false`, not by raising.
- `render` prints the board rather than returning a string.
