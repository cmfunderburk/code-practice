# Tic-Tac-Toe — oral defense

Seven questions about the design of the Tic-Tac-Toe program, for practising
explaining it aloud. Answer each question with its answer closed, then open the
answer to check yourself. Each answer starts with the main point and names the file
that settles it: `SPEC.md`, `python/solution.py`, `python/notes.md`, or a test
file.

Question 7 compares the Python version with the C and Rust versions, which are in
`c/` and `rust/`.

> [!note]- Examiner prompt
> Paste this into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached (for question 7, attach the C and Rust
> `solution` files too):
>
> *You are examining a student on a small Tic-Tac-Toe program, specified in SPEC.md
> and implemented in solution.py. Ask the questions from DEFENSE.md one at a time,
> in order. After each answer, ask follow-up questions about anything vague: ask
> for the specific function, input, or line of SPEC. Don't accept "it's cleaner"
> without the reason. Keep a list of claims that contradict SPEC.md or the code,
> and read it back at the end. Don't show the answers unless the student gives up.*

## Following a game through the program

### 1. Trace four moves and the end of input

The players type these four lines, one after another: `4`, `4`, `x`, and `0`. Then
input ends. For each line, say which functions handle it and what the program
prints. Then say which functions read input or print anything, and what `main`
keeps from one turn to the next.

> [!answer]-
> **`main` keeps one value between turns, the board; every other function only
> computes a result from its arguments.**
> 1. `main` starts with `board = EMPTY_BOARD`. `winner` and `is_draw` say the game
>    is not over, so `main` prints `_render(board)` and `X to move` (`to_move`
>    counts the marks, and there are as many `X`s as `O`s).
> 2. `input()` returns `4` without its `\n`. `int` gives 4, and `play` returns a
>    **new** tuple with `X` in cell 4, which `main` stores with
>    `board = play(board, pos)`. `main` prints the new board and `O to move`.
> 3. The second `4` is also a number, but 4 is no longer in `legal_moves`, so
>    `play` raises `ValueError("illegal move: 4")`. `main` prints the message and
>    does not assign to `board`, so the same board and `O to move` print again.
> 4. `int("x")` raises `ValueError`, so `main` prints `a cell 0-8, please` and
>    starts the next turn without calling `play`. `0` puts `O` in cell 0, and
>    `main` prints that board and `X to move`.
> 5. At end of input, `input()` raises `EOFError`. `main` prints `game abandoned`
>    and returns.
>
> Only `main` calls `input()` and `print()`. `_render` returns the board's
> picture as a string, and `main` prints it. (`python/solution.py`;
> SPEC §3.)

## Design choices

### 2. Storing whose turn it is, or working it out

`to_move` works out whose turn it is by counting the marks on the board, and
`winner` checks all eight lines every time it is called. Nothing but the board
is stored.

Another design keeps the game in an object:

```python
class Game:
    def __init__(self) -> None:
        self.board = [""] * 9
        self.to_move = "X"
        self.winner: str | None = None
```

Here `play(self, pos)` has three updates to make: put `self.to_move`'s mark in
the cell, check the lines and set `self.winner`, and switch `self.to_move` to the
other player. Its other methods, such as `legal_moves` and `is_draw`, read
`self.winner` instead of checking the lines again. In what order must `play`
make the three updates? Say what goes wrong in each of
the two other orders you would most likely write by mistake. Then say why the
program's own `play` has no such order to get right.

> [!answer]-
> **A stored turn or winner is a second copy of what the board already says, and
> every update must keep the copies in step.** The `Game` class must mark the
> cell, then check the lines, then switch the player.
> - **Switch the player first:** the cell gets the next player's mark. X's first
>   move puts an `O` on the board.
> - **Check the lines before marking:** the move that completes a line isn't seen.
>   The other player is then allowed to move on a board that has already been won,
>   and the win is noticed only after that move. If the winning move fills the
>   board, the game ends as a draw.
>
> The program's `play` stores nothing but the cells. `to_move` counts the marks
> and `winner` scans the lines whenever they are called, so they always agree with
> the board. Working them out again costs a pass over nine cells and eight lines.
> (`python/solution.py`; `python/notes.md` §Design choices.)

