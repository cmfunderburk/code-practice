import io
import random
import sys

import pytest


class SnapshotOracle:
    """Reference: saves a copy of the whole text before each edit, not commands."""

    def __init__(self, text: str = "") -> None:
        self.text = text
        self.undo_stack: list[str] = []
        self.redo_stack: list[str] = []

    def _edit(self, new_text: str) -> None:
        self.undo_stack.append(self.text)
        self.text = new_text
        self.redo_stack.clear()

    def insert(self, pos: int, s: str) -> None:
        self._edit(self.text[:pos] + s + self.text[pos:])

    def delete(self, pos: int, n: int) -> None:
        self._edit(self.text[:pos] + self.text[pos + n:])

    def undo(self) -> None:
        self.redo_stack.append(self.text)
        self.text = self.undo_stack.pop()

    def redo(self) -> None:
        self.undo_stack.append(self.text)
        self.text = self.redo_stack.pop()


def test_scripted_replay_hand_computed(sub):
    buf = sub.EditorBuffer()
    buf.insert(0, "hello")
    assert buf.text == "hello"
    buf.insert(5, " world")
    assert buf.text == "hello world"
    buf.delete(0, 6)
    assert buf.text == "world"
    buf.undo()
    assert buf.text == "hello world"
    buf.undo()
    assert buf.text == "hello"
    buf.redo()
    assert buf.text == "hello world"
    buf.insert(0, "big ")
    assert buf.text == "big hello world"
    with pytest.raises(ValueError):
        buf.redo()  # new edit cleared the redo stack


def test_initial_text_and_positions_at_the_ends(sub):
    buf = sub.EditorBuffer("ab")
    buf.insert(2, "c")  # insert at len is legal
    assert buf.text == "abc"
    buf.delete(0, 3)  # delete the whole buffer
    assert buf.text == ""
    buf.undo()
    assert buf.text == "abc"


def test_edit_validation(sub):
    buf = sub.EditorBuffer("abc")
    with pytest.raises(ValueError):
        buf.insert(-1, "x")
    with pytest.raises(ValueError):
        buf.insert(4, "x")
    with pytest.raises(ValueError):
        buf.delete(0, 0)
    with pytest.raises(ValueError):
        buf.delete(2, 2)
    with pytest.raises(ValueError):
        buf.delete(-1, 1)
    assert buf.text == "abc"


def test_undo_and_redo_refuse_when_their_stack_is_empty(sub):
    buf = sub.EditorBuffer("seed")
    with pytest.raises(ValueError):
        buf.undo()  # fresh buffer: nothing to undo
    with pytest.raises(ValueError):
        buf.redo()  # fresh buffer: nothing to redo
    buf.insert(4, "!")
    buf.undo()
    assert buf.text == "seed"
    with pytest.raises(ValueError):
        buf.undo()  # back at the initial state: nothing left


def test_failed_edit_leaves_history_intact(sub):
    buf = sub.EditorBuffer()
    buf.insert(0, "ab")
    buf.undo()  # text "", the insert sits on the redo stack
    with pytest.raises(ValueError):
        buf.insert(5, "x")  # rejected: must not push undo or clear redo
    with pytest.raises(ValueError):
        buf.delete(0, 5)
    buf.redo()  # still redoable
    assert buf.text == "ab"
    buf.undo()
    assert buf.text == ""


def test_random_edits_match_a_snapshot_history(sub):
    rng = random.Random(2026)
    buf = sub.EditorBuffer("seed text")
    oracle = SnapshotOracle("seed text")
    alphabet = "abcdefgh "
    for _ in range(300):
        roll = rng.random()
        if roll < 0.4:
            pos = rng.randint(0, len(oracle.text))
            s = "".join(rng.choice(alphabet)
                        for _ in range(rng.randint(1, 5)))
            buf.insert(pos, s)
            oracle.insert(pos, s)
        elif roll < 0.6 and oracle.text:
            n = rng.randint(1, min(5, len(oracle.text)))
            pos = rng.randint(0, len(oracle.text) - n)
            buf.delete(pos, n)
            oracle.delete(pos, n)
        elif roll < 0.8 and oracle.undo_stack:
            buf.undo()
            oracle.undo()
        elif oracle.redo_stack:
            buf.redo()
            oracle.redo()
        assert buf.text == oracle.text


def test_commands_are_values_that_apply_and_invert(sub):
    ins = sub.Insert(1, "xy")
    assert ins.apply("ab") == "axyb"
    assert ins.invert().apply("axyb") == "ab"
    dele = sub.Delete(1, "b")
    assert dele.apply("abc") == "ac"
    assert dele.invert().apply("ac") == "abc"
    assert ins == sub.Insert(1, "xy")  # equal fields make equal commands


def _feed(monkeypatch, text: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


def test_main_prints_the_python_versions_messages(sub, monkeypatch, capsys):
    _feed(monkeypatch, "i 0 ab\ni 5 x\nd 1 9\nu\nu\nr\nr\nx\np\nq\np\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        "insert out of range: 5",
        "delete out of range: 1+9",
        "nothing to undo",
        "nothing to redo",
        sub.HELP,
        '"ab"',
    ]


def test_main_reads_numbers_as_ascii_digits_of_any_length(sub, monkeypatch, capsys):
    _feed(monkeypatch, "i 000 abc\nd 01 1\ni 1234567890123 x\ni \u0663 y\ni +1 y\np\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        "insert out of range: 1234567890123",
        sub.HELP,
        sub.HELP,
        '"ac"',
    ]


def test_main_keeps_a_carriage_return_in_the_text(sub, monkeypatch, capsys):
    _feed(monkeypatch, "i 0 a\r\nu\r\np\n")
    sub.main()
    assert capsys.readouterr().out == f'{sub.HELP}\n"a\r"\n'
