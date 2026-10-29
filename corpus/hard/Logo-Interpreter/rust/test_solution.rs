use super::*;

fn run(logo: &mut Logo, line: &str) -> Result<(), String> {
    logo.execute(&tokens(line))
}

fn state(logo: &Logo) -> (i64, i64, char, bool, Vec<Segment>) {
    let Turtle {
        x,
        y,
        heading,
        pen_down,
    } = logo.turtle;
    (x, y, HEADINGS[heading], pen_down, logo.segments.clone())
}

#[test]
fn a_square_is_one_history_entry() {
    let mut logo = Logo::new();
    run(&mut logo, "REPEAT 4 [ FORWARD 2 LEFT ]").unwrap();
    let square = vec![
        ((0, 0), (2, 0)),
        ((2, 0), (2, 2)),
        ((2, 2), (0, 2)),
        ((0, 2), (0, 0)),
    ];
    assert_eq!(state(&logo), (0, 0, 'E', true, square));
    logo.undo().unwrap();
    assert_eq!(state(&logo), (0, 0, 'E', true, vec![]));
    assert!(logo.undo().is_err());
}

#[test]
fn each_top_level_command_is_one_entry() {
    let mut logo = Logo::new();
    run(&mut logo, "FORWARD 2 RIGHT FORWARD 3").unwrap();
    assert_eq!(logo.turtle.y, -3);
    logo.undo().unwrap();
    assert_eq!(state(&logo), (2, 0, 'S', true, vec![((0, 0), (2, 0))]));
    logo.undo().unwrap();
    assert_eq!(state(&logo), (2, 0, 'E', true, vec![((0, 0), (2, 0))]));
    logo.undo().unwrap();
    assert_eq!(state(&logo), (0, 0, 'E', true, vec![]));
}

#[test]
fn the_pen_up_moves_without_drawing() {
    let mut logo = Logo::new();
    run(
        &mut logo,
        "PENUP FORWARD 3 LEFT FORWARD 2 PENDOWN RIGHT FORWARD 1",
    )
    .unwrap();
    assert_eq!(state(&logo), (4, 2, 'E', true, vec![((3, 2), (4, 2))]));
    logo.undo().unwrap();
    assert_eq!(state(&logo), (3, 2, 'E', true, vec![]));
}

#[test]
fn case_brackets_and_whitespace_are_free() {
    let mut logo = Logo::new();
    run(
        &mut logo,
        "repeat 2[forward 1 left repeat 2[forward 1 right]]",
    )
    .unwrap();
    let (x, y, heading, pen_down, _) = state(&logo);
    assert_eq!((x, y, heading, pen_down), (3, -1, 'W', true));
    run(&mut logo, "\tREPEAT 3 [ ]\r").unwrap();
    assert_eq!((logo.undo.len(), logo.segments.len()), (2, 6));
}

#[test]
fn numbers_are_parse_i64() {
    let mut logo = Logo::new();
    run(&mut logo, "FORWARD +3 FORWARD 007").unwrap();
    assert_eq!(logo.turtle.x, 10);
    assert!(run(&mut logo, "FORWARD 1_0").is_err());
}

#[test]
fn a_bad_line_changes_nothing() {
    let mut logo = Logo::new();
    run(&mut logo, "FORWARD 2 LEFT").unwrap();
    for line in [
        "FORWARD",
        "FORWARD 0",
        "FORWARD -2",
        "FORWARD x",
        "FORWARD 3.0",
        "FORWARD 1 SPIN",
        "]",
        "[ LEFT ]",
        "REPEAT 2 FORWARD 1",
        "REPEAT 0 [ LEFT ]",
        "REPEAT 2 [ LEFT",
        "REPEAT 2 [ LEFT ] ]",
        "UNDO UNDO",
        "FORWARD 99999999999999999999",
    ] {
        assert!(run(&mut logo, line).is_err(), "{line}");
        assert_eq!(state(&logo), (2, 0, 'N', true, vec![((0, 0), (2, 0))]));
        assert_eq!(logo.undo.len(), 2);
    }
}

#[test]
fn an_overflowing_line_is_refused_whole() {
    let mut logo = Logo::new();
    run(&mut logo, "FORWARD 9223372036854775000").unwrap();
    let before = state(&logo);
    assert!(run(&mut logo, "FORWARD 1 LEFT REPEAT 2 [ RIGHT FORWARD 9000 ]").is_err());
    assert_eq!(state(&logo), before);
    assert_eq!(logo.undo.len(), 1);
    run(&mut logo, "LEFT LEFT FORWARD 9223372036854775000").unwrap();
    assert_eq!((logo.turtle.x, logo.segments.len()), (0, 2));
}
