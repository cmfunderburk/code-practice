//! Editor Buffer: whole program.

// From Python:
// 1. Python's two frozen dataclasses, `Insert` and `Delete`, become one enum,
//    `Edit`, whose variants carry their fields, and `apply` and `invert` match on
//    the variant (Rust Book 6.1, 6.2). [command objects]
// 2. The buffer is `Vec<char>`, not `String`. SPEC counts code points, and a
//    `String` can't be indexed by character (Rust Book 8.2, "Indexing into
//    Strings"), so each edit would first walk the text for byte offsets.
//    [text]
// 3. Python's `apply` builds a new string. Here it changes the buffer through
//    `&mut Vec<char>` (Rust Book 4.2, "Mutable References"), and `invert(self)`
//    moves the edit's text into its inverse, so undo and redo copy no text
//    (Rust Book 4.1, "Ownership and Functions"). [ownership]
// 4. Python's `ValueError` becomes `Result<(), String>`, and `ok_or` with `?`
//    turns an empty stack into its message (Rust Book 9.2, "The ? Operator
//    Shortcut"). [errors]
// 5. Python's `input()` and `int()` become `io::stdin().lines()` and
//    `str::parse`, Rust's own reading of a line and a number. [text]
// 6. The parsed `Command` borrows the insert text from the line, so its type
//    carries a lifetime (Rust Book 10.3, "In Struct Definitions"; the rule is
//    the same for an enum). [borrowing]

use std::io;

const HELP: &str = "i <pos> <text> | d <pos> <n> | u | r | p | q";

// The text of a `Delete` is what it removed, captured when the edit is built:
// that is what lets the inverse exist.
enum Edit {
    Insert { pos: usize, text: Vec<char> },
    Delete { pos: usize, text: Vec<char> },
}

impl Edit {
    fn apply(&self, buffer: &mut Vec<char>) {
        match self {
            Edit::Insert { pos, text } => {
                // `splice` over an empty range inserts; `drain` removes a range.
                buffer.splice(*pos..*pos, text.iter().copied());
            }
            Edit::Delete { pos, text } => {
                buffer.drain(*pos..*pos + text.len());
            }
        }
    }

    // Takes the edit by value, so its `Vec<char>` moves into the new variant.
    fn invert(self) -> Edit {
        match self {
            Edit::Insert { pos, text } => Edit::Delete { pos, text },
            Edit::Delete { pos, text } => Edit::Insert { pos, text },
        }
    }
}

#[derive(Default)]
struct EditorBuffer {
    text: Vec<char>,
    undo: Vec<Edit>,
    redo: Vec<Edit>,
}

impl EditorBuffer {
    fn insert(&mut self, pos: usize, text: &str) -> Result<(), String> {
        if pos > self.text.len() {
            return Err(format!("insert out of range: {pos}"));
        }
        self.apply(Edit::Insert {
            pos,
            text: text.chars().collect(),
        });
        Ok(())
    }

    fn delete(&mut self, pos: usize, n: usize) -> Result<(), String> {
        // `n` is compared with what is left after `pos`, so a huge `pos + n` is
        // never computed: in a debug build it would panic on overflow.
        if n < 1 || pos > self.text.len() || n > self.text.len() - pos {
            return Err(format!("delete out of range: {pos}+{n}"));
        }
        // The one copy of text in the program: the characters a delete removes.
        let text = self.text[pos..pos + n].to_vec();
        self.apply(Edit::Delete { pos, text });
        Ok(())
    }

    fn apply(&mut self, edit: Edit) {
        edit.apply(&mut self.text);
        self.undo.push(edit);
        self.redo.clear();
    }

    // Pop, apply the inverse, and push the original for redo: two moves of the
    // same text, no copies.
    fn undo(&mut self) -> Result<(), String> {
        let edit = self.undo.pop().ok_or("nothing to undo")?;
        let inverse = edit.invert();
        inverse.apply(&mut self.text);
        self.redo.push(inverse.invert());
        Ok(())
    }

    fn redo(&mut self) -> Result<(), String> {
        let edit = self.redo.pop().ok_or("nothing to redo")?;
        edit.apply(&mut self.text);
        self.undo.push(edit);
        Ok(())
    }
}

// `'a` ties the insert text to the decoded line it borrows from.
enum Command<'a> {
    Insert(usize, &'a str),
    Delete(usize, usize),
    Undo,
    Redo,
    Print,
    Quit,
}

fn command(line: &str) -> Option<Command<'_>> {
    match line {
        "u" => return Some(Command::Undo),
        "r" => return Some(Command::Redo),
        "p" => return Some(Command::Print),
        "q" => return Some(Command::Quit),
        _ => {}
    }
    // SPEC §2 by `split_once`: one space after the verb and one after `<pos>`.
    // For `d`, a third field stays inside `<n>` and fails the digit test.
    match line.split_once(' ')? {
        ("i", rest) => {
            let (pos, text) = rest.split_once(' ')?;
            // `str::parse` is Rust's `int()`: ASCII digits, an optional `+`, and
            // `Err` past `usize::MAX`, which `.ok()?` turns into "not a command".
            Some(Command::Insert(pos.parse().ok()?, text))
        }
        ("d", rest) => {
            let (pos, n) = rest.split_once(' ')?;
            Some(Command::Delete(pos.parse().ok()?, n.parse().ok()?))
        }
        _ => None,
    }
}

fn main() {
    let mut buffer = EditorBuffer::default();
    // Python's `input()` loop. `lines()` drops each `\n`, and a `\r\n` with it;
    // `map_while(Result::ok)` stops at a read error, such as a line that isn't
    // UTF-8, as end of input does.
    for line in io::stdin().lines().map_while(Result::ok) {
        let result = match command(&line) {
            None => Err(HELP.to_string()),
            // `q` ends the program at once: lines after it are not read.
            Some(Command::Quit) => return,
            Some(Command::Insert(pos, text)) => buffer.insert(pos, text),
            Some(Command::Delete(pos, n)) => buffer.delete(pos, n),
            Some(Command::Undo) => buffer.undo(),
            Some(Command::Redo) => buffer.redo(),
            Some(Command::Print) => {
                println!("\"{}\"", buffer.text.iter().collect::<String>());
                Ok(())
            }
        };
        if let Err(message) = result {
            println!("{message}");
        }
    }
}