### 3. Returning a new board

`play` doesn't change the board it is given. It returns a new tuple with one more
mark, and `main` keeps the new board with `board = play(board, pos)`.

Suppose `main` wrote `play(board, pos)` on its own line instead. What would the
program print if the players typed `4` and then `0`, and input ended? Then name
two things that are easier because `play` returns a new board instead of changing
the old one.

> [!answer]-
> **The move would be computed and thrown away.** `play` would return a board with
> `X` in cell 4, and `main` would never use it. The empty board and `X to move`
> would print after each line, with no error message, and then `game abandoned`.
> No move would ever take effect. `test_main_threads_each_returned_board` catches
> this: it checks that the board the next turn draws is the one `play` returned.
>
> What returning a new board makes easier:
> - **Testing.** A board is a plain tuple, so a test can write any position
>   directly (the tests' `_board` helper), compare two positions with `==`, and
>   check that `play` left its input unchanged
>   (`test_play_leaves_the_old_board_alone`).
> - **Keeping earlier positions.** An undo command, or a program that searches
>   ahead through possible moves, can keep old boards without copying them,
>   because nothing will change them.
>
> A `play` that changed the board in place would return nothing, so there would be
> no result for `main` to forget. But it would bring back the ordering problem
> from question 2 whenever the game stored anything besides the cells.
> (`python/solution.py`; `python/test_solution.py`.)

### 4. Who checks that a cell is on the board

`main` turns each line into a number with `int()` and passes any number it gets
to `play`. It never checks that the number is between 0 and 8.

What does the Python version print for each of these lines on an empty board:
`9`, `-1`, `x`, `4.5`, and ` 4 ` (with spaces)? Which function produces each
answer? Then explain why `main` doesn't check the range 0 to 8 itself.

> [!answer]-
> **`play` checks every rule about cells, so `main` only has to turn a line into a
> number.**
> - `9` and `-1`: `int` reads them, and `play` finds neither in `legal_moves`, so
>   it raises and `main` prints `illegal move: 9` and `illegal move: -1`.
> - `x` and `4.5`: `int` raises `ValueError`, so `main` prints
>   `a cell 0-8, please`.
> - ` 4 `: `int` ignores the spaces and reads 4, so `X` takes cell 4.
>
> `legal_moves` lists the empty cells of a game that nobody has won. A number off
> the board, an occupied cell, and any move after a win are all missing from that
> list, so `play` refuses all three with one test. If `main` also checked 0 to 8,
> the rule "a move must name a cell" would be written in two places, and a change
> to one would have to be copied to the other.
>
> `int` is generous: it also reads `+4`, and digits from other scripts such as
> Arabic-Indic `٤`, as 4. SPEC §2 lets each version decide how to read such lines.
> Each of them still either names a cell or is refused by `play`, so none can put a
> mark where the rules don't allow it. (`python/solution.py`;
> `test_main_answers_bad_lines_and_play_refuses_bad_cells` in
> `python/test_solution.py`; SPEC §2.)

## Unusual input

### 5. A win on the ninth move

SPEC §1 defines a draw as a full board **with no winner**. The players type
`0 1 2 3 4 5 7 6 8`, one move per line. The ninth move, `X` in cell 8, fills the
board and completes the diagonal 0, 4, 8 at the same time.

What does the program print last? Then consider two changes, each made on its
own:

1. `main`'s last line becomes
   `print("draw" if "" not in board else f"{winner(board)} wins!")`.
2. `is_draw` becomes `return "" not in board`, without the winner test.

What does the program print last after each change, and why?

