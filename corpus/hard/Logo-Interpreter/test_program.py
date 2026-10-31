"""Logo Interpreter shared tests: each version run as a whole program (SPEC §4).

The Python, C, and Rust versions all run these tests. They use only the
`run_program` fixture (`corpus/conftest.py`), which runs the program in each
language with the given stdin, checks that it exits with status 0, and returns its
stdout. Each version may word its state line and its error messages its own way,
so the output is read as a list of answers: an error line (one containing
`error`), or a report, whose state line is read only for its first two integers,
x and y, and whose segment lines are compared exactly.

The expected answers come from `_expected`, a separate small interpreter written
from SPEC §1–§2, with its own tokenizer, parser, turtle, and history of saved
states; no code under test is used to compute an expected answer. Every input
keeps to what SPEC fixes for every version: ASCII words separated by spaces or
tabs, and numbers as plain digits, apart from spellings that no version accepts as
a count, such as `0`, `-2`, or `3.0`.
"""

import random
import re

import pytest

_ERROR = re.compile(r"\berror\b", re.IGNORECASE)
_SEGMENT = re.compile(r"(-?\d+),(-?\d+) -> (-?\d+),(-?\d+)")
_INTEGER = re.compile(r"-?\d+")
_STEPS = {"E": (1, 0), "N": (0, 1), "W": (-1, 0), "S": (0, -1)}
_LEFT = {"E": "N", "N": "W", "W": "S", "S": "E"}
_RIGHT = {after: before for before, after in _LEFT.items()}
_START = (0, 0, "E", True, ())


class _Bad(Exception):
    pass


def _tokens(line: str) -> list[str]:
    return line.replace("[", " [ ").replace("]", " ] ").upper().split()


def _number(tokens: list[str], pos: int) -> int:
    if pos >= len(tokens) or not re.fullmatch(r"[0-9]+", tokens[pos]):
        raise _Bad
    value = int(tokens[pos])
    if value < 1:
        raise _Bad
    return value


def _block(tokens: list[str], pos: int, nested: bool) -> tuple[list, int]:
    """Parse commands from `pos`: a list of (op, arg) and the next position."""
    commands: list = []
    while pos < len(tokens):
        op = tokens[pos]
        if op == "]":
            if not nested:
                raise _Bad
            return commands, pos + 1
        if op == "FORWARD":
            commands.append((op, _number(tokens, pos + 1)))
            pos += 2
        elif op in ("LEFT", "RIGHT", "PENUP", "PENDOWN"):
            commands.append((op, None))
            pos += 1
        elif op == "REPEAT":
            count = _number(tokens, pos + 1)
            if pos + 2 >= len(tokens) or tokens[pos + 2] != "[":
                raise _Bad
            body, pos = _block(tokens, pos + 3, True)
            commands.append((op, (count, body)))
        else:
            raise _Bad
    if nested:
        raise _Bad
    return commands, pos


def _run(commands: list, state: tuple) -> tuple:
    x, y, heading, pen, segments = state
    for op, arg in commands:
        if op == "FORWARD":
            dx, dy = _STEPS[heading]
            end = (x + dx * arg, y + dy * arg)
            if pen:
                segments += ((x, y) + end,)
            x, y = end
        elif op == "LEFT":
            heading = _LEFT[heading]
        elif op == "RIGHT":
            heading = _RIGHT[heading]
        elif op in ("PENUP", "PENDOWN"):
            pen = op == "PENDOWN"
        else:
            count, body = arg
            for _ in range(count):
                x, y, heading, pen, segments = _run(body, (x, y, heading, pen, segments))
    return x, y, heading, pen, segments


def _expected(lines: list[str]) -> list:
    """The expected answers: "error", or (x, y, segments) for a report."""
    state, history, out = _START, [], []
    for line in lines:
        tokens = _tokens(line)
        if tokens == ["UNDO"]:
            if not history:
                out.append("error")
                continue
            state = history.pop()
        else:
            try:
                commands, _ = _block(tokens, 0, False)
            except _Bad:
                out.append("error")
                continue
            for command in commands:
                history.append(state)
                state = _run([command], state)
        x, y, _, _, segments = state
        out.append((x, y, list(segments)))
    return out


