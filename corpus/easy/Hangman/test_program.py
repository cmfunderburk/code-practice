"""Hangman shared tests: each version run as a whole program (SPEC §4).

The Python, C, and Rust versions all run these tests. They use only the
`run_program` fixture (`corpus/conftest.py`), which runs the program in each
language with the given stdin, checks that it exits with status 0, and returns its
stdout. Each run picks its secret word at random, so every check must hold
whichever word is picked. The versions word their output differently, so only the
facts SPEC §4 fixes are read: the line that says the game was won or lost and
names the word, and the rules that can be seen through it. Each version's own
tests check exact games with a known word.
"""

import re
import string

_OUTCOME = re.compile(r"\b(won|lost)\b", re.IGNORECASE)
_LAST_WORD = re.compile(r"([a-z]+)\W*$")


def _guesses(*lines: str) -> str:
    return "".join(f"{line}\n" for line in lines)


def _ending(out: str) -> tuple[str, str] | None:
    """SPEC §4's (outcome, secret), or None when no line says won or lost."""
    found = []
    for line in out.splitlines():
        last = _LAST_WORD.search(line)
        before = line[:last.start()] if last else line
        outcome = _OUTCOME.search(before)
        if outcome:
            assert last, line
            found.append((outcome.group(1).lower(), last.group(1)))
    if not found:
        return None
    assert len(found) == 1, found
    return found[0]


def _alphabet_outcome(secret: str) -> str:
    """How guessing a, b, c, ... in order ends for this secret (SPEC §1)."""
    misses = 0
    for count, letter in enumerate(string.ascii_lowercase, start=1):
        misses += letter not in secret
        if set(secret) <= set(string.ascii_lowercase[:count]):
            return "won"
        if misses == 6:
            return "lost"
    raise AssertionError(f"not a lowercase word: {secret!r}")


def test_guessing_the_alphabet_ends_the_game_by_the_rules(run_program):
    # Each run picks its own word; whichever it is, the outcome must be the
    # one the rules give for guessing a to z in order.
    for _ in range(5):
        out = run_program(_guesses(*string.ascii_lowercase))
        ending = _ending(out)
        assert ending is not None, out[-500:]
        outcome, secret = ending
        assert outcome == _alphabet_outcome(secret), out[-500:]


def test_uppercase_guesses_count_as_lowercase(run_program):
    for _ in range(5):
        out = run_program(_guesses(*string.ascii_uppercase))
        ending = _ending(out)
        assert ending is not None, out[-500:]
        outcome, secret = ending
        assert outcome == _alphabet_outcome(secret), out[-500:]


def test_the_program_stops_reading_after_the_end(run_program):
    out = run_program(_guesses(*string.ascii_lowercase, *["?"] * 20))
    assert _OUTCOME.search(out.splitlines()[-1]), out[-500:]


def test_one_letter_alone_never_ends_the_game(run_program):
    # Every word has two different letters, and a repeated guess costs
    # nothing: one letter guessed fifty times neither wins nor loses.
    for letter in "eq":
        assert _ending(run_program(_guesses(*[letter] * 50))) is None, letter


def test_a_line_that_is_not_one_letter_is_answered(run_program):
    for line in ["", "ab", "7", "?", "é"]:
        assert len(run_program(_guesses(line)).splitlines()) > len(
            run_program("").splitlines()), repr(line)


def test_lines_that_are_not_one_letter_cost_nothing(run_program):
    # Were each rejected line a miss, six of them would lose the game.
    out = run_program(_guesses(*["?", "7", "ab", ""] * 25))
    assert _ending(out) is None


def test_end_of_input_stops_cleanly(run_program):
    for stdin in ["", "q\n", "q", "?\n"]:
        assert _ending(run_program(stdin)) is None, repr(stdin)
