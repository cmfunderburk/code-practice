# Tic-Tac-Toe

Two players play Tic-Tac-Toe at one terminal, on stdin and stdout, one move per
line. The cells are numbered 0 to 8, row by row. `X` moves first and the turns
alternate; three in a row, column, or diagonal wins, and a full board with no
winner is a draw.

Playing:
- Before each move show the board and whose turn it is.
- A move is a cell number. Answer a line that is not a number, a number off the
  board, and a cell already marked; none costs the player the turn.
- When the game ends, show the final board, then a last line containing
  `X wins`, `O wins`, or `draw`, and stop. If input ends first, stop.

The game is the program's `SPEC.md`. Wording and the board's picture are yours;
only the cell numbers and the outcome line are fixed.

## A session

```text
. . .
. . .
. . .
X to move
> 4
. . .
. X .
. . .
O to move
> 4
illegal move: 4
. . .
. X .
. . .
O to move
> x
a cell 0-8, please
. . .
. X .
. . .
O to move
```

(`> ` marks the players' lines.)

## Rust contract

A whole program, `fn main()`, with this core above it:

```rust
#[derive(Clone, Copy, PartialEq)]
enum Mark { X, O }

type Board = [Option<Mark>; 9];

const LINES: [[usize; 3]; 8];

fn to_move(board: Board) -> Mark
fn winner(board: Board) -> Option<Mark>
fn is_draw(board: Board) -> bool
fn play(board: Board, pos: usize) -> Result<Board, String>
fn render(board: Board) -> String // three rows, no trailing newline
```

`play` returns the next board, or `Err` for a cell off the board, a marked cell,
or a decided game.

Differences from the Python version:
- A cell is `Option<Mark>`, not a string, and `winner` returns `Option<Mark>`.
- No `legal_moves`: `play` checks the same conditions directly.
- `play` returns `Result`, not a `ValueError`.
