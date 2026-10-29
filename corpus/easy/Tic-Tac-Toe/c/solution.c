// Tic-Tac-Toe: whole program.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char cells[9];
} Board;

static const int LINES[8][3] = {{0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {0, 3, 6},
                                {1, 4, 7}, {2, 5, 8}, {0, 4, 8}, {2, 4, 6}};

static char to_move(Board board) {
    int x = 0;
    int o = 0;
    for (int i = 0; i < 9; i++) {
        if (board.cells[i] == 'X') x++;
        if (board.cells[i] == 'O') o++;
    }
    return x == o ? 'X' : 'O';
}

static char winner(Board board) {
    for (int i = 0; i < 8; i++) {
        char mark = board.cells[LINES[i][0]];
        if (mark && mark == board.cells[LINES[i][1]] && mark == board.cells[LINES[i][2]])
            return mark;
    }
    return '\0';
}

static bool is_draw(Board board) {
    if (winner(board)) return false;
    for (int i = 0; i < 9; i++)
        if (!board.cells[i]) return false;
    return true;
}

static bool play(Board board, int pos, Board *next) {
    if (pos < 0 || pos > 8 || winner(board) || board.cells[pos]) return false;
    board.cells[pos] = to_move(board);
    *next = board;
    return true;
}

static void render(Board board) {
    for (int i = 0; i < 9; i++) {
        putchar(board.cells[i] ? board.cells[i] : '.');
        putchar(i % 3 == 2 ? '\n' : ' ');
    }
}

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
        line[strcspn(line, "\r\n")] = '\0';
        int pos = 0;
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
