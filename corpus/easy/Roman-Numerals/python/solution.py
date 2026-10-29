VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


ROMAN_TABLE = (
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
)


def to_roman(n: int) -> str:
    if not 1 <= n <= 3999:
        raise ValueError(f"out of range: {n}")
    parts: list[str] = []
    for value, symbol in ROMAN_TABLE:
        count, n = divmod(n, value)
        parts.append(symbol * count)
    return "".join(parts)


def from_roman(s: str) -> int:
    total = 0
    for i, ch in enumerate(s):
        value = VALUES[ch]
        if i + 1 < len(s) and value < VALUES[s[i + 1]]:
            total -= value
        else:
            total += value
    return total


def _canonical(numeral: str) -> bool:
    """The round-trip law as a validator: render the parse, compare."""
    try:
        return to_roman(from_roman(numeral)) == numeral
    except ValueError:
        return False


def main() -> None:
    while True:
        try:
            line = input().strip().upper()
        except EOFError:
            return
        if line.isascii() and line.isdigit():
            try:
                print(to_roman(int(line)))
            except ValueError as err:
                print(f"error: {err}")
        elif not line or any(ch not in VALUES for ch in line):
            print("error: enter a number 1-3999 or a Roman numeral")
        elif _canonical(line):
            print(from_roman(line))
        else:
            print(f"error: not a canonical numeral: {line}")


if __name__ == "__main__":
    main()
