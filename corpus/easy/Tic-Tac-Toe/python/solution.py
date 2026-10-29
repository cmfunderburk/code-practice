EMPTY_BOARD: tuple[str, ...] = ("",) * 9


_LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
          (0, 3, 6), (1, 4, 7), (2, 5, 8),
          (0, 4, 8), (2, 4, 6))


def to_move(board: tuple[str, ...]) -> str:
    return "X" if board.count("X") == board.count("O") else "O"


def winner(board: tuple[str, ...]) -> str | None:
    for a, b, c in _LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def is_draw(board: tuple[str, ...]) -> bool:
    return winner(board) is None and "" not in board


def legal_moves(board: tuple[str, ...]) -> tuple[int, ...]:
    if winner(board) is not None:
        return ()
    return tuple(i for i, cell in enumerate(board) if cell == "")


def play(board: tuple[str, ...], pos: int) -> tuple[str, ...]:
    if pos not in legal_moves(board):
        raise ValueError(f"illegal move: {pos}")
    mark = to_move(board)
    return board[:pos] + (mark,) + board[pos + 1:]


def _render(board: tuple[str, ...]) -> str:
    rows = (board[i:i + 3] for i in (0, 3, 6))
    return "\n".join(" ".join(cell or "." for cell in row) for row in rows)


def main() -> None:
    board = EMPTY_BOARD
    while winner(board) is None and not is_draw(board):
        print(_render(board))
        print(f"{to_move(board)} to move")
        try:
            line = input()
        except EOFError:
            print("game abandoned")
            return
        try:
            pos = int(line)
        except ValueError:
            print("a cell 0-8, please")
            continue
        try:
            board = play(board, pos)
        except ValueError as err:
            print(err)
    print(_render(board))
    print(f"{winner(board)} wins!" if winner(board) else "draw")


if __name__ == "__main__":
    main()
