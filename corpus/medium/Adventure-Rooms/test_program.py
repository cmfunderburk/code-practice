"""Adventure Rooms smoke suite: each language, run whole on stdin (SPEC §5).

The tests use only the `run_program` fixture (`corpus/conftest.py`), which runs the
program, in each language, on the given stdin and returns its stdout (asserting exit
status 0). Each implementation describes rooms and words its answers its own way, so
an answer is read only for the facts SPEC §5 fixes: which rooms and items it names.
A line's answer is what the session prints past the lines before it (end of input
adds nothing), so `_answers` runs each prefix of a session. Random walks are checked
against `_WORLD`, the suite's own copy of SPEC §1, never against an implementation
under test.
"""

import random
import re

_WORLD = {
    "hall": ({"north": "library", "west": "garden"}, ["lamp"]),
    "library": ({"north": "attic", "south": "hall", "west": "cellar"}, ["book"]),
    "cellar": ({"east": "library"}, ["key"]),
    "attic": ({"south": "library"}, []),
    "garden": ({"east": "hall"}, ["rose", "spade"]),
}
_ROOM = re.compile(r"\b(hall|library|cellar|attic|garden)\b")
_ITEM = re.compile(r"\b(lamp|book|key|rose|spade)\b")


def _answers(run_program, lines: list[str]) -> tuple[str, list[str]]:
    """The opening text, then each line's answer."""
    outs = [run_program("".join(f"{line}\n" for line in lines[:k]))
            for k in range(len(lines) + 1)]
    for before, after in zip(outs, outs[1:]):
        assert after.startswith(before), (before, after)
    return outs[0], [after[len(before):] for before, after in zip(outs, outs[1:])]


def _describes(answer: str, room: str, *items: str) -> None:
    assert set(_ROOM.findall(answer)) == {room}, (answer, room)
    assert set(items) <= set(_ITEM.findall(answer)), (answer, items)


def _stays(answer: str) -> None:
    assert answer.strip(), "no answer"
    assert not _ROOM.findall(answer), answer


def _carries(answer: str, *items: str) -> None:
    assert answer.strip(), "no answer"
    assert set(_ITEM.findall(answer)) == set(items), (answer, items)


def test_the_session_opens_in_the_hall(run_program):
    _describes(run_program(""), "hall", "lamp")


def test_spec_session(run_program):
    lines = ["take lamp", "go north", "take sword", "dance", "inventory", "quit"]
    opening, answers = _answers(run_program, lines)
    _describes(opening, "hall", "lamp")
    _stays(answers[0])
    _describes(answers[1], "library", "book")
    _stays(answers[2])
    _stays(answers[3])
    _carries(answers[4], "lamp")
    _stays(answers[5])


def test_every_exit_leads_where_the_map_says(run_program):
    lines = ["go west", "go east", "go north", "go west", "go east", "go north",
             "go south", "go south"]
    rooms = ["garden", "hall", "library", "cellar", "library", "attic", "library",
             "hall"]
    items = {"hall": ["lamp"], "library": ["book"], "cellar": ["key"], "attic": [],
             "garden": ["rose", "spade"]}
    _, answers = _answers(run_program, lines)
    for answer, room in zip(answers, rooms):
        _describes(answer, room, *items[room])


def test_a_refused_go_stays_put(run_program):
    _, answers = _answers(run_program, ["go south", "go up", "go", "look"])
    for answer in answers[:3]:
        _stays(answer)
    _describes(answers[3], "hall", "lamp")


def test_surrounding_spaces_are_ignored(run_program):
    _, answers = _answers(run_program, ["  go   north ", " take  book ", "inventory"])
    _describes(answers[0], "library")
    _carries(answers[2], "book")


def test_take_and_drop_move_items_in_order(run_program):
    lines = ["take lamp", "go west", "take spade", "take rose", "inventory",
             "drop spade", "inventory", "go east", "look"]
    _, answers = _answers(run_program, lines)
    _carries(answers[4], "lamp", "spade", "rose")
    _carries(answers[6], "lamp", "rose")
    _describes(answers[7], "hall")


def test_an_item_can_be_taken_only_where_it_is(run_program):
    lines = ["take lamp", "take lamp", "go north", "drop lamp", "go south",
             "take lamp", "inventory"]
    _, answers = _answers(run_program, lines)
    for answer in (answers[1], answers[3], answers[5]):
        _stays(answer)
    _carries(answers[6])


def test_a_dropped_item_stays_where_it_was_left(run_program):
    lines = ["take lamp", "go north", "drop lamp", "go south", "go north", "look"]
    _, answers = _answers(run_program, lines)
    _describes(answers[4], "library", "book", "lamp")
    _describes(answers[5], "library", "book", "lamp")


def test_refusals_answer_and_change_nothing(run_program):
    lines = ["take", "drop", "drop lamp", "take sword", "dance", "", "xyzzy plugh",
             "inventory", "look"]
    _, answers = _answers(run_program, lines)
    for answer in answers[:7]:
        _stays(answer)
    _carries(answers[7])
    _describes(answers[8], "hall", "lamp")


def test_quit_ends_the_session(run_program):
    _, answers = _answers(run_program, ["take lamp", "quit"])
    _stays(answers[1])
    session = "take lamp\nquit\n"
    assert run_program(session + "look\ninventory\n") == run_program(session)


def test_last_line_needs_no_newline(run_program):
    opening = run_program("")
    out = run_program("take lamp\ninventory")
    assert out.startswith(opening), out
    assert "lamp" in out[len(opening):]


def test_random_walks_follow_the_map(run_program):
    rng = random.Random(2026)
    for _ in range(4):
        room = "hall"
        items = {name: list(start) for name, (_, start) in _WORLD.items()}
        carried: list[str] = []
        lines = []
        expect = []
        for _ in range(12):
            exits, _ = _WORLD[room]
            kind = rng.randrange(5)
            if kind <= 1:
                direction = rng.choice(["north", "south", "east", "west"])
                lines.append(f"go {direction}")
                room = exits.get(direction, room)
                expect.append(("room", room) if direction in exits else ("stay",))
            elif kind == 2:
                item = rng.choice([*items[room], "sword"])
                lines.append(f"take {item}")
                if item in items[room]:
                    items[room].remove(item)
                    carried.append(item)
                expect.append(("stay",))
            elif kind == 3 and carried:
                item = rng.choice(carried)
                lines.append(f"drop {item}")
                carried.remove(item)
                items[room].append(item)
                expect.append(("stay",))
            else:
                lines.append(rng.choice(["look", "inventory"]))
                if lines[-1] == "look":
                    expect.append(("room", room))
                else:
                    expect.append(("carry", *carried))
            if expect[-1][0] == "room":
                expect[-1] = ("room", room, *items[room])
        _, answers = _answers(run_program, lines)
        for line, answer, (kind, *rest) in zip(lines, answers, expect):
            if kind == "room":
                _describes(answer, *rest)
            elif kind == "stay":
                _stays(answer)
            else:
                _carries(answer, *rest)
