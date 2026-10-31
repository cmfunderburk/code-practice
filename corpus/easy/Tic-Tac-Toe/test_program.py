"""Tic-Tac-Toe shared tests: each version run as a whole program (SPEC §4).

The Python, C, and Rust versions all run these tests. They use only the
`run_program` fixture (`corpus/conftest.py`), which runs the program in each
language with the given stdin, checks that it exits with status 0, and returns its
stdout. The versions draw the board and word their messages differently, so only
the outcome line that SPEC §4 fixes is read. The expected outcome comes from
`_expected_outcome`, which replays the moves by the rules in SPEC §1; no code
under test is used to compute an expected answer. Each version's own tests check
its exact output.
"""

import random
import re

_WIN = re.compile(r"\b([XO]) wins\b", re.IGNORECASE)
_DRAW = re.compile(r"\bdraw\b", re.IGNORECASE)
_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8),
          (0, 4, 8), (2, 4, 6)]
_NOT_MOVES = ["", "9", "10", "x", "?", "4.5"]


def _moves(*lines: object) -> str:
    return "".join(f"{line}\n" for line in lines)


def _expected_outcome(moves: list[int]) -> str | None:
    """The outcome ("X", "O", or "draw") the moves reach, or None if undecided."""
    marks: dict[int, str] = {}
    for cell in moves:
        if cell in marks:
            continue
        marks[cell] = "XO"[len(marks) % 2]
        for line in _LINES:
            if all(marks.get(c) == marks[cell] for c in line):
                return marks[cell]
        if len(marks) == 9:
            return "draw"
    return None


def _outcome(out: str) -> str | None:
    """SPEC §4's outcome, read from the last line; None when no line names one."""
    lines = out.splitlines()
    named = [i for i, line in enumerate(lines) if _WIN.search(line) or _DRAW.search(line)]
    if not named:
        return None
    assert named == [len(lines) - 1], out[-500:]
    win = _WIN.search(lines[-1])
    return win.group(1).upper() if win else "draw"


def _plays(run_program, moves: list[int], *noise: object) -> None:
    """Play the moves, each followed by the noise lines, and check the outcome."""
    out = run_program(_moves(*(line for m in moves for line in (m, *noise))))
    assert _outcome(out) == _expected_outcome(moves), (moves, out[-500:])


def test_every_line_wins_for_x(run_program):
    # X takes the line while O marks two cells off it; two marks never win.
    for line in _LINES:
        o_cells = [c for c in range(9) if c not in line][:2]
        _plays(run_program, [line[0], o_cells[0], line[1], o_cells[1], line[2]])


def test_o_wins_on_the_anti_diagonal(run_program):
    _plays(run_program, [0, 2, 1, 4, 8, 6])


def test_a_full_board_with_no_line_is_a_draw(run_program):
    _plays(run_program, [0, 1, 2, 4, 3, 5, 7, 6, 8])


def test_a_win_on_the_ninth_move_is_a_win_not_a_draw(run_program):
    # The last X fills the board and the 0-4-8 diagonal at once.
    moves = [0, 1, 2, 3, 4, 5, 7, 6, 8]
    assert _expected_outcome(moves) == "X"
    _plays(run_program, moves)


def test_random_games_follow_the_rules(run_program):
    rng = random.Random(2026)
    for _ in range(20):
        cells = list(range(9))
        rng.shuffle(cells)
        _plays(run_program, cells)


def test_a_rejected_line_keeps_the_turn(run_program):
    # After each move, send lines that must be rejected: the first move's cell,
    # which is marked from then on, and lines that are not legal moves. If a
    # rejected line passed the turn, the marks would swap and the outcome would
    # change.
    _plays(run_program, [0, 3, 1, 4, 2], 0, *_NOT_MOVES)
    _plays(run_program, [4, 0, 8, 2, 1, 7, 6, 3, 5], 4, "x")


def test_a_line_that_is_not_a_legal_move_is_answered(run_program):
    quiet = len(run_program("").splitlines())
    for line in _NOT_MOVES:
        assert len(run_program(_moves(line)).splitlines()) > quiet, repr(line)
    marked = len(run_program(_moves(4)).splitlines())
    assert len(run_program(_moves(4, 4)).splitlines()) > marked


def test_the_program_stops_reading_after_the_end(run_program):
    out = run_program(_moves(0, 3, 1, 4, 2, 5, 8, "x", 6, 7))
    assert _outcome(out) == "X"


def test_end_of_input_stops_cleanly(run_program):
    for stdin in ["", "4\n", "4", "0\n3\n1\n4\n", "x\n"]:
        assert _outcome(run_program(stdin)) is None, repr(stdin)
