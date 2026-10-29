// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main life_main
#include "solution.c"
#undef main

static World world;
static int generations;

static bool reads(const char *pattern) {
    FILE *in = tmpfile();
    assert(in != nullptr);
    fputs(pattern, in);
    rewind(in);
    bool ok = read_world(in, &world, &generations);
    fclose(in);
    return ok;
}

static bool shows(const char *rows) {
    for (int r = 0; r < world.rows; r++, rows++) {
        for (int c = 0; c < world.cols; c++, rows++)
            if (world.live[r][c] != (*rows == '#')) return false;
    }
    return true;
}

int main(void) {
    // The blinker oscillates with period 2.
    assert(reads("5 5 2\n.....\n.....\n.###.\n.....\n.....\n") && generations == 2);
    step(&world);
    assert(shows("..... ..#.. ..#.. ..#.. ....."));
    step(&world);
    assert(shows("..... ..... .###. ..... ....."));

    // A block is still; cells past the edge are dead, so a blinker on the top
    // edge loses its off-grid birth and a lone corner cell dies.
    assert(reads("4 4 1\n....\n.##.\n.##.\n....") && (step(&world), shows(".... .##. .##. ....")));
    assert(reads("3 3 1\n###\n...\n...\n") && (step(&world), shows(".#. .#. ...")));
    assert(reads("1 1 1\n#\n") && (step(&world), shows(".")));

    // A glider moves one cell diagonally every four generations.
    assert(reads("5 5 4\n.#...\n..#..\n###..\n.....\n.....\n"));
    for (int g = 0; g < 4; g++) step(&world);
    assert(shows("..... ..#.. ...#. .###. ....."));

    // The header's spacing is sscanf's: any whitespace, and a sign.
    assert(reads("2  3 +0\n#.#\n.#.\n") && generations == 0 && shows("#.# .#."));

    // Bad patterns are refused.
    const char *bad[] = {
        "",
        "\n",
        "3 3\n...\n...\n...\n",
        "3 3 1 1\n...\n...\n...\n",
        "3 x 1\n...\n...\n...\n",
        "3 3 -1\n...\n...\n...\n",
        "0 3 1\n",
        "1 101 "
        "0\n......................................................................................."
        "..............\n",
        "1 1 1001\n.\n",
        "3 3 1\n...\n..\n...\n",
        "3 3 1\n...\n....\n...\n",
        "3 3 1\n...\n.x.\n...\n",
        "3 3 1\n...\n...\n",
        "3 3 1\n...\n...\n...\n...\n",
        "3 3 1\n...\n...\n...\n\n",
        "1 3 1\r\n...\r\n",
    };
    for (size_t i = 0; i < sizeof bad / sizeof bad[0]; i++) assert(!reads(bad[i]));

    puts("all tests passed");
    return 0;
}
