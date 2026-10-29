"""Roman Numerals smoke suite: each language, run whole on stdin (SPEC §4).

The tests use only the `run_program` fixture (`corpus/conftest.py`), which runs the
program, in each language, on the given stdin and returns its stdout (asserting exit
status 0). Each implementation words its refusals its own way, so an answer is read
only for the facts SPEC §4 fixes: a numeral answer holds the numeral as its one word
of numeral letters, a value answer holds the value as its one number, and a refusal
holds the word `error`. Expected numerals come from `_numeral`, which renders SPEC
§1's place-value table, and canonicality is membership in the 3999 numerals it
builds, never an implementation under test. Lines stay plain (SPEC §4): no leading
zeros, lowercase, signs, or surrounding spaces, whose reading is each
implementation's choice.
"""

import random
import re

import pytest

_PLACES = (
    ("", "M", "MM", "MMM"),
    ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"),
    ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"),
    ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"),
)


def _numeral(n: int) -> str:
    digits = f"{n:04d}"
    return "".join(place[int(d)] for place, d in zip(_PLACES, digits))


_VALUE_OF = {_numeral(n): n for n in range(1, 4000)}
_ERROR = re.compile(r"\berror\b", re.IGNORECASE)
_LETTERS = re.compile(r"\b[IVXLCDM]+\b")
_NUMBER = re.compile(r"\d+")


def _answers(run_program, lines: list[str]) -> list[str]:
    out = run_program("".join(f"{line}\n" for line in lines)).splitlines()
    assert len(out) == len(lines), (lines, out)
    return out


def _is_numeral(answer: str, numeral: str) -> None:
    assert not _ERROR.search(answer), answer
    assert _LETTERS.findall(answer) == [numeral], (answer, numeral)


def _is_value(answer: str, value: int) -> None:
    assert not _ERROR.search(answer), answer
    assert _NUMBER.findall(answer) == [str(value)], (answer, value)


def _is_refusal(answer: str) -> None:
    assert _ERROR.search(answer), answer


def _check(line: str, answer: str) -> None:
    """SPEC §2's answer kind for one plain line."""
    if line.isdigit() and 1 <= int(line) <= 3999:
        _is_numeral(answer, _numeral(int(line)))
    elif line in _VALUE_OF:
        _is_value(answer, _VALUE_OF[line])
    else:
        _is_refusal(answer)


def test_a_session_answers_each_line(run_program):
    lines = ["1990", "MCMXC", "IIII", "4000", "hello"]
    out = _answers(run_program, lines)
    _is_numeral(out[0], "MCMXC")
    _is_value(out[1], 1990)
    for answer in out[2:]:
        _is_refusal(answer)


def test_every_number_renders(run_program):
    lines = [str(n) for n in range(1, 4000)]
    for n, answer in enumerate(_answers(run_program, lines), start=1):
        _is_numeral(answer, _numeral(n))


def test_every_canonical_numeral_parses(run_program):
    lines = [_numeral(n) for n in range(1, 4000)]
    for n, answer in enumerate(_answers(run_program, lines), start=1):
        _is_value(answer, n)


@pytest.mark.parametrize("line", [
    "0", "4000", "9999", "12345", "99999999999999999999",
])
def test_numbers_out_of_range_are_refused(run_program, line):
    (answer,) = _answers(run_program, [line])
    _is_refusal(answer)


@pytest.mark.parametrize("line", [
    "IIII", "VV", "IC", "IL", "VX", "XM", "IM", "LC", "DM", "MMMM", "IIX",
    "XIIII", "CCCC", "MCMC", "IXIX", "MMMDCCCLXXXVIIV", "CDM", "IVI",
    "MMMMMMMMMMMMMMM", "M" * 40,
])
def test_non_canonical_numerals_are_refused(run_program, line):
    assert line not in _VALUE_OF
    (answer,) = _answers(run_program, [line])
    _is_refusal(answer)


@pytest.mark.parametrize("line", [
    "hello", "12X", "X12", "1 2", "XL II", "4.5", "?", "ABC", "MCMXCZ",
])
def test_lines_that_are_neither_are_refused(run_program, line):
    (answer,) = _answers(run_program, [line])
    _is_refusal(answer)


def test_a_refusal_costs_nothing(run_program):
    lines = ["IIII", "14", "nope", "XIV", "0", "3999"]
    for line, answer in zip(lines, _answers(run_program, lines)):
        _check(line, answer)


def test_end_of_input(run_program):
    assert run_program("") == ""
    (answer,) = run_program("XLII").splitlines()
    _is_value(answer, 42)
    first, last = run_program("42\nXLII").splitlines()
    _is_numeral(first, "XLII")
    _is_value(last, 42)


def test_random_sessions(run_program):
    rng = random.Random(2026)
    junk = ["hello", "12X", "X12", "1 2", "?"]
    for _ in range(12):
        lines = []
        for _ in range(rng.randint(1, 30)):
            kind = rng.randrange(5)
            if kind == 0:
                lines.append(str(rng.randint(0, 9999)))
            elif kind == 1:
                lines.append(_numeral(rng.randint(1, 3999)))
            elif kind == 2:
                lines.append("".join(rng.choice("IVXLCDM")
                                     for _ in range(rng.randint(1, 15))))
            elif kind == 3:
                lines.append(_numeral(rng.randint(1, 3999)) + rng.choice("IVXLCDM"))
            else:
                lines.append(rng.choice(junk))
        for line, answer in zip(lines, _answers(run_program, lines)):
            _check(line, answer)
