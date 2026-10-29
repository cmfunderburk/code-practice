"""Editor Buffer smoke suite: each language, run whole on stdin (SPEC §5).

The tests use only the `run_program` fixture (`corpus/conftest.py`), which runs the
program, in each language, on the given stdin and returns its stdout (asserting exit
status 0). The buffer's text is the program's data, so a `p` answer is checked
exactly; each implementation words its refusals its own way, so a refusal is checked
only as one line. Expected answers come from `_oracle`, a plain simulation of SPEC
§1–§3 that parses lines with regular expressions and keeps whole-text snapshots as
its history, never from an implementation under test. Lines stay plain (SPEC §5): no
signs, leading zeros, or whitespace but the space.
"""

import random
import re

import pytest

_REFUSED = None  # an answer line whose wording is the implementation's

_INSERT = re.compile(r"i ([0-9]+) (.*)", re.DOTALL)
_DELETE = re.compile(r"d ([0-9]+) ([0-9]+)")


def _oracle(lines: list[str]) -> list[str | None]:
    """Each answer line of a whole session (SPEC §1–§3): a `p` line, or _REFUSED."""
    text = ""
    undo: list[str] = []  # snapshots before each edit still in effect
    redo: list[str] = []  # snapshots of undone states, most recent last
    out: list[str | None] = []
    for line in lines:
        insert = _INSERT.fullmatch(line)
        delete = _DELETE.fullmatch(line)
        if line == "q":
            break
        if insert:
            pos, new = int(insert[1]), insert[2]
            if pos > len(text):
                out.append(_REFUSED)
            else:
                undo.append(text)
                redo.clear()
                text = text[:pos] + new + text[pos:]
        elif delete:
            pos, n = int(delete[1]), int(delete[2])
            if n < 1 or pos + n > len(text):
                out.append(_REFUSED)
            else:
                undo.append(text)
                redo.clear()
                text = text[:pos] + text[pos + n:]
        elif line == "u":
            if undo:
                redo.append(text)
                text = undo.pop()
            else:
                out.append(_REFUSED)
        elif line == "r":
            if redo:
                undo.append(text)
                text = redo.pop()
            else:
                out.append(_REFUSED)
        elif line == "p":
            out.append(f'"{text}"')
        else:
            out.append(_REFUSED)
    return out


def _matches(out: str, expected: list[str | None]) -> None:
    lines = out.split("\n")
    assert lines[-1] == "", out
    lines = lines[:-1]
    assert len(lines) == len(expected), (out, expected)
    for line, want in zip(lines, expected):
        if want is not _REFUSED:
            assert line == want, (line, want)


def _run(run_program, lines: list[str], *expected: str | None) -> None:
    assert _oracle(lines) == list(expected), lines
    _matches(run_program(_stdin(lines)), list(expected))


def _stdin(lines: list[str]) -> str:
    return "".join(f"{line}\n" for line in lines)


def test_spec_session(run_program):
    _run(run_program, ["i 0 hello", "i 5  world", "d 0 6", "p", "u", "u", "p", "r", "p",
                       "i 11 !", "r", "x", "p"],
         '"world"', '"hello"', '"hello world"', _REFUSED, _REFUSED, '"hello world!"')


def test_nothing_is_written_at_start_or_for_a_silent_session(run_program):
    assert run_program("") == ""
    assert run_program("i 0 abc\nd 1 1\nu\nr\n") == ""


def test_text_starts_after_the_second_space(run_program):
    _run(run_program, ["i 0 a b  c ", "p", "i 0  ", "p", "i 0 ", "p"],
         '"a b  c "', '" a b  c "', '" a b  c "')


def test_quotes_in_the_text_are_not_escaped(run_program):
    _run(run_program, ['i 0 say "hi"', "p"], '"say "hi""')


def test_insert_at_the_end_is_legal_and_beyond_it_is_not(run_program):
    _run(run_program, ["i 0 abc", "i 3 d", "i 5 x", "p"], _REFUSED, '"abcd"')


