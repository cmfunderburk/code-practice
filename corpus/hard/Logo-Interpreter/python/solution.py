from __future__ import annotations

from dataclasses import dataclass

VECTORS = ((1, 0), (0, 1), (-1, 0), (0, -1))
HEADINGS = "ENWS"


@dataclass(frozen=True)
class Drawing:
    position: tuple[int, int] = (0, 0)
    heading: int = 0
    pen_down: bool = True
    segments: tuple[tuple[tuple[int, int], tuple[int, int]], ...] = ()


@dataclass(frozen=True)
class Command:
    op: str
    arg: int | tuple[Command, ...] | None = None

    def apply(self, drawing: Drawing) -> Drawing:
        if self.op == "forward":
            dx, dy = VECTORS[drawing.heading]
            end = (drawing.position[0] + dx * self.arg,
                   drawing.position[1] + dy * self.arg)
            segments = drawing.segments
            if drawing.pen_down:
                segments += ((drawing.position, end),)
            return Drawing(end, drawing.heading, drawing.pen_down, segments)
        if self.op in {"left", "right"}:
            turn = 1 if self.op == "left" else -1
            return Drawing(drawing.position, (drawing.heading + turn) % 4,
                           drawing.pen_down, drawing.segments)
        if self.op in {"penup", "pendown"}:
            return Drawing(drawing.position, drawing.heading,
                           self.op == "pendown", drawing.segments)
        if self.op == "repeat":
            result = drawing
            count, body = self.arg
            for _ in range(count):
                for command in body:
                    result = command.apply(result)
            return result
        raise ValueError(f"unknown command: {self.op}")

    def inverse(self, before: Drawing) -> Restore:
        return Restore(before)


@dataclass(frozen=True)
class Restore:
    drawing: Drawing

    def apply(self, _drawing: Drawing) -> Drawing:
        return self.drawing


def _positive(token: str) -> int:
    try:
        value = int(token)
    except ValueError as err:
        raise ValueError(f"expected a positive integer, got {token!r}") from err
    if value < 1:
        raise ValueError("counts and distances must be positive")
    return value


def _parse(tokens: list[str], pos: int, nested: bool) -> tuple[tuple[Command, ...], int]:
    commands: list[Command] = []
    while pos < len(tokens):
        op = tokens[pos]
        pos += 1
        if op == "]":
            if not nested:
                raise ValueError("unexpected ]")
            return tuple(commands), pos
        if op == "FORWARD":
            if pos == len(tokens):
                raise ValueError("FORWARD needs a distance")
            commands.append(Command("forward", _positive(tokens[pos])))
            pos += 1
        elif op in {"LEFT", "RIGHT", "PENUP", "PENDOWN"}:
            commands.append(Command(op.lower()))
        elif op == "REPEAT":
            if pos + 1 >= len(tokens) or tokens[pos + 1] != "[":
                raise ValueError("REPEAT needs a count and [ block ]")
            count = _positive(tokens[pos])
            body, pos = _parse(tokens, pos + 2, True)
            commands.append(Command("repeat", (count, body)))
        else:
            raise ValueError(f"unknown command: {op}")
    if nested:
        raise ValueError("missing ]")
    return tuple(commands), pos


def parse(source: str) -> tuple[Command, ...]:
    tokens = source.replace("[", " [ ").replace("]", " ] ").upper().split()
    return _parse(tokens, 0, False)[0]


def render(program: tuple[Command, ...]) -> str:
    parts: list[str] = []
    for command in program:
        if command.op == "forward":
            parts.extend(("FORWARD", str(command.arg)))
        elif command.op == "repeat":
            count, body = command.arg
            parts.extend(("REPEAT", str(count), "[", render(body), "]"))
        else:
            parts.append(command.op.upper())
    return " ".join(parts)


class Logo:
    def __init__(self) -> None:
        self._drawing = Drawing()
        self._undo: list[Restore] = []

    @property
    def position(self) -> tuple[int, int]:
        return self._drawing.position

    @property
    def heading(self) -> str:
        return HEADINGS[self._drawing.heading]

    @property
    def pen_down(self) -> bool:
        return self._drawing.pen_down

    @property
    def segments(self) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
        return self._drawing.segments

    def execute(self, source: str) -> None:
        for command in parse(source):
            before = self._drawing
            self._drawing = command.apply(before)
            self._undo.append(command.inverse(before))

    def undo(self) -> None:
        if not self._undo:
            raise ValueError("nothing to undo")
        self._drawing = self._undo.pop().apply(self._drawing)


def _is_undo(line: str) -> bool:
    """The line's only word is UNDO, in any case."""
    return line.upper().split() == ["UNDO"]


def _report(logo: Logo) -> str:
    """The state line, then the drawing: one line per segment, oldest first."""
    (x, y), segments = logo.position, logo.segments
    pen = "down" if logo.pen_down else "up"
    lines = [f"x={x} y={y} heading={logo.heading} pen={pen} segments={len(segments)}"]
    lines += [f"{x1},{y1} -> {x2},{y2}" for (x1, y1), (x2, y2) in segments]
    return "\n".join(lines)


def main() -> None:
    logo = Logo()
    while True:
        try:
            line = input()
        except EOFError:
            return
        try:
            if _is_undo(line):
                logo.undo()
            else:
                logo.execute(line)
        except ValueError as err:
            print(f"error: {err}")
        else:
            print(_report(logo))


if __name__ == "__main__":
    main()
