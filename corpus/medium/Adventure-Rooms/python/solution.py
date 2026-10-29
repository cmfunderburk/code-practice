from collections.abc import Callable

DIRECTIONS = ("north", "south", "east", "west")

DESCRIPTIONS = {
    "hall": "a dusty entrance hall",
    "library": "a book-lined library",
    "cellar": "a damp stone cellar",
    "attic": "a cramped attic",
    "garden": "an overgrown garden",
}

EXITS = {
    "hall": {"north": "library", "west": "garden"},
    "library": {"south": "hall", "north": "attic", "west": "cellar"},
    "cellar": {"east": "library"},
    "attic": {"south": "library"},
    "garden": {"east": "hall"},
}

START_ITEMS = {
    "hall": ["lamp"],
    "library": ["book"],
    "cellar": ["key"],
    "attic": [],
    "garden": ["rose", "spade"],
}

State = dict


def new_game() -> State:
    return {"room": "hall",
            "inventory": [],
            "items": {room: list(items) for room, items in START_ITEMS.items()},
            "over": False}


def _look(state: State) -> str:
    room = state["room"]
    exits = ", ".join(d for d in DIRECTIONS if d in EXITS[room])
    lines = [f"You are in {DESCRIPTIONS[room]}.", f"Exits: {exits}."]
    if state["items"][room]:
        lines.append("You see: " + ", ".join(state["items"][room]) + ".")
    return "\n".join(lines)


def _do_look(state: State, arg: str) -> tuple[State, str]:
    return state, _look(state)


def _do_go(state: State, arg: str) -> tuple[State, str]:
    if not arg:
        return state, "Go where?"
    if arg not in EXITS[state["room"]]:
        return state, "You can't go that way."
    state["room"] = EXITS[state["room"]][arg]
    return state, _look(state)


def _do_take(state: State, arg: str) -> tuple[State, str]:
    if not arg:
        return state, "Take what?"
    if arg not in state["items"][state["room"]]:
        return state, f"There is no {arg} here."
    state["items"][state["room"]].remove(arg)
    state["inventory"].append(arg)
    return state, "Taken."


def _do_drop(state: State, arg: str) -> tuple[State, str]:
    if not arg:
        return state, "Drop what?"
    if arg not in state["inventory"]:
        return state, f"You are not carrying {arg}."
    state["inventory"].remove(arg)
    state["items"][state["room"]].append(arg)
    return state, "Dropped."


def _do_inventory(state: State, arg: str) -> tuple[State, str]:
    if not state["inventory"]:
        return state, "You are carrying nothing."
    return state, "You are carrying: " + ", ".join(state["inventory"]) + "."


def _do_quit(state: State, arg: str) -> tuple[State, str]:
    state["over"] = True
    return state, "Goodbye."


VERBS: dict[str, Callable[[State, str], tuple[State, str]]] = {
    "look": _do_look,
    "go": _do_go,
    "take": _do_take,
    "drop": _do_drop,
    "inventory": _do_inventory,
    "quit": _do_quit,
}


def execute(state: State, line: str) -> tuple[State, str]:
    if state["over"]:
        raise ValueError("the game is over")
    verb, _, arg = line.strip().partition(" ")
    if verb not in VERBS:
        raise ValueError(f"unknown verb: {verb}")
    return VERBS[verb](state, arg.strip())


def main() -> None:
    state = new_game()
    print(_look(state))
    while not state["over"]:
        try:
            line = input()
        except EOFError:
            return
        try:
            state, output = execute(state, line)
        except ValueError as err:
            print(err)
        else:
            print(output)


if __name__ == "__main__":
    main()
