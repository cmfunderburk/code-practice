import io
import random
import sys

import pytest


def _random_expr(rng: random.Random, depth: int) -> str:
    """Random well-formed expression text, to compare calculate with Python's eval."""
    if depth == 0 or rng.random() < 0.3:
        return str(rng.randint(0, 99))
    kind = rng.randrange(6)
    if kind == 0:
        return "-" + _random_expr(rng, depth - 1)
    if kind == 1:
        return "(" + _random_expr(rng, depth - 1) + ")"
    op = "+-*/"[kind - 2]
    return _random_expr(rng, depth - 1) + op + _random_expr(rng, depth - 1)


def test_precedence_and_parens(sub):
    assert sub.calculate("2+3*4") == 14
    assert sub.calculate("(2+3)*4") == 20
    assert sub.calculate("2*(3+4)") == 14
    assert sub.calculate("10-2*3") == 4


def test_left_associativity(sub):
    assert sub.calculate("20-5-3") == 12
    assert sub.calculate("100/5/2") == 10.0
    assert sub.calculate("2-3+4") == 3


def test_unary_minus(sub):
    assert sub.calculate("-3+5") == 2
    assert sub.calculate("--3") == 3
    assert sub.calculate("2*-3") == -6
    assert sub.calculate("-(2+3)") == -5
    assert sub.calculate("2--3") == 5


def test_division_is_true_division(sub):
    result = sub.calculate("7/2")
    assert result == 3.5 and isinstance(result, float)
    assert sub.calculate("8/2") == 4.0


def test_integer_results_stay_int(sub):
    result = sub.calculate("2+3")
    assert result == 5 and isinstance(result, int)


def test_whitespace_tolerant(sub):
    assert sub.calculate("  2 +  3*4 ") == 14
    assert sub.calculate("2 * ( 1 + 1 )") == 4
    assert sub.calculate("\t2\t+3") == 5


def test_only_ascii_spaces_digits_and_tabs(sub):
    for bad in ("2\v+1", "2\r", "\u00a02", "\uff12+1", "\u0663"):
        with pytest.raises(ValueError):
            sub.calculate(bad)


def test_malformed_raises(sub):
    for bad in ("", "   ", "2+", "(2", "2)*3", "1 2", "2^3", "*3", "()", "2//3"):
        with pytest.raises(ValueError):
            sub.calculate(bad)


def test_zero_division_propagates(sub):
    with pytest.raises(ZeroDivisionError):
        sub.calculate("1/0")


def test_random_expressions_match_python_eval(sub):
    # Python's eval uses the same grammar, precedence, and operators, so calculate
    # must return exactly what eval returns, int or float included.
    rng = random.Random(2026)
    checked = 0
    while checked < 200:
        text = _random_expr(rng, 4)
        try:
            expected = eval(text)
        except ZeroDivisionError:
            with pytest.raises(ZeroDivisionError):
                sub.calculate(text)
            continue
        got = sub.calculate(text)
        assert got == expected and type(got) is type(expected), text
        checked += 1


def test_tokenize(sub):
    assert sub.tokenize("12 + 3") == ["12", "+", "3"]
    assert sub.tokenize(" (1+20)*-3 ") == ["(", "1", "+", "20", ")", "*", "-", "3"]


def test_parse_builds_the_tuple_ast(sub):
    assert sub.parse(sub.tokenize("2+3*4")) == \
        ("+", ("num", 2), ("*", ("num", 3), ("num", 4)))
    assert sub.parse(sub.tokenize("-(1+2)/3")) == \
        ("/", ("neg", ("+", ("num", 1), ("num", 2))), ("num", 3))


def test_evaluate_hand_built_nodes(sub):
    node = ("*", ("num", 6), ("neg", ("num", 7)))
    assert sub.evaluate(node) == -42
    assert sub.evaluate(node) == -42  # evaluate keeps no state: the same tree gives the same answer


def _feed(monkeypatch, text: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


def test_main_prints_each_value_as_python_does(sub, monkeypatch, capsys):
    _feed(monkeypatch, "2+3*4\n7/2\n8/2\n1/0\n2^3\n\n9\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        "14",
        "3.5",
        "4.0",
        "error: division by zero",
        "error: unknown character: ^",
    ]


def test_main_hands_each_line_to_calculate(sub, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(sub, "calculate", lambda text: seen.append(text) or 1)
    _feed(monkeypatch, " 1 + 2\n3")
    sub.main()
    assert seen == [" 1 + 2", "3"]
    assert capsys.readouterr().out == "1\n1\n"
