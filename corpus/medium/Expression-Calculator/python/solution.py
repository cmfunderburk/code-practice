Node = tuple  # ("num", value) | ("neg", node) | (op, left, right), op in + - * /


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in " \t":
            i += 1
        elif ch in "0123456789":
            j = i
            while j < len(text) and text[j] in "0123456789":
                j += 1
            tokens.append(text[i:j])
            i = j
        elif ch in "+-*/()":
            tokens.append(ch)
            i += 1
        else:
            raise ValueError(f"unknown character: {ch}")
    return tokens


def parse(tokens: list[str]) -> Node:
    node, pos = _expr(tokens, 0)
    if pos != len(tokens):
        raise ValueError(f"trailing input: {tokens[pos]}")
    return node


def _expr(tokens: list[str], pos: int) -> tuple[Node, int]:
    node, pos = _term(tokens, pos)
    while pos < len(tokens) and tokens[pos] in "+-":
        op = tokens[pos]
        right, pos = _term(tokens, pos + 1)
        node = (op, node, right)
    return node, pos


def _term(tokens: list[str], pos: int) -> tuple[Node, int]:
    node, pos = _factor(tokens, pos)
    while pos < len(tokens) and tokens[pos] in "*/":
        op = tokens[pos]
        right, pos = _factor(tokens, pos + 1)
        node = (op, node, right)
    return node, pos


def _factor(tokens: list[str], pos: int) -> tuple[Node, int]:
    if pos == len(tokens):
        raise ValueError("unexpected end of input")
    token = tokens[pos]
    if token == "-":
        node, pos = _factor(tokens, pos + 1)
        return ("neg", node), pos
    if token == "(":
        node, pos = _expr(tokens, pos + 1)
        if pos == len(tokens) or tokens[pos] != ")":
            raise ValueError("expected )")
        return node, pos + 1
    if token.isdigit():
        return ("num", int(token)), pos + 1
    raise ValueError(f"unexpected token: {token}")


def evaluate(node: Node) -> int | float:
    match node:
        case ("num", value):
            return value
        case ("neg", operand):
            return -evaluate(operand)
        case ("+", left, right):
            return evaluate(left) + evaluate(right)
        case ("-", left, right):
            return evaluate(left) - evaluate(right)
        case ("*", left, right):
            return evaluate(left) * evaluate(right)
        case ("/", left, right):
            return evaluate(left) / evaluate(right)
    raise ValueError(f"bad node: {node!r}")


def calculate(text: str) -> int | float:
    return evaluate(parse(tokenize(text)))


def main() -> None:
    while True:
        try:
            line = input()
        except EOFError:
            return
        if not line:
            return
        try:
            print(calculate(line))
        except (ValueError, ZeroDivisionError) as err:
            print(f"error: {err}")


if __name__ == "__main__":
    main()
