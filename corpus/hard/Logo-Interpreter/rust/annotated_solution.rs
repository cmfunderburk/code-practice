//! Logo Interpreter: whole program.

// From Python:
// 1. Python's `Command` dataclass, an `op` string with an untyped `arg`,
//    becomes an enum whose variants carry their own data (Rust Book 6.1).
//    `Repeat` holds its block in a `Vec`, which already puts the children on
//    the heap, so the recursive type needs no `Box` (Rust Book 15.1, "Enabling
//    Recursive Types with Boxes"). [commands]
// 2. Python's `apply` returns a new frozen `Drawing`. Here `run` changes the
//    turtle and appends segments through `&mut` (Rust Book 4.2). [state]
// 3. Python's undo stack holds `Restore` values, each a whole previous
//    `Drawing`. Here an entry is the previous `Turtle`, which is `Copy`, and the
//    segment count: commands only append segments, so `truncate` restores the
//    drawing (Rust Book Appendix C, "Clone and Copy"). [history]
// 4. Python's `split()` becomes `split_whitespace` and `int()` becomes
//    `parse::<i64>`, each Rust's own rule: `parse` takes a sign and leading
//    zeros but not `int`'s `_` separators, so `1_000` is an error here, and it
//    fails on a number past `i64`. [parsing]
// 5. Python's `ValueError` becomes `Result<_, String>`, passed up the parser's
//    recursion with `?` (Rust Book 9.2). The line parses before anything runs,
//    so a bad line changes nothing. [errors]
// 6. Python's integers never overflow. Coordinates are `i64`, and `run` moves
//    with `checked_mul` and `checked_add`, whose `None` the `?` operator passes
//    up through `Option<()>` (Rust Book 9.2, "Where the ? Operator Can Be
//    Used"). `execute` then rolls the whole line back, so an overflow is an
//    error line rather than a debug-build panic. [integers]
// 7. Python's `input()` raises `EOFError` at end of input. `stdin().lines()`
//    is an iterator that simply ends. [io]

use std::fmt::Write;
use std::io;

const VECTORS: [(i64, i64); 4] = [(1, 0), (0, 1), (-1, 0), (0, -1)];
const HEADINGS: [char; 4] = ['E', 'N', 'W', 'S'];

type Segment = ((i64, i64), (i64, i64));

// `Copy`: a history entry and an undo copy the turtle by assignment.
#[derive(Clone, Copy)]
struct Turtle {
    x: i64,
    y: i64,
    heading: usize,
    pen_down: bool,
}

// LEFT and RIGHT are quarter turns counterclockwise, 1 and 3; PENUP and
// PENDOWN set the pen.
enum Command {
    Forward(i64),
    Turn(usize),
    Pen(bool),
    Repeat(i64, Vec<Command>),
}

impl Command {
    // `None` when a coordinate would overflow `i64`; `?` passes it up.
    fn run(&self, turtle: &mut Turtle, segments: &mut Vec<Segment>) -> Option<()> {
        match self {
            Command::Forward(distance) => {
                let start = (turtle.x, turtle.y);
                let (dx, dy) = VECTORS[turtle.heading];
                turtle.x = turtle.x.checked_add(dx.checked_mul(*distance)?)?;
                turtle.y = turtle.y.checked_add(dy.checked_mul(*distance)?)?;
                if turtle.pen_down {
                    segments.push((start, (turtle.x, turtle.y)));
                }
            }
            Command::Turn(quarters) => turtle.heading = (turtle.heading + quarters) % 4,
            Command::Pen(down) => turtle.pen_down = *down,
            // Repeat borrows its block and runs it `count` times; no history here,
            // since only top-level commands are entries.
            Command::Repeat(count, body) => {
                for _ in 0..*count {
                    for command in body {
                        command.run(turtle, segments)?;
                    }
                }
            }
        }
        Some(())
    }
}

// Brackets get spaces around them, as in Python, so they split off as tokens.
fn tokens(line: &str) -> Vec<String> {
    line.replace('[', " [ ")
        .replace(']', " ] ")
        .split_whitespace()
        .map(str::to_ascii_uppercase)
        .collect()
}

