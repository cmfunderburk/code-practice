from dataclasses import dataclass

HELP = "i <pos> <text> | d <pos> <n> | u | r | p | q"


@dataclass(frozen=True)
class Insert:
    pos: int
    text: str

    def apply(self, text: str) -> str:
        return text[:self.pos] + self.text + text[self.pos:]

    def invert(self) -> "Delete":
        return Delete(self.pos, self.text)


@dataclass(frozen=True)
class Delete:
    pos: int
    text: str

    def apply(self, text: str) -> str:
        return text[:self.pos] + text[self.pos + len(self.text):]

    def invert(self) -> Insert:
        return Insert(self.pos, self.text)


class EditorBuffer:
    def __init__(self, text: str = "") -> None:
        self._text = text
        self._undo: list[Insert | Delete] = []
        self._redo: list[Insert | Delete] = []

    @property
    def text(self) -> str:
        return self._text

    def insert(self, pos: int, s: str) -> None:
        if not 0 <= pos <= len(self._text):
            raise ValueError(f"insert out of range: {pos}")
        self._do(Insert(pos, s))

    def delete(self, pos: int, n: int) -> None:
        if n < 1 or pos < 0 or pos + n > len(self._text):
            raise ValueError(f"delete out of range: {pos}+{n}")
        self._do(Delete(pos, self._text[pos:pos + n]))

    def _do(self, command: Insert | Delete) -> None:
        self._text = command.apply(self._text)
        self._undo.append(command)
        self._redo.clear()

    def undo(self) -> None:
        if not self._undo:
            raise ValueError("nothing to undo")
        command = self._undo.pop()
        self._text = command.invert().apply(self._text)
        self._redo.append(command)

    def redo(self) -> None:
        if not self._redo:
            raise ValueError("nothing to redo")
        command = self._redo.pop()
        self._text = command.apply(self._text)
        self._undo.append(command)


def _number(text: str) -> int | None:
    """A position or count: ASCII digits, as an int."""
    return int(text) if text.isascii() and text.isdigit() else None


def _command(line: str) -> tuple[str, tuple[int | str, ...]] | None:
    """One line's verb and arguments, or None if it isn't a command."""
    if line in ("u", "r", "p", "q"):
        return line, ()
    verb, _, rest = line.partition(" ")
    if verb == "i":
        pos, space, text = rest.partition(" ")
        if space and (n := _number(pos)) is not None:
            return "i", (n, text)
    elif verb == "d":
        fields = rest.split(" ")
        numbers = [_number(field) for field in fields]
        if len(fields) == 2 and None not in numbers:
            return "d", tuple(numbers)
    return None


def main() -> None:
    buffer = EditorBuffer()
    while True:
        try:
            line = input()
        except EOFError:
            return
        command = _command(line)
        if command is None:
            print(HELP)
            continue
        verb, args = command
        if verb == "q":
            return
        try:
            if verb == "i":
                buffer.insert(*args)
            elif verb == "d":
                buffer.delete(*args)
            elif verb == "u":
                buffer.undo()
            elif verb == "r":
                buffer.redo()
            else:
                print(f'"{buffer.text}"')
        except ValueError as err:
            print(err)


if __name__ == "__main__":
    main()