def _answers(out: str) -> list:
    """The program's answers, read as SPEC §4 describes them."""
    answers: list = []
    for line in out.splitlines():
        if _ERROR.search(line):
            answers.append("error")
        elif segment := _SEGMENT.fullmatch(line):
            assert answers and answers[-1] != "error", f"stray segment line: {out}"
            answers[-1][2].append(tuple(int(n) for n in segment.groups()))
        else:
            numbers = _INTEGER.findall(line)
            assert len(numbers) >= 2, f"state line without x and y: {line!r}"
            answers.append((int(numbers[0]), int(numbers[1]), []))
    return answers


def _stdin(lines: list[str]) -> str:
    return "".join(f"{line}\n" for line in lines)


def _check(run_program, lines: list[str]) -> None:
    assert _answers(run_program(_stdin(lines))) == _expected(lines), lines


_EXAMPLE_IN = [
    "FORWARD 2 LEFT",
    "penup REPEAT 2 [ FORWARD 1 RIGHT ]",
    "FORWARD 0",
    "UNDO",
    "undo",
    "",
    "UNDO",
    "UNDO",
    "UNDO",
]
_FIRST = [(0, 0, 2, 0)]
_EXAMPLE_ANSWERS = [
    (2, 0, _FIRST), (3, 1, _FIRST), "error", (2, 0, _FIRST), (2, 0, _FIRST),
    (2, 0, _FIRST), (2, 0, _FIRST), (0, 0, []), "error",
]


def test_spec_example(run_program):
    assert _expected(_EXAMPLE_IN) == _EXAMPLE_ANSWERS
    assert _answers(run_program(_stdin(_EXAMPLE_IN))) == _EXAMPLE_ANSWERS


def test_a_square_is_one_history_entry(run_program):
    square = [(0, 0, 2, 0), (2, 0, 2, 2), (2, 2, 0, 2), (0, 2, 0, 0)]
    assert _answers(run_program("REPEAT 4 [ FORWARD 2 LEFT ]\nUNDO\nUNDO\n")) == [
        (0, 0, square), (0, 0, []), "error",
    ]


def test_each_top_level_command_is_one_entry(run_program):
    assert _answers(run_program("FORWARD 2 RIGHT FORWARD 3\nUNDO\nUNDO\nUNDO\n")) == [
        (2, -3, [(0, 0, 2, 0), (2, 0, 2, -3)]),
        (2, 0, [(0, 0, 2, 0)]),
        (2, 0, [(0, 0, 2, 0)]),
        (0, 0, []),
    ]


def test_turns_cycle_through_every_heading(run_program):
    # Each FORWARD 1 shows the heading the turns before it left.
    _check(run_program, ["LEFT FORWARD 1", "LEFT FORWARD 1", "LEFT FORWARD 1",
                         "LEFT FORWARD 1", "RIGHT FORWARD 1", "UNDO", "UNDO",
                         "FORWARD 1"])


def test_moving_with_the_pen_up_draws_nothing(run_program):
    _check(run_program, ["PENUP FORWARD 3 LEFT FORWARD 2 PENDOWN RIGHT FORWARD 1",
                         "UNDO", "FORWARD 1", "PENDOWN", "PENUP", "PENUP",
                         "UNDO", "FORWARD 2"])


def test_negative_coordinates_print_with_a_minus(run_program):
    assert _answers(run_program("LEFT LEFT FORWARD 4 LEFT FORWARD 10000\n")) == [
        (-4, -10000, [(0, 0, -4, 0), (-4, 0, -4, -10000)]),
    ]


def test_case_and_bracket_spacing_do_not_matter(run_program):
    _check(run_program, ["repeat 2[forward 1 left repeat 2[forward 1 right]]",
                         "Repeat 3 [Forward 2 Left]", "UnDo", "\tFORWARD\t2\t"])


def test_nested_and_empty_blocks(run_program):
    _check(run_program, ["REPEAT 3 [ REPEAT 2 [ FORWARD 1 ] LEFT ]",
                         "REPEAT 5 [ ]", "REPEAT 2 [ REPEAT 3 [ ] ]",
                         "UNDO", "UNDO", "UNDO", "UNDO"])


