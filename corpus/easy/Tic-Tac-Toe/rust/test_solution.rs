use super::*;

fn played(moves: &[usize]) -> Board {
    moves.iter().fold([None; 9], |board, &pos| {
        play(board, pos).expect("a legal move")
    })
}

#[test]
fn x_moves_first_and_the_turns_alternate() {
    let board: Board = [None; 9];
    assert!(to_move(board) == Mark::X);
    let board = played(&[4]);
    assert!(board[4] == Some(Mark::X) && to_move(board) == Mark::O);
}

#[test]
fn every_line_wins() {
    for line in LINES {
        let mut board: Board = [None; 9];
        for pos in line {
            board[pos] = Some(Mark::O);
        }
        assert!(winner(board) == Some(Mark::O), "{line:?}");
        assert!(!is_draw(board));
    }
}

#[test]
fn games_end_with_a_win_or_a_draw() {
    assert!(winner(played(&[0, 3, 1, 4, 2])) == Some(Mark::X));
    assert!(winner(played(&[0, 2, 1, 4, 8, 6])) == Some(Mark::O));
    let draw = played(&[0, 1, 2, 4, 3, 5, 7, 6, 8]);
    assert!(is_draw(draw) && winner(draw).is_none());
    // The ninth move fills the board and the 0-4-8 diagonal at once.
    let ninth = played(&[0, 1, 2, 3, 4, 5, 7, 6, 8]);
    assert!(winner(ninth) == Some(Mark::X) && !is_draw(ninth));
}

#[test]
fn illegal_moves_are_refused() {
    let board = played(&[4]);
    assert_eq!(play(board, 4).err().as_deref(), Some("illegal move: 4"));
    assert_eq!(play(board, 9).err().as_deref(), Some("illegal move: 9"));
    assert!(play(played(&[0, 3, 1, 4, 2]), 8).is_err());
}

#[test]
fn playing_leaves_the_old_board_alone() {
    let before = played(&[4]);
    let after = play(before, 0).expect("a legal move");
    assert!(before[0].is_none() && after[0] == Some(Mark::O));
}

#[test]
fn render_draws_three_rows() {
    assert_eq!(render(played(&[0, 4])), "X . .\n. O .\n. . .");
}
