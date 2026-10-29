use super::*;

fn text(buffer: &EditorBuffer) -> String {
    buffer.text.iter().collect()
}

#[test]
fn a_scripted_replay() {
    let mut buffer = EditorBuffer::default();
    buffer.insert(0, "hello").unwrap();
    buffer.insert(5, " world").unwrap();
    buffer.delete(0, 6).unwrap();
    assert_eq!(text(&buffer), "world");
    buffer.undo().unwrap();
    assert_eq!(text(&buffer), "hello world");
    buffer.undo().unwrap();
    assert_eq!(text(&buffer), "hello");
    buffer.redo().unwrap();
    assert_eq!(text(&buffer), "hello world");
    buffer.insert(0, "big ").unwrap();
    assert_eq!(text(&buffer), "big hello world");
    assert_eq!(buffer.redo(), Err("nothing to redo".to_string()));
}

#[test]
fn bounds_and_refusals_change_nothing() {
    let mut buffer = EditorBuffer::default();
    buffer.insert(0, "ab").unwrap();
    buffer.undo().unwrap();
    assert!(buffer.insert(5, "x").is_err());
    assert!(buffer.delete(0, 5).is_err());
    assert!(buffer.delete(0, 0).is_err());
    assert!(buffer.delete(usize::MAX, usize::MAX).is_err());
    buffer.redo().unwrap();
    assert_eq!(text(&buffer), "ab");
    buffer.insert(2, "c").unwrap();
    buffer.delete(0, 3).unwrap();
    assert_eq!(text(&buffer), "");
    buffer.undo().unwrap();
    buffer.undo().unwrap();
    buffer.undo().unwrap();
    assert_eq!(buffer.undo(), Err("nothing to undo".to_string()));
}

#[test]
fn positions_count_characters() {
    let mut buffer = EditorBuffer::default();
    buffer.insert(0, "héllo").unwrap();
    buffer.insert(2, "\u{1f600}").unwrap();
    buffer.delete(1, 1).unwrap();
    assert_eq!(text(&buffer), "h\u{1f600}llo");
    buffer.undo().unwrap();
    assert_eq!(text(&buffer), "hé\u{1f600}llo");
}

#[test]
fn an_empty_insert_is_an_edit() {
    let mut buffer = EditorBuffer::default();
    buffer.insert(0, "ab").unwrap();
    buffer.undo().unwrap();
    buffer.insert(0, "").unwrap();
    assert!(buffer.redo().is_err());
}

#[test]
fn the_parser_reads_each_command() {
    assert!(matches!(
        command("i 5  world"),
        Some(Command::Insert(5, " world"))
    ));
    assert!(matches!(command("i 0 "), Some(Command::Insert(0, ""))));
    assert!(matches!(command("i 007 x"), Some(Command::Insert(7, "x"))));
    assert!(matches!(command("d 1 2"), Some(Command::Delete(1, 2))));
    assert!(matches!(command("u"), Some(Command::Undo)));
    assert!(matches!(command("r"), Some(Command::Redo)));
    assert!(matches!(command("p"), Some(Command::Print)));
    assert!(matches!(command("q"), Some(Command::Quit)));
    for line in [
        "",
        "x",
        "uu",
        "u ",
        "i",
        "i 5",
        "i x y",
        "i -1 y",
        "i  1 y",
        "d 1",
        "d 1 2 3",
        "d 1  2",
        "d 1 x",
        "i 99999999999999999999999 y",
    ] {
        assert!(command(line).is_none(), "{line:?}");
    }
}
