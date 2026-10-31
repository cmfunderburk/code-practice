// Game of Life: whole program.
// From Python:
// 1. Python stores the live cells as a `set` of `(r, c)` tuples. C has no set
//    type, and the grid is at most 100 × 100, so this version stores one
//    `bool` per cell: a dense grid.
//    [approach]
// 2. Python's `step` returns a new set. Here `step` updates the grid in place,
//    which is safe because every count is taken before any cell changes.
//    [mutation]
// 3. Python reads all of stdin, splits it into lines, and then validates. This
//    parser reads one line at a time with `fgets` into a buffer one grid row
//    long, and stops at the first bad line. A `\r` before the `\n` stays in the
//    line, where Python's `splitlines` would drop it, so `\r\n` input is bad
//    input here. [io]
// 4. Python's `int` reads any length of digits; `sscanf("%d")` reads an `int`.
//    [integers]

// `FILE`, `fgets`, `sscanf`, `printf`, `fwrite`, `puts`, and `stdout` from
// `<stdio.h>`.
#include <stdio.h>
// `strcspn` and `strlen` from `<string.h>`.
#include <string.h>

constexpr int MAX_SIDE = 100;
constexpr int MAX_GENERATIONS = 1000;

// Every board fits the maximum size; `rows` and `cols` say how much of it is used.
typedef struct {
    int rows, cols;
    bool live[MAX_SIDE][MAX_SIDE];
} World;

// Counts neighbors as Python's `Counter` does: each live cell adds one to each of
// its eight neighbors. `counts` has a one-cell border on every side, so
// cell (r, c) is counted at [r + 1][c + 1], and its neighbors at offsets 0..2.
static void step(World *world) {
    // `= {}` zero-fills the whole array (C23).
    unsigned char counts[MAX_SIDE + 2][MAX_SIDE + 2] = {};
    for (int r = 0; r < world->rows; r++)
        for (int c = 0; c < world->cols; c++)
            if (world->live[r][c])
                for (int dr = 0; dr < 3; dr++)
                    for (int dc = 0; dc < 3; dc++)
                        if (dr != 1 || dc != 1) counts[r + dr][c + dc]++;
    // Python keeps `(r, c)` when `n == 3 or (n == 2 and (r, c) in live)`. Only the
    // interior is read, which is Python's `0 <= r < rows and 0 <= c < cols` clip.
    for (int r = 0; r < world->rows; r++) {
        for (int c = 0; c < world->cols; c++) {
            int n = counts[r + 1][c + 1];
            world->live[r][c] = n == 3 || (n == 2 && world->live[r][c]);
        }
    }
}

// Python's `splitlines()` for one line: at most `MAX_SIDE` characters, without
// the `'\n'`. `fgets` stops after `'\n'` or when the buffer is full, so a line
// that fills it without a `'\n'` is too long for any grid (Beej 12.5.1).
static bool read_line(FILE *in, char line[static MAX_SIDE + 2]) {
    if (fgets(line, MAX_SIDE + 2, in) == nullptr) return false;
    size_t len = strcspn(line, "\n");
    if (line[len] != '\n' && len > MAX_SIDE) return false;
    line[len] = '\0';
    return true;
}

// Python's `parse_input`, filling the world instead of returning grid lines. It
// reads from any stream, not only stdin.
static bool read_world(FILE *in, World *world, int *generations) {
    char line[MAX_SIDE + 2];
    // Python's `map(int, header.split())` into three names. `%d` skips leading
    // whitespace and takes a sign, and a fourth match, `%c` after any space,
    // means the line holds more than three fields. A number too big for `int`
    // is undefined behavior in `sscanf`; `strtol` would report it (Beej 11.1).
    char extra;
    if (!read_line(in, line) ||
        sscanf(line, "%d %d %d %c", &world->rows, &world->cols, generations, &extra) != 3)
        return false;
    if (world->rows < 1 || world->rows > MAX_SIDE || world->cols < 1 || world->cols > MAX_SIDE ||
        *generations < 0 || *generations > MAX_GENERATIONS)
        return false;
    // Python's `len(line) != cols or set(line) - {"#", "."}`, for each row.
    for (int r = 0; r < world->rows; r++) {
        if (!read_line(in, line) || strlen(line) != (size_t)world->cols) return false;
        for (int c = 0; c < world->cols; c++) {
            if (line[c] != '#' && line[c] != '.') return false;
            world->live[r][c] = line[c] == '#';
        }
    }
    // Nothing may follow the grid: Python's `len(grid) != rows` for extra lines.
    return fgets(line, sizeof line, in) == nullptr;
}

// Python's `_render`. Each row is built in a local array and written whole.
static void print_world(const World *world, int generation) {
    printf("gen %d\n", generation);
    for (int r = 0; r < world->rows; r++) {
        char line[MAX_SIDE + 1];
        for (int c = 0; c < world->cols; c++) line[c] = world->live[r][c] ? '#' : '.';
        line[world->cols] = '\n';
        fwrite(line, 1, (size_t)world->cols + 1, stdout);
    }
}

int main(void) {
    // `static` storage: allocated once for the whole run and zero-filled, rather
    // than placed on the stack (Beej 16.2.2).
    static World world;
    int generations = 0;
    if (!read_world(stdin, &world, &generations)) {
        puts("error: expected a rows cols generations header and a grid of # and .");
        return 0;
    }
    for (int generation = 0; generation <= generations; generation++) {
        if (generation > 0) step(&world);
        print_world(&world, generation);
    }
    return 0;
}
