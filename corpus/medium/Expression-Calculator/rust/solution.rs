//! Expression Calculator: whole program.

use std::io;

#[derive(Clone, Copy, PartialEq)]
enum Token {
    Num(i64),
    Op(u8),
}

enum Node {
    Num(i64),
    Neg(Box<Node>),
    Bin(u8, Box<Node>, Box<Node>),
}

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
                let value = text[start..i].parse().map_err(|_| "number too large")?;
                tokens.push(Token::Num(value));
            }
            op @ (b'+' | b'-' | b'*' | b'/' | b'(' | b')') => {
                tokens.push(Token::Op(op));
                i += 1;
            }
            _ => {
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
        self.tokens.get(self.pos).copied()
    }

    fn expr(&mut self) -> Result<Node, String> {
        let mut node = self.term()?;
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
        Value::Int(v) => v as f64,
        Value::Float(v) => v,
    }
}

fn apply(op: u8, a: Value, b: Value) -> Result<Value, String> {
    match (a, b) {
        _ if op == b'/' => {
            let divisor = real(b);
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

fn calculate(text: &str) -> Result<Value, String> {
    evaluate(&parse(tokenize(text)?)?)
}

fn main() {
    let lines = io::stdin().lines().map_while(Result::ok);
    for line in lines.take_while(|line| !line.is_empty()) {
        match calculate(&line) {
            Ok(Value::Int(v)) => println!("{v}"),
            Ok(Value::Float(v)) => println!("{v}"),
            Err(message) => println!("error: {message}"),
        }
    }
}
