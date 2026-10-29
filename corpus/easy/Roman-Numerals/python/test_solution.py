import io
import sys

import pytest


GOLDEN = [
    (1, "I"), (2, "II"), (3, "III"), (4, "IV"), (5, "V"), (6, "VI"),
    (7, "VII"), (8, "VIII"), (9, "IX"), (10, "X"), (11, "XI"), (12, "XII"),
    (40, "XL"), (90, "XC"), (400, "CD"), (900, "CM"),
    (1990, "MCMXC"), (2026, "MMXXVI"), (3999, "MMMCMXCIX"),
]

# independent positional formulation: a different algorithm than either
# drilled direction (table walk / lookahead scan)
ONES = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
TENS = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
HUNDREDS = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
THOUSANDS = ("", "M", "MM", "MMM")


def _ref_roman(n: int) -> str:
    return (THOUSANDS[n // 1000] + HUNDREDS[n // 100 % 10]
            + TENS[n // 10 % 10] + ONES[n % 10])


def test_golden_pairs_both_ways(sub):
    for n, numeral in GOLDEN:
        assert sub.to_roman(n) == numeral
        assert sub.from_roman(numeral) == n


def test_full_space_render_against_positional_oracle(sub):
    for n in range(1, 4000):
        assert sub.to_roman(n) == _ref_roman(n), n


def test_full_space_parse_against_positional_oracle(sub):
    for n in range(1, 4000):
        assert sub.from_roman(_ref_roman(n)) == n, n


def test_round_trip(sub):
    for n in range(1, 4000):
        assert sub.from_roman(sub.to_roman(n)) == n, n


def test_render_domain_errors(sub):
    for bad in (0, 4000, -1):
        with pytest.raises(ValueError):
            sub.to_roman(bad)


def _feed(monkeypatch, text: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


def test_main_answers_in_the_python_wording(sub, monkeypatch, capsys):
    _feed(monkeypatch, "1990\nMCMXC\nIIII\n4000\nhello\n\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        "MCMXC",
        "1990",
        "error: not a canonical numeral: IIII",
        "error: out of range: 4000",
        "error: enter a number 1-3999 or a Roman numeral",
        "error: enter a number 1-3999 or a Roman numeral",
    ]


def test_main_trims_and_folds_case(sub, monkeypatch, capsys):
    _feed(monkeypatch, "  0042 \nmcmxc\n xiv\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == ["XLII", "1990", "14"]


def test_main_refuses_digits_that_are_not_ascii(sub, monkeypatch, capsys):
    _feed(monkeypatch, "\u0664\u0662\n+12\n")
    sub.main()
    for line in capsys.readouterr().out.splitlines():
        assert line.startswith("error: "), line


def test_main_checks_a_numeral_by_the_round_trip(sub, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(sub, "to_roman", lambda n: seen.append(n) or "X")
    _feed(monkeypatch, "IIIIIIIIII\n")
    sub.main()
    assert seen == [10]
    assert capsys.readouterr().out.splitlines() == [
        "error: not a canonical numeral: IIIIIIIIII"]
