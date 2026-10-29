"""Expression Calculator smoke suite: each language, run whole on stdin (SPEC §4).

The tests use only the `run_program` fixture (`corpus/conftest.py`), which runs the
program, in each language, on the given stdin and returns its stdout (asserting exit
status 0). Each implementation prints numbers its own way, so a value line is read
as the one number it contains and compared within nine significant digits; an error
line is recognised by the word `error`. Random expressions are checked against
`_oracle`, which walks Python's own `ast` of the text (its precedence matches SPEC
§1's grammar) and skips any expression whose values grow past 10^12, where
fixed-width implementations may legitimately overflow.
"""

import ast
import math
import random
import re

import pytest

_NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ERROR = re.compile(r"\berror\b", re.IGNORECASE)
_LIMIT = 10 ** 12


class _OutOfRange(Exception):
    pass


def _value(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant):
        result = node.value
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        result = -_value(node.operand)
    elif isinstance(node, ast.BinOp):
        left, right = _value(node.left), _value(node.right)
        if isinstance(node.op, ast.Add):
            result = left + right
        elif isinstance(node.op, ast.Sub):
            result = left - right
        elif isinstance(node.op, ast.Mult):
            result = left * right
        else:
            if right == 0:
                raise ZeroDivisionError
            result = left / right
    else:
        raise AssertionError(f"unexpected node {ast.dump(node)}")
    if abs(result) > _LIMIT:
        raise _OutOfRange
    return result


def _oracle(text: str) -> float | None:
    """The expected value, math.nan for division by zero, None if out of range."""
    try:
        return _value(ast.parse(text, mode="eval").body)
    except ZeroDivisionError:
        return math.nan
    except _OutOfRange:
        return None


def _random_expr(rng: random.Random, depth: int) -> str:
    if depth == 0 or rng.random() < 0.3:
        return str(rng.randint(0, 99))
    kind = rng.randrange(6)
    if kind == 0:
        return "-" + _random_expr(rng, depth - 1)
    if kind == 1:
        return "(" + _random_expr(rng, depth - 1) + ")"
    op = "+-*/"[kind - 2]
    return _random_expr(rng, depth - 1) + op + _random_expr(rng, depth - 1)


def _answers(out: str, count: int) -> list[str]:
    lines = out.splitlines()
    assert len(lines) == count, out
    return lines


def _assert_value(line: str, expected: float) -> None:
    assert not _ERROR.search(line), line
    numbers = _NUMBER.findall(line)
    assert len(numbers) == 1, line
    assert math.isclose(float(numbers[0]), expected, rel_tol=1e-9, abs_tol=1e-12), (
        line, expected)


def _assert_error(line: str) -> None:
    assert _ERROR.search(line), line


def test_a_session_answers_each_line(run_program):
    lines = _answers(run_program("2+3*4\n(2+3)*4\n7/2\n2*-3\n1/0\n2)*3\n"), 6)
    for line, expected in zip(lines, [14, 20, 3.5, -6]):
        _assert_value(line, expected)
    _assert_error(lines[4])
    _assert_error(lines[5])


@pytest.mark.parametrize("line, expected", [
    ("20-5-3", 12),
    ("100/5/2", 10),
    ("2-3+4", 3),
    ("--3", 3),
    ("-(2+3)", -5),
    ("2--3", 5),
    ("007+1", 8),
    (" 2 +\t3 ", 5),
    ("1/3", 1 / 3),
    ("6/3", 2),
    ("7/2*2", 7),
    ("1/128", 1 / 128),
    ("1000000/3", 1000000 / 3),
    ("-1/3000000", -1 / 3000000),
    ("1/2-1/2", 0),
    ("123456789*1000", 123456789000),
], ids=lambda value: value if isinstance(value, str) else "")
def test_values_follow_the_grammar(run_program, line, expected):
    (answer,) = _answers(run_program(f"{line}\n"), 1)
    _assert_value(answer, expected)


@pytest.mark.parametrize("line", [
    "1/0", "0/0", "1/(1/2-1/2)", "5/(3-3)", "2+", "(2", "2)*3", "1 2", "2^3",
    "*3", "()", "2//3", "   ", "2 + x", "２+1",
], ids=[
    "int-zero", "zero-zero", "float-zero", "expr-zero", "dangling-op", "unclosed",
    "unopened", "adjacent", "caret", "leading-op", "empty-parens", "floor-div",
    "spaces-only", "letter", "fullwidth-digit",
])
def test_errors_are_answered_and_the_session_goes_on(run_program, line):
    error, after = _answers(run_program(f"{line}\n1+1\n"), 2)
    _assert_error(error)
    _assert_value(after, 2)


def test_an_empty_line_ends_the_session(run_program):
    (answer,) = _answers(run_program("1+1\n\n2+2\n"), 1)
    _assert_value(answer, 2)
    assert run_program("\n1+1\n") == ""


def test_end_of_input_ends_the_session(run_program):
    assert run_program("") == ""
    first, last = _answers(run_program("1+1\n2*3"), 2)
    _assert_value(first, 2)
    _assert_value(last, 6)


def test_random_expressions_match_the_semantics(run_program):
    rng = random.Random(2026)
    lines, expected = [], []
    while len(lines) < 200:
        text = _random_expr(rng, 4)
        want = _oracle(text)
        if want is not None:
            lines.append(text)
            expected.append(want)
    answers = _answers(run_program("".join(f"{line}\n" for line in lines)), 200)
    for text, answer, want in zip(lines, answers, expected):
        if math.isnan(want):
            _assert_error(answer)
        else:
            _assert_value(answer, want)
