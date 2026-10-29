//! Roman Numerals: whole program.

use std::io;

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
        numeral.push_str(&symbol.repeat((rest / value) as usize));
        rest %= value;
    }
    Some(numeral)
}

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
    if let Ok(n) = line.parse::<i64>() {
        return to_roman(n).unwrap_or_else(|| format!("error: {n} is not in 1-3999"));
    }
    match canonical(&line) {
        Some(n) => n.to_string(),
        None => format!("error: {line:?} is not a number 1-3999 or a canonical numeral"),
    }
}

fn main() {
    for line in io::stdin().lines().map_while(Result::ok) {
        println!("{}", answer(&line));
    }
}
