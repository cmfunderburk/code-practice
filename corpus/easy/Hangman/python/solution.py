import random
import string
from dataclasses import dataclass

WORDS = ("banana", "jigsaw", "kayak", "oxygen", "puzzle", "python", "rhythm", "wizard")


@dataclass(frozen=True)
class HangmanState:
    secret: str
    guessed: frozenset[str]
    max_wrong: int


def new_game(secret: str, max_wrong: int = 6) -> HangmanState:
    return HangmanState(secret, frozenset(), max_wrong)


def wrong_count(state: HangmanState) -> int:
    return len(state.guessed - set(state.secret))


def masked(state: HangmanState) -> str:
    return "".join(ch if ch in state.guessed else "_" for ch in state.secret)


def status(state: HangmanState) -> str:
    if set(state.secret) <= state.guessed:
        return "won"
    if wrong_count(state) >= state.max_wrong:
        return "lost"
    return "playing"


def guess(state: HangmanState, letter: str) -> HangmanState:
    if status(state) != "playing":
        raise ValueError(f"game is over: {status(state)}")
    if letter in state.guessed:
        raise ValueError(f"already guessed: {letter}")
    return HangmanState(state.secret, state.guessed | {letter}, state.max_wrong)


def main() -> None:
    state = new_game(random.choice(WORDS))
    while status(state) == "playing":
        print(f"{masked(state)}  wrong: {wrong_count(state)}/{state.max_wrong}")
        try:
            letter = input().strip().lower()
        except EOFError:
            print(f"you quit! the word was {state.secret}")
            return
        if len(letter) != 1 or letter not in string.ascii_lowercase:
            print("one letter a-z, please")
            continue
        try:
            state = guess(state, letter)
        except ValueError as err:
            print(err)
    print(f"you {status(state)}! the word was {state.secret}")


if __name__ == "__main__":
    main()
