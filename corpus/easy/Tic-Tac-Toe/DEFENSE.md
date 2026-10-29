# Tic-Tac-Toe — oral defense

Seven questions for rehearsing this program's design aloud. Read them with the callouts
closed, answer, then open a callout to check. Each answer leads with the decisive point
and cites where this directory settles it: `SPEC.md`, `python/notes.md`, or the
code. The last compares the C and Rust ports; attach their `solution` files to the
committee prompt for it.

> [!note]- Committee prompt
> Paste into an LLM session, with `SPEC.md`, `python/solution.py`, and
> `python/notes.md` attached:
>
> *You are examining a candidate on a small Tic-Tac-Toe program, specified in SPEC.md
> and implemented in solution.py. Ask the questions from DEFENSE.md one at a time, in
> order. After each answer, press on anything vague: demand the specific structure,
> failure mode, or line of SPEC. Don't accept "it's cleaner" without the mechanism.
> Keep a list of claims that contradict SPEC.md or the code, and read it back at the
> end. Don't reveal the answer callouts unless the candidate concedes.*

## Lifecycle

### 1. Trace `4`, `4`, `x`, `0`, then end of input, from stdin to the last line

Name each function the input passes through, which ones are pure, and what the shell
holds between turns.

> [!answer]-
> 1. `main` starts from `EMPTY_BOARD`. `winner` and `is_draw` say the game is
>    undecided, so it prints `_render(board)` and `X to move` (`to_move` counts the
>    marks).
> 2. `input()` reads one line without its `\n`. `int` turns `4` into 4, and `play`
>    returns a **new** tuple with `X` at 4, which the shell rebinds to `board`.
> 3. The second `4` reads as a number too, but `play` finds 4 missing from
>    `legal_moves` and raises `illegal move: 4`. The shell prints it and doesn't
>    rebind, so the board and the mover are unchanged.
> 4. `int("x")` raises `ValueError`, so the shell prints `a cell 0-8, please` and
>    `play` is never called. `0` puts `O` at 0.
> 5. At end of input `input()` raises `EOFError`, and the shell prints
>    `game abandoned` and returns.
>
> Between turns the shell holds one value, `board`. Every function except `main` is
> pure, including `_render`. (`python/solution.py`; SPEC §3.)

## Trade-offs

### 2. Why derive the mover and the winner instead of storing them, as a game object would?

> [!answer]-
> A stored mover or winner is a second copy of a fact the board already determines,
> so it can disagree with the board. A game object that keeps `_to_move` and
> `_winner` has a `play` that must mark the cell, then check the lines, then toggle
> the mover, in that order. Toggle first and the wrong mark lands; check first and
> the winning move is missed. Here `to_move` compares the X and O counts and
> `winner` scans the eight lines on every call, so there is no order to get wrong.
> The cost is recomputing over nine cells, which is nothing.
> (`python/notes.md` §Shapes chosen and rejected.)

### 3. What does threading the board as a value cost the shell, and what does it buy?

> [!answer]-
> **The cost:** the shell must write `board = play(board, pos)`. Call `play` without
> rebinding and the move is computed and thrown away: the same board prints again
> and the same player is asked to move, until input runs out. A game object
> can't make that mistake, since `game.play` changes the game in place; it trades it
> for the ordering obligation in question 2.
>
> **The gain:** a board is a plain tuple. Any position can be written directly,
> positions compare with `==`, and `play` leaves its input alone. Keeping an earlier
> board, for an undo or a game tree, needs no copying. (`python/solution.py`;
> `python/notes.md`, *The drilled composition root*.)

### 4. The shell reads a move with `int()`. Who rejects `9`, and why doesn't the shell check the range?

> [!answer]-
> **The core does, because the range is a rule.** `play` accepts only a position in
> `legal_moves`, which lists the empty cells of an undecided board, so `9`, `-1`,
> and an occupied cell all raise `illegal move: <cell>`. If the shell also checked
> 0–8, the two checks could drift apart; here the shell's one job is turning a line
> into a number, and `int()` failing is its one message, `a cell 0-8, please`.
>
> **`int()` is generous, and that is a choice, not a bug.** It strips whitespace and
> reads `+4` and non-ASCII digits such as `٤` as 4. SPEC could call those invalid
> so Python, C, and Rust print the same bytes, but it leaves spacing and signs to
> each implementation; the cell numbers themselves stay fixed, so one line of
> moves plays the same game everywhere. (`python/notes.md` §Shapes chosen and
> rejected; SPEC §2.)

## Adversarial

### 5. The ninth move completes a line. What does the program print, and what would print `draw` instead?

> [!answer]-
> It prints the full board and `X wins!`. For example, `0 1 2 3 4 5 7 6 8` ends with
> X on the 0–4–8 diagonal and no empty cell. `is_draw` is
> `winner(board) is None and "" not in board`, so a full board with a line is not a
> draw, and SPEC §1 defines a draw as a full board **with no winner**.
>
> A shell that decides the result by fullness, such as
> `"draw" if "" not in board else ...`, or an `is_draw` that drops the winner test,
> prints `draw` for this game.
>
> Two winners at once can't happen. `legal_moves` returns `()` once a line exists,
> so `play` refuses every later move. (`python/solution.py`.)

## Scale

### 6. What larger program has this program's shape, and where does that shape pay off there?

> [!answer]-
> **A text editor.** Run headless from a key script, it needs a pure step,
> (state, key) → state, and a pure render, state → frame string, with the terminal
> I/O in the shell. Here `play` is the step and `_render` the render. An editor adds
> undo and redo, and that is where a value core pays off: each step leaves the
> earlier state intact. This program keeps only the current board, so it never has
> to decide which states to keep. An editor's undo stack does. (`python/notes.md`
> §Scales up to.)

## Across languages

### 7. Python threads an immutable tuple through `main`. How do the C and Rust ports make the board a value, and how does each read a move?

> [!answer]-
> **All three thread a value, and only Python allocates to do it.**
> - **Python** uses a tuple of nine strings, `""` for empty. `play` slices a new
>   tuple, and `main` rebinds `board = play(board, pos)`. A move is `int(line)`, and
>   `play` rejects any number that isn't an empty cell.
> - **C** can't pass or return a bare array by value, so `Board` wraps
>   `char cells[9]` in a struct. Every predicate takes a 9-byte copy, and
>   `play(Board, int, Board *next)` writes the next board through a pointer, as
>   C Hangman's `guess` does. An empty cell is `'\0'`, so `Board board = {}` is
>   the empty board. A move is `fgets` plus `strtol`, whose end pointer catches
>   trailing junk; `cell_of` also rejects numbers outside 0–8 before narrowing a
>   `long` to an `int`, so `9` gets the format message, not `illegal move`.
> - **Rust** uses `[Option<Mark>; 9]`, nine bytes and `Copy`. `play(mut board,
>   pos)` marks its own copy and returns it in `Ok`. The `Mark` enum means a cell
>   can hold only `X`, `O`, or nothing, where Python's string cell could hold
>   anything. A move is `line.trim().parse::<usize>()`; as in Python, any number
>   reaches `play`, but `-1` fails to parse, since `usize` has no sign.
>
> Neither port needs `legal_moves`: `play` checks the same conditions directly.
> SPEC fixes only the outcome line and that every line is answered, so their
> wording may differ. (`c/notes.md` and `rust/notes.md`.)
