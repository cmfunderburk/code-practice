// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main tic_tac_toe_main
#include "solution.c"
#undef main

static Board played(const int moves[], size_t count) {
    Board board = {};
    for (size_t i = 0; i < count; i++) assert(play(board, moves[i], &board));
    return board;
}

#define PLAYED(...)                                                                                \
    played((const int[]){__VA_ARGS__}, sizeof((const int[]){__VA_ARGS__}) / sizeof(int))

int main(void) {
    // X moves first, and the turns alternate.
    Board board = {};
    assert(to_move(board) == 'X' && !winner(board) && !is_draw(board));
    board = PLAYED(4);
    assert(board.cells[4] == 'X' && to_move(board) == 'O');

    // Every row, column, and diagonal wins.
    for (int i = 0; i < 8; i++) {
        Board line = {};
        for (int k = 0; k < 3; k++) line.cells[LINES[i][k]] = 'O';
        assert(winner(line) == 'O' && !is_draw(line));
    }

    // X wins on the top row; O on the anti-diagonal.
    assert(winner(PLAYED(0, 3, 1, 4, 2)) == 'X');
    assert(winner(PLAYED(0, 2, 1, 4, 8, 6)) == 'O');

    // A full board with no line is a draw; one with a line is a win.
    board = PLAYED(0, 1, 2, 4, 3, 5, 7, 6, 8);
    assert(is_draw(board) && !winner(board));
    board = PLAYED(0, 1, 2, 3, 4, 5, 7, 6, 8);
    assert(winner(board) == 'X' && !is_draw(board));

    // A marked cell, a cell off the board, and any move after a win are
    // refused, and *next is left alone.
    board = PLAYED(4);
    Board untouched = {};
    assert(!play(board, 4, &untouched) && !play(board, 9, &untouched));
    assert(!play(board, -1, &untouched));
    assert(!play(PLAYED(0, 3, 1, 4, 2), 8, &untouched));
    assert(memcmp(&untouched, &(Board){}, sizeof untouched) == 0);

    // The caller's board is a copy: playing never changes it.
    Board before = PLAYED(4);
    Board after;
    assert(play(before, 0, &after));
    assert(!before.cells[0] && after.cells[0] == 'O');

    // A move line is a number from 0 to 8.
    int pos = -1;
    assert(cell_of("0", &pos) && pos == 0);
    assert(cell_of("8", &pos) && pos == 8);
    const char *not_cells[] = {"", "9", "-1", "x", "4x", "4.5", "4 ", "99999999999999999999"};
    for (size_t i = 0; i < sizeof not_cells / sizeof not_cells[0]; i++)
        assert(!cell_of(not_cells[i], &pos));

    puts("all tests passed");
    return 0;
}
