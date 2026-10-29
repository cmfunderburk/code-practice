// Game of Life: whole program.

#include <stdio.h>
#include <string.h>

constexpr int MAX_SIDE = 100;
constexpr int MAX_GENERATIONS = 1000;

typedef struct {
    int rows, cols;
    bool live[MAX_SIDE][MAX_SIDE];
} World;

static void step(World *world) {
    unsigned char counts[MAX_SIDE + 2][MAX_SIDE + 2] = {};
    for (int r = 0; r < world->rows; r++)
        for (int c = 0; c < world->cols; c++)
            if (world->live[r][c])
                for (int dr = 0; dr < 3; dr++)
                    for (int dc = 0; dc < 3; dc++)
                        if (dr != 1 || dc != 1) counts[r + dr][c + dc]++;
    for (int r = 0; r < world->rows; r++) {
        for (int c = 0; c < world->cols; c++) {
            int n = counts[r + 1][c + 1];
            world->live[r][c] = n == 3 || (n == 2 && world->live[r][c]);
        }
    }
}

static bool read_line(FILE *in, char line[static MAX_SIDE + 2]) {
    if (fgets(line, MAX_SIDE + 2, in) == nullptr) return false;
    size_t len = strcspn(line, "\n");
    if (line[len] != '\n' && len > MAX_SIDE) return false;
    line[len] = '\0';
    return true;
}

static bool read_world(FILE *in, World *world, int *generations) {
    char line[MAX_SIDE + 2];
    char extra;
    if (!read_line(in, line) ||
        sscanf(line, "%d %d %d %c", &world->rows, &world->cols, generations, &extra) != 3)
        return false;
    if (world->rows < 1 || world->rows > MAX_SIDE || world->cols < 1 || world->cols > MAX_SIDE ||
        *generations < 0 || *generations > MAX_GENERATIONS)
        return false;
    for (int r = 0; r < world->rows; r++) {
        if (!read_line(in, line) || strlen(line) != (size_t)world->cols) return false;
        for (int c = 0; c < world->cols; c++) {
            if (line[c] != '#' && line[c] != '.') return false;
            world->live[r][c] = line[c] == '#';
        }
    }
    return fgets(line, sizeof line, in) == nullptr;
}

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