fn positive(token: Option<&String>) -> Result<i64, String> {
    let token = token.ok_or("a count or distance is missing")?;
    // `parse` takes a sign and leading zeros, but no `_`, and fails past `i64`.
    match token.parse::<i64>() {
        Ok(value) if value >= 1 => Ok(value),
        Ok(_) => Err("counts and distances must be positive".to_string()),
        Err(_) => Err(format!("expected a positive integer, got {token}")),
    }
}

// One recursive call per `[`, as in Python; the shared iterator is the
// position, so a nested block resumes its parent where it stopped.
fn parse_block(
    tokens: &mut std::slice::Iter<String>,
    nested: bool,
) -> Result<Vec<Command>, String> {
    let mut commands = Vec::new();
    while let Some(op) = tokens.next() {
        let command = match op.as_str() {
            // A match guard tells the closing `]` of a block from a stray one.
            "]" if nested => return Ok(commands),
            "]" => return Err("unexpected ]".to_string()),
            "FORWARD" => Command::Forward(positive(tokens.next())?),
            "LEFT" => Command::Turn(1),
            "RIGHT" => Command::Turn(3),
            "PENUP" => Command::Pen(false),
            "PENDOWN" => Command::Pen(true),
            "REPEAT" => {
                let count = positive(tokens.next())?;
                if tokens.next().map(String::as_str) != Some("[") {
                    return Err("REPEAT needs a count and [ block ]".to_string());
                }
                Command::Repeat(count, parse_block(tokens, true)?)
            }
            _ => return Err(format!("unknown command: {op}")),
        };
        commands.push(command);
    }
    if nested {
        return Err("missing ]".to_string());
    }
    Ok(commands)
}

struct Logo {
    turtle: Turtle,
    segments: Vec<Segment>,
    // Each entry: the turtle before a top-level command, and how many segments
    // there were.
    undo: Vec<(Turtle, usize)>,
}

impl Logo {
    fn new() -> Logo {
        Logo {
            turtle: Turtle {
                x: 0,
                y: 0,
                heading: 0,
                pen_down: true,
            },
            segments: Vec::new(),
            undo: Vec::new(),
        }
    }

    // `?` returns before the loop on a parse error, so nothing changes.
    fn execute(&mut self, tokens: &[String]) -> Result<(), String> {
        let start = self.undo.len();
        for command in parse_block(&mut tokens.iter(), false)? {
            self.undo.push((self.turtle, self.segments.len()));
            if command.run(&mut self.turtle, &mut self.segments).is_none() {
                // An overflow puts back the line's first entry, so the failing
                // line changes nothing, as a parse error doesn't.
                let (turtle, drawn) = self.undo[start];
                self.turtle = turtle;
                self.segments.truncate(drawn);
                self.undo.truncate(start);
                return Err("the turtle would leave the 64-bit grid".to_string());
            }
        }
        Ok(())
    }

    fn undo(&mut self) -> Result<(), String> {
        let (turtle, drawn) = self.undo.pop().ok_or("nothing to undo")?;
        self.turtle = turtle;
        self.segments.truncate(drawn);
        Ok(())
    }

    // The state line and every segment in one `String`, printed once;
    // `writeln!` into a `String` comes from `std::fmt::Write`.
    fn report(&self) -> String {
        let Turtle {
            x,
            y,
            heading,
            pen_down,
        } = self.turtle;
        let mut text = format!(
            "x={x} y={y} heading={} pen={} segments={}\n",
            HEADINGS[heading],
            if pen_down { "down" } else { "up" },
            self.segments.len()
        );
        for ((x1, y1), (x2, y2)) in &self.segments {
            writeln!(text, "{x1},{y1} -> {x2},{y2}").unwrap();
        }
        text
    }
}

fn main() {
    let mut logo = Logo::new();
    // `lines()` yields each line without its `\n` (or `\r\n`); a line that isn't
    // UTF-8 is an `Err`, and `map_while` stops there, as at end of input.
    for line in io::stdin().lines().map_while(Result::ok) {
        let tokens = tokens(&line);
        // UNDO is a line, not a command: only a line whose sole token it is.
        let result = if tokens == ["UNDO"] {
            logo.undo()
        } else {
            logo.execute(&tokens)
        };
        match result {
            Ok(()) => print!("{}", logo.report()),
            Err(message) => println!("error: {message}"),
        }
    }
}
