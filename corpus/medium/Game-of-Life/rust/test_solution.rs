use super::*;

fn cells(rows: &[&str]) -> HashSet<Cell> {
    let mut live = HashSet::new();
    for (r, row) in rows.iter().enumerate() {
        for (c, ch) in row.chars().enumerate() {
            if ch == '#' {
                live.insert((r, c));
            }
        }
    }
    live
}

fn after(rows: &[&str], generations: usize) -> HashSet<Cell> {
    let mut live = cells(rows);
    for _ in 0..generations {
        live = step(&live, rows.len(), rows[0].len());
    }
    live
}

#[test]
fn blinker_oscillates_and_block_is_still() {
    let blinker = [".....", ".....", ".###.", ".....", "....."];
    let turned = [".....", "..#..", "..#..", "..#..", "....."];
    assert_eq!(after(&blinker, 1), cells(&turned));
    assert_eq!(after(&blinker, 2), cells(&blinker));
    let block = ["....", ".##.", ".##.", "...."];
    assert_eq!(after(&block, 1), cells(&block));
}

#[test]
fn cells_past_the_edge_are_dead() {
    assert_eq!(
        after(&["###", "...", "..."], 1),
        cells(&[".#.", ".#.", "..."])
    );
    assert_eq!(
        after(&["..#", "..#", "..#"], 1),
        cells(&["...", ".##", "..."])
    );
    assert!(after(&["#"], 1).is_empty());
}

#[test]
fn glider_moves_one_cell_diagonally_every_four_generations() {
    let glider = [".#...", "..#..", "###..", ".....", "....."];
    let moved = [".....", "..#..", "...#.", ".###.", "....."];
    assert_eq!(after(&glider, 4), cells(&moved));
}

#[test]
fn step_leaves_its_input_alone() {
    let live = cells(&["###"]);
    step(&live, 1, 3);
    assert_eq!(live, cells(&["###"]));
}

#[test]
fn parse_input_reads_the_pattern() {
    let world = parse_input("2  3 +0\r\n#.#\r\n.#.").unwrap();
    assert_eq!((world.rows, world.cols, world.generations), (2, 3, 0));
    assert_eq!(world.live, cells(&["#.#", ".#."]));
}

#[test]
fn parse_input_refuses_bad_patterns() {
    for text in [
        "",
        "\n",
        "3 3\n...\n...\n...\n",
        "3 3 1 1\n...\n...\n...\n",
        "3 x 1\n...\n...\n...\n",
        "3 3 -1\n...\n...\n...\n",
        "0 3 1\n",
        "1 1 1001\n.\n",
        "99999999999999999999999 1 1\n.\n",
        "3 3 1\n...\n..\n...\n",
        "3 3 1\n...\n.x.\n...\n",
        "3 3 1\n...\n...\n",
        "3 3 1\n...\n...\n...\n...\n",
        "3 3 1\n...\n...\n...\n\n",
    ] {
        assert!(parse_input(text).is_err(), "{text:?}");
    }
}
