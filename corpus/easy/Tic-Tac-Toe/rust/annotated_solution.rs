//! Tic-Tac-Toe: whole program.

// From Python:
// 1. Python's board is a tuple of nine strings. Here it is `[Option<Mark>; 9]`:
//    a cell can only be `X`, `O`, or empty, and an empty cell is `None` rather
//    than `""` (Rust Book 6.1). [types]
// 2. The board is nine bytes and `Copy`, so every function takes it by value.
//    `play` marks its own copy and returns it, and the caller's board can't
//    change, as Python's tuple can't (Rust Book 4.1, "Stack-Only Data: Copy").
//    [mutation]
// 3. Python raises `ValueError` for an illegal move. `play` returns
//    `Result<Board, String>`, and `main` matches on it (Rust Book 9.2). [errors]
// 4. Python's `main` reads a move with `int(line)`. Here it is
//    `line.trim().parse::<usize>()`, which returns `Err` for anything but
//    digits (an optional `+` aside), and `play` rejects a number off the
//    board, as Python's `play` does (Rust Book 2, "Comparing the Guess"). [parsing]
// 5. Python's `input()` raises `EOFError` at end of input. `stdin().lines()`
//    yields `None` there, and `Err` for a line that isn't UTF-8; `main` stops
//    on either. [io]

use std::io;

// `Copy` makes a `Mark`, and so the whole board, copy on assignment; `PartialEq`
// allows `==` (Rust Book Appendix C).
#[derive(Clone, Copy, PartialEq)]
enum Mark {
    X,
    O,
}

// A type alias: `Board` is just a name for the array type (Rust Book 20.3).
type Board = [Option<Mark>; 9];

const LINES: [[usize; 3]; 8] = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
];

impl Mark {
    fn symbol(self) -> char {
        match self {
            Mark::X => 'X',
            Mark::O => 'O',
        }
    }
}

// Python's `to_move`: the mover is derived from the counts, stored nowhere.
fn to_move(board: Board) -> Mark {
    // A closure that captures `board` (Rust Book 13.1). The pattern `&&cell`
    // unwraps the two references `filter` passes (Rust Book 19.1).
    let count = |mark| board.iter().filter(|&&cell| cell == Some(mark)).count();
    if count(Mark::X) == count(Mark::O) {
        Mark::X
    } else {
        Mark::O
    }
}

fn winner(board: Board) -> Option<Mark> {
    // `find_map` returns the first `Some` the closure gives, like Python's loop
    // with an early `return`. The match guard after `if` checks the other two
    // cells (Rust Book 19.3).
    LINES.iter().find_map(|&[a, b, c]| match board[a] {
        Some(mark) if board[b] == Some(mark) && board[c] == Some(mark) => Some(mark),
        _ => None,
    })
}

fn is_draw(board: Board) -> bool {
    winner(board).is_none() && board.iter().all(Option::is_some)
}

// `mut board` makes the parameter, a copy of the caller's board, changeable.
// `get` returns `None` past the end, so an out-of-range `pos` is illegal too.
fn play(mut board: Board, pos: usize) -> Result<Board, String> {
    if winner(board).is_some() || board.get(pos) != Some(&None) {
        return Err(format!("illegal move: {pos}"));
    }
    board[pos] = Some(to_move(board));
    Ok(board)
}

fn render(board: Board) -> String {
    let rows: Vec<String> = board
        // `chunks(3)` yields the three rows as slices, Python's `board[i:i + 3]`.
        .chunks(3)
        .map(|row| {
            let cells: Vec<String> = row
                .iter()
                // An empty cell renders as `.`, a marked one as its letter.
                .map(|cell| cell.map_or('.', Mark::symbol).to_string())
                .collect();
            cells.join(" ")
        })
        .collect();
    rows.join("\n")
}

fn main() {
    // Each item is `io::Result<String>`, without the newline.
    let mut lines = io::stdin().lines();
    let mut board: Board = [None; 9];
    while winner(board).is_none() && !is_draw(board) {
        println!("{}", render(board));
        println!("{} to move", to_move(board).symbol());
        // `let…else` handles the end first: no line, or one that isn't UTF-8
        // (Rust Book 6.3).
        let Some(Ok(line)) = lines.next() else {
            println!("game abandoned");
            return;
        };
        // The turbofish `::<usize>` names the type to parse into. A negative
        // number fails here, since `usize` has none.
        let Ok(pos) = line.trim().parse::<usize>() else {
            println!("a cell 0-8, please");
            continue;
        };
        match play(board, pos) {
            // Python's `board = play(board, pos)`.
            Ok(next) => board = next,
            Err(message) => println!("{message}"),
        }
    }
    println!("{}", render(board));
    match winner(board) {
        Some(mark) => println!("{} wins!", mark.symbol()),
        None => println!("draw"),
    }
}
