import io
import sys

import pytest


def _board(x: set[int], o: set[int]) -> tuple[str, ...]:
    return tuple("X" if i in x else "O" if i in o else "" for i in range(9))


# Every winning line, as hand-picked positions (X on the line, O elsewhere).
WIN_FIXTURES = [
    ({0, 1, 2}, {3, 4}), ({3, 4, 5}, {0, 1}), ({6, 7, 8}, {0, 1}),
    ({0, 3, 6}, {1, 2}), ({1, 4, 7}, {0, 2}), ({2, 5, 8}, {0, 1}),
    ({0, 4, 8}, {1, 2}), ({2, 4, 6}, {0, 1}),
]

DRAW = _board({0, 2, 3, 5, 7}, {1, 4, 6, 8})


def test_every_winning_line(sub):
    for x, o in WIN_FIXTURES:
        assert sub.winner(_board(x, o)) == "X", (x, o)


def test_draw_and_ongoing(sub):
    assert sub.winner(DRAW) is None
    assert sub.is_draw(DRAW) is True
    mid = _board({0}, {4})
    assert sub.winner(mid) is None and sub.is_draw(mid) is False


def test_to_move_alternates(sub):
    b = sub.EMPTY_BOARD  # the module's empty board
    assert sub.to_move(b) == "X"
    b = sub.play(b, 0)
    assert sub.to_move(b) == "O"
    b = sub.play(b, 4)
    assert sub.to_move(b) == "X"


def test_play_is_pure(sub):
    b0 = sub.EMPTY_BOARD
    b1 = sub.play(b0, 0)
    assert b0 == ("",) * 9          # original untouched
    assert b1[0] == "X"


def test_top_row_win_sequence(sub):
    b = sub.EMPTY_BOARD
    for pos in (0, 4, 1, 5, 2):     # X: 0,1,2  O: 4,5
        b = sub.play(b, pos)
    assert sub.winner(b) == "X"
    assert sub.legal_moves(b) == ()


def test_illegal_moves_raise(sub):
    b = sub.play(sub.EMPTY_BOARD, 0)
    with pytest.raises(ValueError):
        sub.play(b, 0)              # occupied
    with pytest.raises(ValueError):
        sub.play(b, 9)              # out of range
    won = _board({0, 1, 2}, {3, 4})
    with pytest.raises(ValueError):
        sub.play(won, 5)            # game decided


def _feed(monkeypatch, text: str) -> None:
    stdin = io.TextIOWrapper(io.BytesIO(text.encode()), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)


def test_main_threads_each_returned_board(sub, monkeypatch, capsys):
    initial = object()
    after_move = object()
    calls = []

    def winner(board):
        calls.append(("winner", board))
        return "X" if board is after_move else None

    def is_draw(board):
        calls.append(("is_draw", board))
        return False

    def render(board):
        calls.append(("render", board))
        return "after" if board is after_move else "before"

    def to_move(board):
        calls.append(("to_move", board))
        return "X"

    def play(board, pos):
        calls.append(("play", board, pos))
        if pos == 0:
            raise ValueError("illegal move: 0")
        return after_move

    monkeypatch.setattr(sub, "EMPTY_BOARD", initial)
    monkeypatch.setattr(sub, "winner", winner)
    monkeypatch.setattr(sub, "is_draw", is_draw)
    monkeypatch.setattr(sub, "_render", render)
    monkeypatch.setattr(sub, "to_move", to_move)
    monkeypatch.setattr(sub, "play", play)
    _feed(monkeypatch, "x\n0\n4\nignored\n")

    sub.main()

    assert ("winner", initial) in calls and ("winner", after_move) in calls
    assert ("is_draw", initial) in calls
    assert ("to_move", initial) in calls
    assert [call for call in calls if call[0] == "render"] == [
        ("render", initial),
        ("render", initial),
        ("render", initial),
        ("render", after_move),
    ]
    assert [call for call in calls if call[0] == "play"] == [
        ("play", initial, 0),
        ("play", initial, 4),
    ]
    assert capsys.readouterr().out.splitlines() == [
        "before", "X to move",
        "a cell 0-8, please",
        "before", "X to move",
        "illegal move: 0",
        "before", "X to move",
        "after", "X wins!",
    ]


def test_main_answers_bad_lines_and_lets_the_core_judge_cells(sub, monkeypatch, capsys):
    # int() reads the line, spaces and all; the core rejects a cell off the
    # board as it rejects a marked one.
    _feed(monkeypatch, " 4 \n4\n9\n-1\nx\n0\n")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        ". . .", ". . .", ". . .", "X to move",
        ". . .", ". X .", ". . .", "O to move",
        "illegal move: 4",
        ". . .", ". X .", ". . .", "O to move",
        "illegal move: 9",
        ". . .", ". X .", ". . .", "O to move",
        "illegal move: -1",
        ". . .", ". X .", ". . .", "O to move",
        "a cell 0-8, please",
        ". . .", ". X .", ". . .", "O to move",
        "O . .", ". X .", ". . .", "X to move",
        "game abandoned",
    ]


def test_main_reports_a_draw(sub, monkeypatch, capsys):
    _feed(monkeypatch, "0\n1\n2\n4\n3\n5\n7\n6\n8\n")
    sub.main()
    assert capsys.readouterr().out.splitlines()[-4:] == [
        "X O X", "X O O", "O X X", "draw",
    ]


def test_main_abandons_at_end_of_input(sub, monkeypatch, capsys):
    monkeypatch.setattr(sub, "play", lambda *args: pytest.fail("played"))
    _feed(monkeypatch, "")
    sub.main()
    assert capsys.readouterr().out.splitlines() == [
        ". . .", ". . .", ". . .", "X to move", "game abandoned",
    ]