> [!answer]-
> **It prints the full board and `X wins!`.** The loop stops because `winner`
> finds the diagonal. `main`'s last line asks `winner` first, and `is_draw` is
> `winner(board) is None and "" not in board`, so this board is not a draw.
>
> 1. This version prints `draw`. It decides the result by whether the board is
>    full, before asking whether anyone won. The shared test
>    `test_a_win_on_the_ninth_move_is_a_win_not_a_draw` catches it.
> 2. This version still prints `X wins!`. `main` calls `is_draw` only after
>    `winner` has said nobody won, and when nobody has won, the two versions of
>    `is_draw` agree. The change would matter to any other code that asked
>    `is_draw` about a won board, such as a `main` whose last line asked `is_draw`
>    before `winner`: that one prints `draw`. No Python test asks `is_draw` about a
>    won board; the C and Rust tests do.
>
> The two players can never both have a line: once someone has won,
> `legal_moves` returns `()`, so `play` refuses every later move.
> (`python/solution.py`; `test_program.py`.)

## Beyond this program

### 6. A step function and a render function in a larger program

In this program, `play` is a *step function*: it takes the current state (the
board) and one input (a move), and returns the next state. `_render` turns a state
into text. Neither reads input or prints; `main` does all of that.

Consider a text editor that must be testable without a terminal: a test gives it
a file and a script of keystrokes, and checks the final file and the final
screen. Describe the editor's core in the same terms as `play` and `_render`.
Then explain why undo and redo are easier to write when each step returns a new
state, and what an editor has to decide about earlier states that this program
never does.

> [!answer]-
> **The editor's core is a step function, (state, key) → state, and a render
> function, state → screen text, with all terminal input and output in its `main`
> loop.** A test can then run the script by calling the step function once per
> key, and compare the rendered text with the expected screen, without a
> terminal. Here `play` is the step and `_render` the render, and the tests feed
> `main` a string of moves in place of a person typing.
>
> When each step returns a new state and leaves the old one unchanged, undo can
> keep a list of earlier states and go back to the previous one. Nothing has to be
> reversed by hand. This program keeps only the current board, so it never has to
> decide which states to keep. An editor does: keeping a whole copy of a large file
> after every keystroke uses a lot of memory, so editors often keep a list of the
> edits made and how to reverse each one instead. (`python/notes.md`
> §Where this shows up again.)

## Across languages

### 7. How the Python, C, and Rust versions pass the board and read a move

In all three versions, `play` takes a board and gives back the next board without
changing the caller's board. For each version, say what type the board has, how
`play` returns the next board, and how a line becomes a move. Then find a line
that two versions answer differently.

> [!answer]-
> **All three pass the board by value; they differ in the board's type and in how
> much of a line each accepts as a move.**
> - **Python** uses a tuple of nine strings, `""` for an empty cell. `play` builds
>   a new tuple by slicing, and `main` keeps it with `board = play(board, pos)`. A
>   move is `int(line)`, and `play` refuses any number that isn't an empty cell.
> - **C** can't pass or return a bare array by value, so `Board` is a struct
>   holding `char cells[9]`. Every function that takes a board gets its own
>   9-byte copy, and `play(Board, int, Board *next)` writes the next board
>   through the pointer and returns `false` for an illegal move. An empty cell
>   is `'\0'`, so `Board board = {}` is the empty board. A move is read with
>   `fgets` and `strtol`: `cell_of` accepts spaces before the number and a sign,
>   but nothing after the number, and it refuses a number outside 0 to 8 before
>   `play` sees it.
> - **Rust** uses `[Option<Mark>; 9]`, where `Mark` is an enum of `X` and `O`, so a
>   cell can hold only `X`, `O`, or nothing. The array is `Copy`, so
>   `play(mut board, pos)` marks its own copy and returns it in `Ok`. A move is
>   `line.trim().parse::<usize>()`: spaces around the number are fine, and a
>   number off the board reaches `play`, which refuses it.
>
> Neither the C nor the Rust version has `legal_moves`; each `play` tests the same
> conditions directly. Examples where they differ: `9` is `illegal move: 9` in
> Python and Rust but `a cell 0-8, please` in C. `-1` is `illegal move: -1` in
> Python, but `a cell 0-8, please` in Rust (a `usize` has no sign) and in C. `4 `
> (with a trailing space) takes cell 4 in Python and Rust, but C refuses it.
> Only the outcome line is fixed by SPEC §4, so all of these are allowed.
> (`notes.md` and `solution.*` in `c/` and `rust/`.)
