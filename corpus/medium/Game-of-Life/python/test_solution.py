import io
import sys

import pytest


# A blinker (a line of three live cells) flips between horizontal and vertical,
# a block (a 2 x 2 square) never changes, and a glider moves one cell diagonally
# every four generations (SPEC §1).
BLINKER = ({(2, 1), (2, 2), (2, 3)}, 5, 5)
BLINKER_NEXT = {(1, 2), (2, 2), (3, 2)}
BLOCK = ({(1, 1), (1, 2), (2, 1), (2, 2)}, 4, 4)
GLIDER = ({(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)}, 10, 10)


def _recount_step(live: set, rows: int, cols: int) -> set:
    # Reference: visit every cell of the grid and count its live neighbors
    # directly, a different method from step's Counter over the live cells.
    out = set()
    for r in range(rows):
        for c in range(cols):
            n = sum((r + dr, c + dc) in live
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                    if (dr, dc) != (0, 0))
            if n == 3 or ((r, c) in live and n == 2):
                out.add((r, c))
    return out


def _step(sub, live, rows, cols):
    return sub.step(set(live), rows, cols)


def test_blinker_oscillates(sub):
    assert _step(sub, *BLINKER) == BLINKER_NEXT
    assert _step(sub, BLINKER_NEXT, 5, 5) == BLINKER[0]


def test_block_is_still(sub):
    assert _step(sub, *BLOCK) == BLOCK[0]


def test_step_treats_cells_past_the_edge_as_dead(sub):
    assert _step(sub, {(0, 0)}, 3, 3) == set()
    # a blinker jammed against the top edge loses its off-grid birth
    assert _step(sub, {(0, 0), (0, 1), (0, 2)}, 3, 3) == {(0, 1), (1, 1)}


def test_glider_moves_one_cell_diagonally_every_four_generations(sub):
    live, rows, cols = GLIDER
    for _ in range(4):
        live = _step(sub, live, rows, cols)
    assert live == {(r + 1, c + 1) for r, c in GLIDER[0]}


def test_step_matches_a_cell_by_cell_recount(sub):
    for live, rows, cols in (BLINKER, BLOCK, GLIDER,
                             ({(1, 1), (1, 2), (2, 3), (3, 1)}, 5, 6)):
        assert _step(sub, live, rows, cols) == _recount_step(live, rows, cols)


def test_step_leaves_its_input_unchanged(sub):
    live = set(BLINKER[0])
    sub.step(live, 5, 5)
    assert live == BLINKER[0]


def _feed(monkeypatch, text: str) -> None:
    stdin = io.TextIOWrapper(io.BytesIO(text.encode()), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)


def test_main_builds_the_live_set_and_renders_each_step_result(sub, monkeypatch, capsys):
    stepped = []
    rendered = []
    successors = [object() for _ in range(3)]

    def fake_step(live, rows, cols):
        stepped.append((live, rows, cols))
        return successors[len(stepped) - 1]

    def fake_render(live, rows, cols):
        rendered.append((live, rows, cols))
        return f"frame-{len(rendered) - 1}"

    monkeypatch.setattr(sub, "step", fake_step)
    monkeypatch.setattr(sub, "_render", fake_render)
    _feed(monkeypatch, "3 4 3\n.#..\n..#.\n#...\n")
    sub.main()

    initial = rendered[0][0]
    assert initial == {(0, 1), (1, 2), (2, 0)}
    assert stepped == [(value, 3, 4) for value in [initial, *successors[:2]]]
    assert rendered == [(value, 3, 4) for value in [initial, *successors[:3]]]
    assert capsys.readouterr().out.splitlines() == [
        item
        for gen in range(4)
        for item in (f"gen {gen}", f"frame-{gen}")
    ]


def test_main_reports_bad_input_without_stepping(sub, monkeypatch, capsys):
    monkeypatch.setattr(sub, "step", lambda *args: pytest.fail("stepped"))
    _feed(monkeypatch, "3 3 1\n...\n.x.\n...\n")
    sub.main()
    out = capsys.readouterr().out
    assert out.startswith("error: ") and out.count("\n") == 1
