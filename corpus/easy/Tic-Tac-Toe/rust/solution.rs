//! Tic-Tac-Toe: whole program.

use std::io;

#[derive(Clone, Copy, PartialEq)]
enum Mark {
    X,
    O,
}

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

fn to_move(board: Board) -> Mark {
    let count = |mark| board.iter().filter(|&&cell| cell == Some(mark)).count();
    if count(Mark::X) == count(Mark::O) {
        Mark::X
    } else {
        Mark::O
    }
}

fn winner(board: Board) -> Option<Mark> {
    LINES.iter().find_map(|&[a, b, c]| match board[a] {
        Some(mark) if board[b] == Some(mark) && board[c] == Some(mark) => Some(mark),
        _ => None,
    })
}

fn is_draw(board: Board) -> bool {
    winner(board).is_none() && board.iter().all(Option::is_some)
}

fn play(mut board: Board, pos: usize) -> Result<Board, String> {
    if winner(board).is_some() || board.get(pos) != Some(&None) {
        return Err(format!("illegal move: {pos}"));
    }
    board[pos] = Some(to_move(board));
    Ok(board)
}

fn render(board: Board) -> String {
    let rows: Vec<String> = board
        .chunks(3)
        .map(|row| {
            let cells: Vec<String> = row
                .iter()
                .map(|cell| cell.map_or('.', Mark::symbol).to_string())
                .collect();
            cells.join(" ")
        })
        .collect();
    rows.join("\n")
}

fn main() {
    let mut lines = io::stdin().lines();
    let mut board: Board = [None; 9];
    while winner(board).is_none() && !is_draw(board) {
        println!("{}", render(board));
        println!("{} to move", to_move(board).symbol());
        let Some(Ok(line)) = lines.next() else {
            println!("game abandoned");
            return;
        };
        let Ok(pos) = line.trim().parse::<usize>() else {
            println!("a cell 0-8, please");
            continue;
        };
        match play(board, pos) {
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