def test_delete_bounds(run_program):
    _run(run_program, ["i 0 abc", "d 0 0", "d 2 2", "d 3 1", "d 0 3", "p", "u", "p"],
         _REFUSED, _REFUSED, _REFUSED, '""', '"abc"')


def test_undo_and_redo_walk_the_history_both_ways(run_program):
    _run(run_program, ["i 0 a", "i 1 b", "i 2 c", "u", "u", "u", "u", "p",
                       "r", "r", "r", "r", "p"],
         _REFUSED, '""', _REFUSED, '"abc"')


def test_a_new_edit_clears_redo_but_undo_does_not(run_program):
    _run(run_program, ["i 0 ab", "i 2 cd", "u", "u", "r", "p", "d 0 1", "r", "p"],
         '"ab"', _REFUSED, '"b"')


def test_an_empty_insert_is_an_edit(run_program):
    _run(run_program, ["i 0 ab", "u", "i 0 ", "r", "u", "p", "u", "p"],
         _REFUSED, '""', _REFUSED, '""')


def test_a_refused_edit_keeps_both_histories(run_program):
    _run(run_program, ["i 0 ab", "u", "i 5 x", "d 0 5", "r", "p", "u", "p"],
         _REFUSED, _REFUSED, '"ab"', '""')


def test_positions_count_characters_not_bytes(run_program):
    _run(run_program, ["i 0 héllo", "d 1 1", "p", "u", "i 2 \U0001f600", "p",
                       "i 7 !", "i 6 ?", "p", "d 5 2", "p"],
         '"hllo"', '"hé\U0001f600llo"', _REFUSED, '"hé\U0001f600llo?"',
         '"hé\U0001f600ll"')


def test_a_combining_mark_is_its_own_character(run_program):
    # "e" + U+0301 COMBINING ACUTE ACCENT: two characters, one glyph.
    _run(run_program, ["i 0 e\u0301x", "d 1 1", "p"], '"ex"')


def test_large_numbers_are_refused(run_program):
    _run(run_program, ["i 0 abc", "i 3 d", "d 5 9", "i 999999999 x",
                       "d 999999999 999999999", "p"],
         _REFUSED, _REFUSED, _REFUSED, '"abcd"')


@pytest.mark.parametrize("line", [
    "", "x", "uu", "up", "pp", "i", "i ", "i 5", "i x y", "i 1x y", "i  1 y",
    "i -1 y", "d", "d 1", "d 1 ", "d 1 2 3", "d 1  2", "d  1 2", "d 1 -2",
    "d 1 x", "z 0 y",
], ids=lambda line: repr(line))
def test_a_line_that_is_not_a_command_is_answered_and_changes_nothing(run_program, line):
    _run(run_program, ["i 0 ab", line, "p", "u", "p"], _REFUSED, '"ab"', '""')


def test_quit_ends_the_session_and_later_lines_are_not_read(run_program):
    assert run_program("i 0 ab\nq\np\n") == ""
    assert run_program("p\nq\np") == '""\n'


def test_end_of_input_without_a_final_newline(run_program):
    assert run_program("i 0 ab\np") == '"ab"\n'
    assert run_program("i 0 ab") == ""


def test_random_sessions_match_the_rules(run_program):
    rng = random.Random(2026)
    alphabet = "ab é中\U0001f600\""
    for _ in range(25):
        lines: list[str] = []
        for _ in range(rng.randint(1, 30)):
            roll = rng.random()
            if roll < 0.35:
                text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 4)))
                lines.append(f"i {rng.randint(0, 12)} {text}")
            elif roll < 0.55:
                lines.append(f"d {rng.randint(0, 10)} {rng.randint(0, 4)}")
            elif roll < 0.7:
                lines.append("u")
            elif roll < 0.8:
                lines.append("r")
            elif roll < 0.95:
                lines.append("p")
            else:
                lines.append(rng.choice(["x", "i 1", "d 1", "uu"]))
        lines.append("p")
        _matches(run_program(_stdin(lines)), _oracle(lines))
