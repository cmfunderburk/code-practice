//! Roman Numerals: whole program.

// From Python:
// 1. Python's `ROMAN_TABLE` tuple becomes a `const` array of `(i64, &str)` rows,
//    and the `for` loop takes each row by value (Rust Book 3.1, "Declaring
//    Constants"). Python's `symbol * count` is `str::repeat`. [table]
// 2. Python's `to_roman` raises `ValueError` outside 1-3999, and the shell
//    prints the error. Here it returns `Option<String>`, and `answer` writes the
//    refusal itself (Rust Book 6.1, "The Option Enum"). [errors]
// 3. The canonical test keeps Python's round trip, render the parse and
//    compare, with `?` on `Option` for the two ways it can fail: a letter that
//    isn't a numeral, and a total outside 1-3999 (Rust Book 9.2, "Where to Use
//    the ? Operator"). [round trip]
// 4. Python's `strip().upper()` and `int(line)` become `trim()`,
//    `to_ascii_uppercase()`, and `str::parse`, Rust's own reading of a line:
//    `parse` also takes a sign, so `+12` is a number. [text]

// `io::stdin().lines()` yields each line without its line end.
use std::io;

// Descending, with the six subtractive pairs as rows of their own: a greedy
// walk then never needs to look ahead. One integer type, `i64`, runs through
// the whole program, so the parse's total renders back with no conversion.
const TABLE: [(i64, &str); 13] = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
];

fn to_roman(n: i64) -> Option<String> {
    if !(1..=3999).contains(&n) {
        return None;
    }
    let mut rest = n;
    let mut numeral = String::new();
    for (value, symbol) in TABLE {
        // `rest` is never negative, so the count converts to `usize` exactly.
        numeral.push_str(&symbol.repeat((rest / value) as usize));
        rest %= value;
    }
    Some(numeral)
}

// Python's `VALUES` dict as a `match`; `None` is a letter that isn't a numeral.
fn value(letter: char) -> Option<i64> {
    match letter {
        'I' => Some(1),
        'V' => Some(5),
        'X' => Some(10),
        'L' => Some(50),
        'C' => Some(100),
        'D' => Some(500),
        'M' => Some(1000),
        _ => None,
    }
}

// The subtractive scan: a letter smaller than the next one subtracts. It totals
// any string of numeral letters, canonical or not. The total is signed because
// a subtraction can come first (`IV` starts at -1). Collecting into
// `Option<Vec<_>>` stops at the first letter that isn't a numeral.
fn from_roman(numeral: &str) -> Option<i64> {
    let values: Vec<i64> = numeral.chars().map(value).collect::<Option<_>>()?;
    let mut total = 0;
    for (i, &v) in values.iter().enumerate() {
        if values.get(i + 1).is_some_and(|&next| v < next) {
            total -= v;
        } else {
            total += v;
        }
    }
    Some(total)
}

fn canonical(numeral: &str) -> Option<i64> {
    let n = from_roman(numeral)?;
    (to_roman(n)? == numeral).then_some(n)
}

fn answer(line: &str) -> String {
    let line = line.trim().to_ascii_uppercase();
    // A number too big for `i64` fails to parse and falls through to the
    // numeral test, which refuses it.
    if let Ok(n) = line.parse::<i64>() {
        return to_roman(n).unwrap_or_else(|| format!("error: {n} is not in 1-3999"));
    }
    // `{line:?}` quotes the line, so an empty or odd one is visible.
    match canonical(&line) {
        Some(n) => n.to_string(),
        None => format!("error: {line:?} is not a number 1-3999 or a canonical numeral"),
    }
}

// Python's `input()` loop. `map_while(Result::ok)` stops at the first read
// error, such as a line that isn't UTF-8, as end of input does.
fn main() {
    for line in io::stdin().lines().map_while(Result::ok) {
        println!("{}", answer(&line));
    }
}
