//! Logo Interpreter: whole program.

use std::fmt::Write;
use std::io;

const VECTORS: [(i64, i64); 4] = [(1, 0), (0, 1), (-1, 0), (0, -1)];
const HEADINGS: [char; 4] = ['E', 'N', 'W', 'S'];

type Segment = ((i64, i64), (i64, i64));

#[derive(Clone, Copy)]
struct Turtle {
    x: i64,
    y: i64,
    heading: usize,
    pen_down: bool,
}

enum Command {
    Forward(i64),
    Turn(usize),
    Pen(bool),
    Repeat(i64, Vec<Command>),
}

impl Command {
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

fn tokens(line: &str) -> Vec<String> {
    line.replace('[', " [ ")
        .replace(']', " ] ")
        .split_whitespace()
        .map(str::to_ascii_uppercase)
        .collect()
}

fn positive(token: Option<&String>) -> Result<i64, String> {
    let token = token.ok_or("a count or distance is missing")?;
    match token.parse::<i64>() {
        Ok(value) if value >= 1 => Ok(value),
        Ok(_) => Err("counts and distances must be positive".to_string()),
        Err(_) => Err(format!("expected a positive integer, got {token}")),
    }
}

fn parse_block(
    tokens: &mut std::slice::Iter<String>,
    nested: bool,
) -> Result<Vec<Command>, String> {
    let mut commands = Vec::new();
    while let Some(op) = tokens.next() {
        let command = match op.as_str() {
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

    fn execute(&mut self, tokens: &[String]) -> Result<(), String> {
        let start = self.undo.len();
        for command in parse_block(&mut tokens.iter(), false)? {
            self.undo.push((self.turtle, self.segments.len()));
            if command.run(&mut self.turtle, &mut self.segments).is_none() {
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
    for line in io::stdin().lines().map_while(Result::ok) {
        let tokens = tokens(&line);
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
