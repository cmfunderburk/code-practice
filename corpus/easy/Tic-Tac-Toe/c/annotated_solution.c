// Tic-Tac-Toe: whole program.
// From Python:
// 1. Python's board is an immutable `tuple` of nine cells. A C array can't be
//    passed or returned by value, but a struct holding one can, so `Board`
//    wraps the nine cells. Every predicate takes a 9-byte copy, so none can
//    change the caller's board, and `play` writes the next board through
//    `next`, as Python's `play` returns a new tuple. [mutation]
// 2. Python marks an empty cell with `""`. Here it is `'\0'`, so the
//    zero-filled `Board board = {}` is Python's `EMPTY_BOARD`. [types]
// 3. Python's `winner` returns `str | None`. C has no `None` for a `char`, so
//    `winner` returns `'\0'` when nobody has won, and `if (winner(board))`
//    reads like Python's `is not None`. [absence]
// 4. Python's `play` checks `pos in legal_moves(board)`. Nothing else in this
//    program lists the legal moves, so `play` tests the same three conditions
//    itself: the cell is on the board, nobody has won, and the cell is empty.
//    [approach]
// 5. Python raises `ValueError` for an illegal move. C returns `false`, leaves
//    `*next` unwritten, and `main` prints the message. [errors]
// 6. Python's shell reads a move with `int(line)` and lets `play` reject a
//    number off the board. C's `strtol` is the parser here: it reports where it
//    stopped, so a line with anything after the number is caught, and `cell_of`
//    rejects a number outside 0-8 before it is narrowed to an `int`. [parsing]
// 7. Python's `input()` raises `EOFError` at end of input. `fgets` returns a
//    null pointer instead, and keeps the newline that `input()` drops. [io]

// `fgets`, `printf`, `putchar`, and `puts` from `<stdio.h>`.
#include <stdio.h>
// `strtol` from `<stdlib.h>`.
#include <stdlib.h>
// `strcspn` from `<string.h>`.
#include <string.h>

// Python's `tuple[str, ...]`: `'X'`, `'O'`, or `'\0'` for an empty cell.
typedef struct {
    char cells[9];
} Board;

// Python's `_LINES`, a two-dimensional array (Beej 6.5): eight lines of three
// cells each, written with nested braces (Beej 20.1).
static const int LINES[8][3] = {{0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {0, 3, 6},
                                {1, 4, 7}, {2, 5, 8}, {0, 4, 8}, {2, 4, 6}};

// Python's `board.count("X") == board.count("O")`: the mover is derived from
// the marks, never stored.
static char to_move(Board board) {
    int x = 0;
    int o = 0;
    for (int i = 0; i < 9; i++) {
        if (board.cells[i] == 'X') x++;
        if (board.cells[i] == 'O') o++;
    }
    return x == o ? 'X' : 'O';
}

// Python's `board[a] and board[a] == board[b] == board[c]`. C has no chained
// comparison, so it is two `==` joined by `&&`.
static char winner(Board board) {
    for (int i = 0; i < 8; i++) {
        char mark = board.cells[LINES[i][0]];
        if (mark && mark == board.cells[LINES[i][1]] && mark == board.cells[LINES[i][2]])
            return mark;
    }
    return '\0';
}

// Python's `winner(board) is None and "" not in board`.
static bool is_draw(Board board) {
    if (winner(board)) return false;
    for (int i = 0; i < 9; i++)
        if (!board.cells[i]) return false;
    return true;
}

// `board` is a copy (Beej 8.5), so marking a cell here changes nothing the
// caller holds until the result is written through `next`.
static bool play(Board board, int pos, Board *next) {
    if (pos < 0 || pos > 8 || winner(board) || board.cells[pos]) return false;
    board.cells[pos] = to_move(board);
    *next = board;
    return true;
}

// Python's `_render`: `.` for an empty cell, a space between cells, and a
// newline after every third.
static void render(Board board) {
    for (int i = 0; i < 9; i++) {
        putchar(board.cells[i] ? board.cells[i] : '.');
        putchar(i % 3 == 2 ? '\n' : ' ');
    }
}

// A move line's cell. `strtol` skips leading spaces, reads an optional sign
// and digits, and points `end` just past them; `end == line` means no digits,
// and `*end != '\0'` means something followed them. A number too large for a
// `long` comes back as `LONG_MAX`, which the range check rejects too.
static bool cell_of(const char line[], int *pos) {
    char *end;
    long value = strtol(line, &end, 10);
    if (end == line || *end != '\0' || value < 0 || value > 8) return false;
    *pos = (int)value;
    return true;
}

int main(void) {
    Board board = {};
    char line[64];
    while (!winner(board) && !is_draw(board)) {
        render(board);
        printf("%c to move\n", to_move(board));
        if (fgets(line, sizeof line, stdin) == nullptr) {
            puts("game abandoned");
            return 0;
        }
        // Cut the line end, `\n` or `\r\n`. A line longer than the buffer
        // arrives in pieces, and each piece is answered as not a cell.
        line[strcspn(line, "\r\n")] = '\0';
        int pos = 0;
        // The `else if` is Python's `board = play(board, pos)`. Passing `board`
        // by value and `&board` as the output is safe: the copy is made first.
        if (!cell_of(line, &pos)) {
            puts("a cell 0-8, please");
        } else if (!play(board, pos, &board)) {
            printf("illegal move: %d\n", pos);
        }
    }
    render(board);
    char mark = winner(board);
    if (mark) {
        printf("%c wins!\n", mark);
    } else {
        puts("draw");
    }
    return 0;
}
