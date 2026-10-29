import io
import sys
from types import SimpleNamespace

import pytest


def test_win_replay(sub):
    state = sub.new_game("banana")
    assert sub.masked(state) == "______"
    assert sub.status(state) == "playing"
    state = sub.guess(state, "a")
    assert sub.masked(state) == "_a_a_a"
    state = sub.guess(state, "x")          # miss
    assert sub.wrong_count(state) == 1
    state = sub.guess(state, "n")
    assert sub.masked(state) == "_anana"
    state = sub.guess(state, "b")
    assert sub.masked(state) == "banana"
    assert sub.status(state) == "won"


def test_loss_replay_six_wrong(sub):
    state = sub.new_game("banana")
    for letter in "cdefg":                 # 5 misses
        state = sub.guess(state, letter)
    assert sub.status(state) == "playing"
    state = sub.guess(state, "h")          # 6th miss
    assert sub.status(state) == "lost"
    assert sub.wrong_count(state) == 6


def test_custom_budget(sub):
    state = sub.guess(sub.new_game("io", max_wrong=1), "z")
    assert sub.status(state) == "lost"


def test_repeat_guess_raises_even_when_correct(sub):
    state = sub.guess(sub.new_game("banana"), "a")
    with pytest.raises(ValueError):
        sub.guess(state, "a")


def test_guess_after_game_over_raises(sub):
    state = sub.guess(sub.new_game("io", max_wrong=1), "z")
    with pytest.raises(ValueError):
        sub.guess(state, "i")


def test_guess_after_win_raises(sub):
    state = sub.guess(sub.guess(sub.new_game("io"), "i"), "o")
    assert sub.status(state) == "won"
    with pytest.raises(ValueError):
        sub.guess(state, "z")


def test_purity_input_state_unchanged_and_repeatable(sub):
    state = sub.new_game("banana")
    once = sub.guess(state, "a")
    again = sub.guess(state, "a")
    assert state.guessed == frozenset()    # input untouched
    assert once == again                   # same state twice -> equal results


def _feed(monkeypatch, text: str) -> None:
    stdin = io.TextIOWrapper(io.BytesIO(text.encode()), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)


def _secret(monkeypatch, sub, word: str) -> None:
    """Script the shell's pick; it must choose from the built-in WORDS."""
    def choice(seq):
        assert seq is sub.WORDS, "the secret is random.choice(WORDS)"
        return word

    monkeypatch.setattr(sub.random, "choice", choice)


def test_words_are_lowercase_with_two_different_letters(sub):
    # SPEC §1: no single letter can win alone.
    assert sub.WORDS
    for word in sub.WORDS:
        assert word.isascii() and word.isalpha() and word.islower(), word
        assert len(set(word)) >= 2, word


def test_main_threads_returned_state_through_the_core(sub, monkeypatch, capsys):
    initial = SimpleNamespace(max_wrong=6, secret="banana")
    after_guess = SimpleNamespace(max_wrong=6, secret="banana")
    calls: list[tuple[str, object]] = []

    def new_game(secret):
        calls.append(("new_game", secret))
        return initial

    def status(state):
        calls.append(("status", state))
        return "playing" if state is initial else "won"

    def masked(state):
        calls.append(("masked", state))
        return "______"

    def wrong_count(state):
        calls.append(("wrong_count", state))
        return 0

    def guess(state, letter):
        calls.append(("guess", (state, letter)))
        if letter == "a":
            raise ValueError("already guessed: a")
        return after_guess

    monkeypatch.setattr(sub, "new_game", new_game)
    monkeypatch.setattr(sub, "status", status)
    monkeypatch.setattr(sub, "masked", masked)
    monkeypatch.setattr(sub, "wrong_count", wrong_count)
    monkeypatch.setattr(sub, "guess", guess)
    _secret(monkeypatch, sub, "banana")
    _feed(monkeypatch, "?\nA\n b \nignored\n")

    sub.main()

    assert calls == [
        ("new_game", "banana"),
        ("status", initial),
        ("masked", initial),
        ("wrong_count", initial),
        ("status", initial),
        ("masked", initial),
        ("wrong_count", initial),
        ("guess", (initial, "a")),
        ("status", initial),
        ("masked", initial),
        ("wrong_count", initial),
        ("guess", (initial, "b")),
        ("status", after_guess),
        ("status", after_guess),
    ]
    assert capsys.readouterr().out.splitlines() == [
        "______  wrong: 0/6",
        "one letter a-z, please",
        "______  wrong: 0/6",
        "already guessed: a",
        "______  wrong: 0/6",
        "you won! the word was banana",
    ]


def test_main_plays_a_whole_game(sub, monkeypatch, capsys):
    _secret(monkeypatch, sub, "io")
    _feed(monkeypatch, "x\nI\ni\n7\no\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        "__  wrong: 0/6",
        "__  wrong: 1/6",
        "i_  wrong: 1/6",
        "already guessed: i",
        "i_  wrong: 1/6",
        "one letter a-z, please",
        "i_  wrong: 1/6",
        "you won! the word was io",
    ]


def test_main_reports_a_quit_at_end_of_input(sub, monkeypatch, capsys):
    _secret(monkeypatch, sub, "io")
    _feed(monkeypatch, "x")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        "__  wrong: 0/6",
        "__  wrong: 1/6",
        "you quit! the word was io",
    ]
