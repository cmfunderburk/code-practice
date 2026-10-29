//! Expression Calculator: whole program.
// From Python:
// 1. Python's tagged tuples become `enum Node`, with children in `Box` because a
//    type can't contain itself directly (Rust Book 15.1). `match` must cover
//    every variant, so an unknown node can't reach `evaluate`. [types]
// 2. Python's `int | float` becomes `enum Value`. Integer arithmetic uses
//    `checked_add` and its siblings, which return `None` on overflow where
//    Python's integers would just grow; a debug build would panic. [integers]
// 3. Python's parsing functions raise `ValueError` and return `(node, pos)`.
//    Here they are methods on a `Parser` that owns `pos`, and each returns
//    `Result<Node, String>`, with `?` passing an error up (Rust Book 9.2).
//    [errors]
// 4. Python's `input()` raising `EOFError` becomes `lines()` running out; a
//    line that isn't UTF-8 ends the session too. [io]
// 5. Python's `print` of a float becomes `Display`, which also prints the
//    shortest text that reads back to the same float, but shows `8/2` as `4`
//    where Python shows `4.0`. [text]

use std::io;

// Python's token strings. `Copy` lets `peek` hand a token out by value, and
// `PartialEq` lets the parser compare one with `!=`.
#[derive(Clone, Copy, PartialEq)]
enum Token {
    Num(i64),
    Op(u8),
}

// Python's `("num", v)`, `("neg", node)`, and `(op, left, right)`.
enum Node {
    Num(i64),
    Neg(Box<Node>),
    Bin(u8, Box<Node>, Box<Node>),
}

// Python's `int | float`. `Debug` and `PartialEq` let two values be compared
// with `assert_eq!`.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Value {
    Int(i64),
    Float(f64),
}

fn tokenize(text: &str) -> Result<Vec<Token>, String> {
    let bytes = text.as_bytes();
    let mut tokens = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        match bytes[i] {
            b' ' | b'\t' => i += 1,
            b'0'..=b'9' => {
                let start = i;
                while i < bytes.len() && bytes[i].is_ascii_digit() {
                    i += 1;
                }
                // `?` converts the `&str` error into the function's `String` error type.
                let value = text[start..i].parse().map_err(|_| "number too large")?;
                tokens.push(Token::Num(value));
            }
            // `op @` binds the matched byte to a name (Rust Book 19.3).
            op @ (b'+' | b'-' | b'*' | b'/' | b'(' | b')') => {
                tokens.push(Token::Op(op));
                i += 1;
            }
            _ => {
                // Only ASCII bytes were consumed, so `i` is on a character boundary and the
                // whole character can be named in the message.
                let ch = text[i..].chars().next().unwrap();
                return Err(format!("unknown character: {ch}"));
            }
        }
    }
    Ok(tokens)
}

struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    fn peek(&self) -> Option<Token> {
        // `get` returns `None` past the end, where Python checks `pos == len(tokens)`.
        self.tokens.get(self.pos).copied()
    }

    fn expr(&mut self) -> Result<Node, String> {
        let mut node = self.term()?;
        // Python's `while pos < len(tokens) and tokens[pos] in "+-"`, as one pattern.
        while let Some(Token::Op(op @ (b'+' | b'-'))) = self.peek() {
            self.pos += 1;
            node = Node::Bin(op, Box::new(node), Box::new(self.term()?));
        }
        Ok(node)
    }

    fn term(&mut self) -> Result<Node, String> {
        let mut node = self.factor()?;
        while let Some(Token::Op(op @ (b'*' | b'/'))) = self.peek() {
            self.pos += 1;
            node = Node::Bin(op, Box::new(node), Box::new(self.factor()?));
        }
        Ok(node)
    }

    fn factor(&mut self) -> Result<Node, String> {
        // `ok_or` turns `None` into an `Err`, and `?` returns it.
        let token = self.peek().ok_or("unexpected end of input")?;
        self.pos += 1;
        match token {
            Token::Op(b'-') => Ok(Node::Neg(Box::new(self.factor()?))),
            Token::Op(b'(') => {
                let node = self.expr()?;
                if self.peek() != Some(Token::Op(b')')) {
                    return Err("expected )".to_string());
                }
                self.pos += 1;
                Ok(node)
            }
            Token::Num(value) => Ok(Node::Num(value)),
            Token::Op(op) => Err(format!("unexpected token: {}", char::from(op))),
        }
    }
}

fn parse(tokens: Vec<Token>) -> Result<Node, String> {
    let mut parser = Parser { tokens, pos: 0 };
    let node = parser.expr()?;
    if parser.pos != parser.tokens.len() {
        return Err("trailing input".to_string());
    }
    Ok(node)
}

fn real(value: Value) -> f64 {
    match value {
        // `as` rounds an integer past 2^53 to the nearest float, as Python's
        // `float()` does.
        Value::Int(v) => v as f64,
        Value::Float(v) => v,
    }
}

fn apply(op: u8, a: Value, b: Value) -> Result<Value, String> {
    match (a, b) {
        _ if op == b'/' => {
            let divisor = real(b);
            // Python raises `ZeroDivisionError` for `0` and `0.0`; `-0.0 == 0.0` too.
            if divisor == 0.0 {
                return Err("division by zero".to_string());
            }
            Ok(Value::Float(real(a) / divisor))
        }
        (Value::Int(x), Value::Int(y)) => {
            let result = match op {
                b'+' => x.checked_add(y),
                b'-' => x.checked_sub(y),
                _ => x.checked_mul(y),
            };
            result
                .map(Value::Int)
                .ok_or_else(|| "integer overflow".to_string())
        }
        _ => {
            let (x, y) = (real(a), real(b));
            Ok(Value::Float(match op {
                b'+' => x + y,
                b'-' => x - y,
                _ => x * y,
            }))
        }
    }
}

fn evaluate(node: &Node) -> Result<Value, String> {
    match node {
        Node::Num(value) => Ok(Value::Int(*value)),
        Node::Neg(operand) => match evaluate(operand)? {
            Value::Int(v) => v
                .checked_neg()
                .map(Value::Int)
                .ok_or_else(|| "integer overflow".to_string()),
            Value::Float(v) => Ok(Value::Float(-v)),
        },
        Node::Bin(op, left, right) => apply(*op, evaluate(left)?, evaluate(right)?),
    }
}

// Python's `evaluate(parse(tokenize(text)))`, with `?` after each stage.
fn calculate(text: &str) -> Result<Value, String> {
    evaluate(&parse(tokenize(text)?)?)
}

fn main() {
    // Python's `input()` loop. `lines()` drops the `\n` (and a `\r\n`), and
    // `map_while(Result::ok)` stops at the first read error, such as a line that
    // isn't UTF-8, as end of input does.
    let lines = io::stdin().lines().map_while(Result::ok);
    // An empty line ends the session, as in Python's shell.
    for line in lines.take_while(|line| !line.is_empty()) {
        match calculate(&line) {
            // `Display` for `f64` prints the shortest text that reads back to the
            // same float, like Python's `print`, but drops a whole number's
            // `.0`: `8/2` prints `4`.
            Ok(Value::Int(v)) => println!("{v}"),
            Ok(Value::Float(v)) => println!("{v}"),
            Err(message) => println!("error: {message}"),
        }
    }
}
