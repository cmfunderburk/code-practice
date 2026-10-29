import io
import random
import sys

import pytest


def snapshot(logo):
    return logo.position, logo.heading, logo.pen_down, logo.segments


def test_square_is_hand_computed_and_repeat_is_atomic(sub):
    logo = sub.Logo()
    logo.execute("REPEAT 4 [ FORWARD 2 LEFT ]")
    assert snapshot(logo) == (
        (0, 0), "E", True,
        (((0, 0), (2, 0)), ((2, 0), (2, 2)),
         ((2, 2), (0, 2)), ((0, 2), (0, 0))),
    )
    logo.undo()
    assert snapshot(logo) == ((0, 0), "E", True, ())
    with pytest.raises(ValueError):
        logo.undo()


def test_each_top_level_command_is_one_history_entry(sub):
    logo = sub.Logo()
    logo.execute("FORWARD 2 RIGHT FORWARD 3")
    assert snapshot(logo) == (
        (2, -3), "S", True,
        (((0, 0), (2, 0)), ((2, 0), (2, -3))),
    )
    logo.undo()
    assert snapshot(logo) == ((2, 0), "S", True, (((0, 0), (2, 0)),))
    logo.undo()
    assert snapshot(logo) == ((2, 0), "E", True, (((0, 0), (2, 0)),))
    logo.undo()
    assert snapshot(logo) == ((0, 0), "E", True, ())


def test_pen_state_moves_without_drawing(sub):
    logo = sub.Logo()
    logo.execute("PENUP FORWARD 3 LEFT FORWARD 2 PENDOWN RIGHT FORWARD 1")
    assert logo.position == (4, 2)
    assert logo.heading == "E"
    assert logo.pen_down
    assert logo.segments == (((3, 2), (4, 2)),)
    logo.undo()
    assert logo.position == (3, 2)
    assert logo.pen_down


def test_nested_repeat_and_case_insensitive_source(sub):
    logo = sub.Logo()
    logo.execute("repeat 2 [ forward 1 left repeat 2[forward 1 right] ]")
    assert logo.position == (3, -1)
    assert logo.heading == "W"
    assert len(logo.segments) == 6


def test_parse_render_round_trip_is_canonical(sub):
    source = "repeat 2[forward 3 left repeat 4 [ penup right ]] pendown"
    program = sub.parse(source)
    rendered = sub.render(program)
    assert rendered == \
        "REPEAT 2 [ FORWARD 3 LEFT REPEAT 4 [ PENUP RIGHT ] ] PENDOWN"
    assert sub.parse(rendered) == program
    assert sub.render(sub.parse("")) == ""


@pytest.mark.parametrize("bad", [
    "FORWARD", "FORWARD 0", "FORWARD -2", "FORWARD nope", "SPIN",
    "]", "REPEAT 2 FORWARD 1", "REPEAT 0 [ LEFT ]", "REPEAT 2 [ LEFT",
])
def test_bad_source_is_atomic(sub, bad):
    logo = sub.Logo()
    logo.execute("FORWARD 2")
    before = snapshot(logo)
    with pytest.raises(ValueError):
        logo.execute(bad)
    assert snapshot(logo) == before
    logo.undo()  # failed input did not add a history entry
    assert logo.position == (0, 0)


def test_commands_are_values_with_pure_apply_and_inverse(sub):
    command = sub.parse("FORWARD 3")[0]
    before = sub.Drawing()
    first = command.apply(before)
    second = command.apply(before)
    assert first == second
    assert before == sub.Drawing()
    assert command.inverse(before).apply(first) == before


def _source(program):
    parts = []
    for op, arg in program:
        if op == "forward":
            parts.extend(("FORWARD", str(arg)))
        elif op == "repeat":
            count, body = arg
            parts.extend(("REPEAT", str(count), "[", _source(body), "]"))
        else:
            parts.append(op.upper())
    return " ".join(parts)


def _model(program, state=None):
    x, y, heading, pen, segments = state or (0, 0, 0, True, [])
    vectors = ((1, 0), (0, 1), (-1, 0), (0, -1))
    for op, arg in program:
        if op == "forward":
            dx, dy = vectors[heading]
            end = (x + dx * arg, y + dy * arg)
            if pen:
                segments.append(((x, y), end))
            x, y = end
        elif op == "left":
            heading = (heading + 1) % 4
        elif op == "right":
            heading = (heading - 1) % 4
        elif op == "penup":
            pen = False
        elif op == "pendown":
            pen = True
        else:
            count, body = arg
            for _ in range(count):
                x, y, heading, pen, segments = _model(
                    body, (x, y, heading, pen, segments))
    return x, y, heading, pen, segments


def _program(rng, depth):
    result = []
    for _ in range(rng.randint(1, 6)):
        choices = ["forward", "left", "right", "penup", "pendown"]
        if depth:
            choices.append("repeat")
        op = rng.choice(choices)
        if op == "forward":
            result.append((op, rng.randint(1, 5)))
        elif op == "repeat":
            result.append((op, (rng.randint(1, 3), _program(rng, depth - 1))))
        else:
            result.append((op, None))
    return result


def test_seeded_program_sweep_against_flat_interpreter(sub):
    rng = random.Random(20260710)
    for _ in range(100):
        program = _program(rng, 2)
        x, y, heading, pen, segments = _model(program)
        logo = sub.Logo()
        logo.execute(_source(program))
        assert snapshot(logo) == (
            (x, y), "ENWS"[heading], pen, tuple(segments),
        )


def _feed(monkeypatch, text: str) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))


def test_main_reports_each_line_in_the_python_wording(sub, monkeypatch, capsys):
    _feed(monkeypatch, "FORWARD 2 LEFT\nSPIN\nundo\n\nUNDO\nUNDO\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        "x=2 y=0 heading=N pen=down segments=1",
        "0,0 -> 2,0",
        "error: unknown command: SPIN",
        "x=2 y=0 heading=E pen=down segments=1",
        "0,0 -> 2,0",
        "x=2 y=0 heading=E pen=down segments=1",
        "0,0 -> 2,0",
        "x=0 y=0 heading=E pen=down segments=0",
        "error: nothing to undo",
    ]


def test_main_sends_undo_lines_to_undo_and_the_rest_to_execute(
        sub, monkeypatch, capsys):
    calls = []

    class Recorder(sub.Logo):
        def execute(self, source):
            calls.append(("execute", source))

        def undo(self):
            calls.append(("undo",))

    monkeypatch.setattr(sub, "Logo", Recorder)
    _feed(monkeypatch, " Undo \n\nundo undo\nforward 1")
    sub.main()
    assert calls == [("undo",), ("execute", ""), ("execute", "undo undo"),
                     ("execute", "forward 1")]
    assert len(capsys.readouterr().out.splitlines()) == 4
