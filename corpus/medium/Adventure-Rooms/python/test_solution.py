import io
import sys

import pytest


def run(sub, lines, state=None):
    """Replay a command script from a fresh game, collecting outputs."""
    if state is None:
        state = sub.new_game()
    outputs = []
    for line in lines:
        state, out = sub.execute(state, line)
        outputs.append(out)
    return state, outputs


HALL = ("You are in a dusty entrance hall.\n"
        "Exits: north, west.\n"
        "You see: lamp.")


def test_look_golden(sub):
    _, outs = run(sub, ["look"])
    assert outs == [HALL]


def test_full_transcript_hand_computed(sub):
    _, outs = run(sub, [
        "look", "take lamp", "look", "go north", "take book", "go west",
        "take key", "inventory", "go east", "go north", "drop book", "look",
    ])
    assert outs == [
        HALL,
        "Taken.",
        "You are in a dusty entrance hall.\nExits: north, west.",
        "You are in a book-lined library.\nExits: north, south, west.\nYou see: book.",
        "Taken.",
        "You are in a damp stone cellar.\nExits: east.\nYou see: key.",
        "Taken.",
        "You are carrying: lamp, book, key.",
        "You are in a book-lined library.\nExits: north, south, west.",
        "You are in a cramped attic.\nExits: south.",
        "Dropped.",
        "You are in a cramped attic.\nExits: south.\nYou see: book.",
    ]


def test_bad_direction_leaves_you_in_place(sub):
    _, outs = run(sub, ["go south", "go up", "go", "look"])
    assert outs == ["You can't go that way.", "You can't go that way.",
                    "Go where?", HALL]


def test_take_and_drop_failures(sub):
    _, outs = run(sub, ["take sword", "take", "drop lamp", "drop"])
    assert outs == ["There is no sword here.", "Take what?",
                    "You are not carrying lamp.", "Drop what?"]


def test_dropped_item_stays_where_left(sub):
    _, outs = run(sub, ["take lamp", "go north", "drop lamp", "go south",
                        "go north", "look"])
    assert outs[-1] == ("You are in a book-lined library.\n"
                        "Exits: north, south, west.\n"
                        "You see: book, lamp.")


def test_inventory_empty(sub):
    _, outs = run(sub, ["inventory"])
    assert outs == ["You are carrying nothing."]


def test_unknown_verb_raises(sub):
    state = sub.new_game()
    with pytest.raises(ValueError):
        sub.execute(state, "dance")
    with pytest.raises(ValueError):
        sub.execute(state, "")


def test_quit_is_terminal(sub):
    state, outs = run(sub, ["quit"])
    assert outs == ["Goodbye."]
    with pytest.raises(ValueError):
        sub.execute(state, "look")
    with pytest.raises(ValueError):
        sub.execute(state, "quit")


def test_two_games_are_independent(sub):
    run(sub, ["take lamp"])
    _, outs = run(sub, ["look"])
    assert outs == [HALL]


def test_dispatch_consults_the_table_at_call_time(sub):
    def xyzzy(state, arg):
        return state, "Nothing happens."

    sub.VERBS["xyzzy"] = xyzzy
    _, out = sub.execute(sub.new_game(), "xyzzy")
    assert out == "Nothing happens."


def _feed(monkeypatch, text: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


def test_main_threads_successful_state_after_a_nonmutating_error(
        sub, monkeypatch, capsys):
    initial = {"over": False, "name": "initial"}
    middle = {"over": False, "name": "middle"}
    terminal = {"over": True, "name": "terminal"}
    calls = []

    monkeypatch.setattr(sub, "new_game", lambda: initial)
    monkeypatch.setattr(sub, "_look", lambda state: (
        "starting room" if state is initial
        else pytest.fail("main looked at the wrong initial state")
    ))

    def fake_execute(state, line):
        calls.append((state, line))
        if line == "dance":
            raise ValueError("unknown verb: dance")
        if line == "look":
            return middle, "Looked."
        assert state is middle
        return terminal, "Goodbye."

    monkeypatch.setattr(sub, "execute", fake_execute)
    _feed(monkeypatch, "dance\nlook\nquit\nnever read\n")
    sub.main()

    assert calls == [
        (initial, "dance"),
        (initial, "look"),
        (middle, "quit"),
    ]
    assert capsys.readouterr().out.splitlines() == [
        "starting room",
        "unknown verb: dance",
        "Looked.",
        "Goodbye.",
    ]


def test_main_hands_each_line_to_execute_unchanged(sub, monkeypatch, capsys):
    seen = []

    def fake_execute(state, line):
        seen.append(line)
        return state, "ok"

    monkeypatch.setattr(sub, "execute", fake_execute)
    _feed(monkeypatch, "  go north \n\nLOOK")
    sub.main()
    assert seen == ["  go north ", "", "LOOK"]


def test_main_ends_silently_at_end_of_input(sub, monkeypatch, capsys):
    _feed(monkeypatch, "take lamp\n")
    sub.main()
    assert capsys.readouterr().out == HALL + "\nTaken.\n"


def test_main_prints_the_python_wording(sub, monkeypatch, capsys):
    _feed(monkeypatch, "take lamp\ngo north\ntake sword\ndance\ninventory\nquit\nlook\n")
    sub.main()
    assert capsys.readouterr().out == HALL + """
Taken.
You are in a book-lined library.
Exits: north, south, west.
You see: book.
There is no sword here.
unknown verb: dance
You are carrying: lamp.
Goodbye.
"""