def test_deep_nesting(run_program):
    deep = "REPEAT 1 [ " * 100 + "FORWARD 1" + " ]" * 100
    _check(run_program, [deep, "UNDO", "UNDO"])


def test_empty_lines_run_no_commands(run_program):
    _check(run_program, ["", "   ", "FORWARD 1", "", "UNDO", "UNDO", ""])


@pytest.mark.parametrize("line", ["  undo", "UNDO  ", "uNdO", "\tUndo"])
def test_undo_ignores_case_and_spaces(run_program, line):
    _check(run_program, ["FORWARD 2 LEFT", line, line])


@pytest.mark.parametrize("line", [
    "UNDO UNDO", "FORWARD 1 UNDO", "UNDO FORWARD 1", "UNDO[", "[UNDO]", "UNDOS",
])
def test_undo_is_not_part_of_the_language(run_program, line):
    _check(run_program, ["FORWARD 2", line, "UNDO", "UNDO"])


@pytest.mark.parametrize("token", [
    "0", "-2", "-0", "00", "-", "++3", "3.0", "1e3", "0x10", "three", "x2", "[", "]",
])
def test_bad_numbers_are_errors(run_program, token):
    _check(run_program, ["FORWARD 1", f"FORWARD {token}", f"REPEAT {token} [ LEFT ]",
                         "UNDO", "UNDO"])


@pytest.mark.parametrize("line", [
    "FORWARD", "SPIN", "]", "[", "[ LEFT ]", "LEFT ] RIGHT", "REPEAT", "REPEAT 2",
    "REPEAT 2 FORWARD 1", "REPEAT [ LEFT ]", "REPEAT 0 [ LEFT ]", "REPEAT 2 [ LEFT",
    "REPEAT 2 [ LEFT ] ]", "REPEAT 2 [ REPEAT 2 [ LEFT ]", "FORWARD 1 LEFT SPIN",
    "LEFT FORWARD", "FORWARDS 2", "PEN UP", "REPEAT 2 [ FORWARD 0 ]",
])
def test_a_bad_line_runs_nothing(run_program, line):
    _check(run_program, ["FORWARD 2 LEFT", line, "UNDO", "UNDO", "UNDO"])


def test_input_without_a_final_newline(run_program):
    assert _answers(run_program("FORWARD 1\nLEFT")) == [
        (1, 0, [(0, 0, 1, 0)]), (1, 0, [(0, 0, 1, 0)]),
    ]


def test_empty_input_prints_nothing(run_program):
    assert run_program("") == ""


def test_many_commands_on_one_line(run_program):
    _check(run_program, ["REPEAT 100 [ REPEAT 100 [ LEFT ] FORWARD 1 ]", "UNDO"])


def _random_command(rng: random.Random, depth: int) -> str:
    kind = rng.choice(["FORWARD", "LEFT", "RIGHT", "PENUP", "PENDOWN"]
                      + (["REPEAT"] if depth else []))
    if kind == "FORWARD":
        return f"{rng.choice(['forward', 'FORWARD', 'Forward'])} {rng.randint(1, 9)}"
    if kind == "REPEAT":
        body = " ".join(_random_command(rng, depth - 1)
                        for _ in range(rng.randint(0, 3)))
        return f"REPEAT {rng.randint(1, 3)} [{rng.choice(['', ' '])}{body} ]"
    return rng.choice([kind, kind.lower()])


def _random_line(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.25:
        return rng.choice(["UNDO", "undo", " UNDO\t"])
    if roll < 0.35:
        return rng.choice(["", "SPIN", "FORWARD 0", "REPEAT 2 [ LEFT", "]",
                           "FORWARD x", "LEFT UNDO", "\tLEFT"])
    return " ".join(_random_command(rng, 2) for _ in range(rng.randint(1, 4)))


def test_random_sessions_match_the_rules(run_program):
    rng = random.Random(2026)
    for _ in range(40):
        _check(run_program, [_random_line(rng) for _ in range(rng.randint(0, 12))])
