//! Editor Buffer: whole program.

use std::io;

const HELP: &str = "i <pos> <text> | d <pos> <n> | u | r | p | q";

enum Edit {
    Insert { pos: usize, text: Vec<char> },
    Delete { pos: usize, text: Vec<char> },
}

impl Edit {
    fn apply(&self, buffer: &mut Vec<char>) {
        match self {
            Edit::Insert { pos, text } => {
                buffer.splice(*pos..*pos, text.iter().copied());
            }
            Edit::Delete { pos, text } => {
                buffer.drain(*pos..*pos + text.len());
            }
        }
    }

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
        if n < 1 || pos > self.text.len() || n > self.text.len() - pos {
            return Err(format!("delete out of range: {pos}+{n}"));
        }
        let text = self.text[pos..pos + n].to_vec();
        self.apply(Edit::Delete { pos, text });
        Ok(())
    }

    fn apply(&mut self, edit: Edit) {
        edit.apply(&mut self.text);
        self.undo.push(edit);
        self.redo.clear();
    }

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
    match line.split_once(' ')? {
        ("i", rest) => {
            let (pos, text) = rest.split_once(' ')?;
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
    for line in io::stdin().lines().map_while(Result::ok) {
        let result = match command(&line) {
            None => Err(HELP.to_string()),
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
