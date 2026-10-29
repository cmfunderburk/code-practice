import sys
from collections import Counter


def step(live: set[tuple[int, int]], rows: int,
         cols: int) -> set[tuple[int, int]]:
    counts = Counter(
        (r + dr, c + dc)
        for r, c in live
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    )
    return {
        (r, c)
        for (r, c), n in counts.items()
        if (n == 3 or (n == 2 and (r, c) in live))
        and 0 <= r < rows and 0 <= c < cols
    }


def parse_input(text: str) -> tuple[int, int, int, list[str]]:
    """Validate SPEC §2; return rows, cols, generations, and the grid lines."""
    header, *grid = text.splitlines() or [""]
    try:
        rows, cols, generations = map(int, header.split())
    except ValueError:
        raise ValueError(
            f"header needs rows cols generations: {header!r}") from None
    if not (1 <= rows <= 100 and 1 <= cols <= 100 and 0 <= generations <= 1000):
        raise ValueError(
            f"need 1-100 rows and cols, 0-1000 generations: {header!r}")
    if len(grid) != rows:
        raise ValueError(f"expected {rows} grid lines, got {len(grid)}")
    for r, line in enumerate(grid):
        if len(line) != cols or set(line) - {"#", "."}:
            raise ValueError(f"row {r} must be {cols} of '#' or '.': {line!r}")
    return rows, cols, generations, grid


def _render(live: set[tuple[int, int]], rows: int, cols: int) -> str:
    return "\n".join(
        "".join("#" if (r, c) in live else "." for c in range(cols))
        for r in range(rows)
    )


def main() -> None:
    try:
        rows, cols, generations, grid = parse_input(sys.stdin.read())
    except ValueError as err:
        print(f"error: {err}")
        return
    live = {(r, c) for r, line in enumerate(grid)
            for c, ch in enumerate(line) if ch == "#"}
    for gen in range(generations + 1):
        if gen:
            live = step(live, rows, cols)
        print(f"gen {gen}")
        print(_render(live, rows, cols))


if __name__ == "__main__":
    main()
