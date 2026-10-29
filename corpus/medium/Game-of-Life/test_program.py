"""Game of Life smoke suite: each language, run whole on stdin (SPEC §5).

The tests use only the `run_program` fixture (`corpus/conftest.py`), which runs the
program, in each language, on the given stdin and returns its stdout (asserting exit
status 0). Each implementation labels a frame its own way, so a label line is read
only for its first number, the generation; grid lines are compared exactly. Expected
grids come from a definition-level recount of every cell, never from an
implementation under test.
"""

import random
import re

import pytest

_BLINKER = """\
5 5 2
.....
.....
.###.
.....
.....
"""

_BLINKER_FRAMES = [
    [".....", ".....", ".###.", ".....", "....."],
    [".....", "..#..", "..#..", "..#..", "....."],
    [".....", ".....", ".###.", ".....", "....."],
]


def _oracle_step(grid: list[str]) -> list[str]:
    rows, cols = len(grid), len(grid[0])

    def alive(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols and grid[r][c] == "#"

    out = []
    for r in range(rows):
        line = []
        for c in range(cols):
            n = sum(alive(r + dr, c + dc)
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
            line.append("#" if n == 3 or (n == 2 and alive(r, c)) else ".")
        out.append("".join(line))
    return out


def _pattern(grid: list[str], generations: int) -> str:
    return f"{len(grid)} {len(grid[0])} {generations}\n" + "".join(
        f"{line}\n" for line in grid)


def _expected(grid: list[str], generations: int) -> list[list[str]]:
    frames = []
    for _ in range(generations + 1):
        frames.append(grid)
        grid = _oracle_step(grid)
    return frames


def _frames(out: str, rows: int, count: int) -> list[list[str]]:
    lines = out.splitlines()
    assert len(lines) == count * (rows + 1), out
    frames = []
    for gen in range(count):
        label, *grid = lines[gen * (rows + 1):(gen + 1) * (rows + 1)]
        assert re.findall(r"\d+", label)[:1] == [str(gen)], label
        frames.append(grid)
    return frames


def _simulates(run_program, grid: list[str], generations: int) -> None:
    out = run_program(_pattern(grid, generations))
    assert _frames(out, len(grid), generations + 1) == _expected(grid, generations)


def _assert_error(out: str) -> None:
    lines = out.splitlines()
    assert len(lines) == 1, out
    assert re.search(r"\berror\b", lines[0], re.IGNORECASE), out


def test_spec_example_blinker(run_program):
    assert _frames(run_program(_BLINKER), 5, 3) == _BLINKER_FRAMES


def test_glider_crosses_a_bounded_board(run_program):
    _simulates(run_program, ["..#.....", "...#....", ".###....", "........",
                             "........", "........", "........", "........"], 12)


def test_cells_beyond_the_edge_are_dead(run_program):
    # A blinker jammed against the top edge loses its off-grid birth.
    assert _expected(["###", "...", "..."], 1)[1] == [".#.", ".#.", "..."]
    _simulates(run_program, ["###", "...", "..."], 1)


def test_corner_cell_dies_on_a_one_by_one_board(run_program):
    assert _frames(run_program("1 1 1\n#\n"), 1, 2) == [["#"], ["."]]


def test_zero_generations_writes_one_frame(run_program):
    assert _frames(run_program("2 3 0\n#.#\n.#.\n"), 2, 1) == [["#.#", ".#."]]


def test_final_newline_is_optional(run_program):
    assert _frames(run_program(_BLINKER.rstrip("\n")), 5, 3) == _BLINKER_FRAMES


def test_still_life_over_the_generation_limit(run_program):
    _simulates(run_program, ["....", ".##.", ".##.", "...."], 1000)


def test_largest_board(run_program):
    rng = random.Random(100)
    _simulates(run_program,
               ["".join(rng.choice("#..") for _ in range(100)) for _ in range(100)], 3)


def test_random_boards_match_the_definition(run_program):
    rng = random.Random(2026)
    for _ in range(8):
        rows, cols = rng.randint(1, 12), rng.randint(1, 12)
        grid = ["".join(rng.choice("#..") for _ in range(cols)) for _ in range(rows)]
        _simulates(run_program, grid, rng.randint(0, 6))


@pytest.mark.parametrize("stdin", [
    "",
    "\n",
    "3 3\n...\n...\n...\n",
    "3 3 1 1\n...\n...\n...\n",
    "3 x 1\n...\n...\n...\n",
    "3 3 -1\n...\n...\n...\n",
    "0 3 1\n",
    "3 0 1\n\n\n\n",
    "101 1 0\n" + ".\n" * 101,
    "1 101 0\n" + "." * 101 + "\n",
    "1 1 1001\n.\n",
    "3 3 1\n...\n..\n...\n",
    "3 3 1\n...\n....\n...\n",
    "3 3 1\n...\n.x.\n...\n",
    "3 3 1\n...\n.O.\n...\n",
    "3 3 1\n...\n...\n",
    "3 3 1\n...\n...\n...\n...\n",
    "3 3 1\n...\n...\n...\n\n",
], ids=[
    "empty", "blank-line", "two-fields", "four-fields", "not-a-number",
    "negative", "zero-rows", "zero-cols", "rows-over-100", "cols-over-100",
    "generations-over-1000", "short-line", "long-line", "bad-character",
    "letter-o", "too-few-lines", "extra-line", "extra-blank-line",
])
def test_malformed_input_is_one_error_line(run_program, stdin):
    _assert_error(run_program(stdin))
