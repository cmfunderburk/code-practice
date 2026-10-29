//! Game of Life: whole program.
// From Python:
// 1. Live cells stay a set and the step stays a `Counter` scatter, as in Python:
//    `HashSet` and `HashMap` are in the standard library. The C port, which has
//    neither, stores a dense grid. [library]
// 2. Coordinates are `usize`, which can't be negative. A neighbor above row 0
//    or left of column 0 is dropped as it is made, and the final filter clips
//    only the bottom and right edges. [integers]
// 3. Python raises `ValueError` from `parse_input`. Here it returns
//    `Result<World, String>`, and `?` passes a header error up (Rust Book 9.2).
//    It reads the way Python's does, with `lines` and `split_whitespace`, so
//    extra spaces and `\r\n` line ends are accepted. [errors]
// 4. Up to 1,001 frames of 100 lines go through a locked `BufWriter`, the
//    usual choice for a whole program, so stdout isn't flushed at every
//    newline. [io]

// Python's `set` and `Counter` (Rust Book 8.3).
use std::collections::{HashMap, HashSet};
use std::io::{self, BufWriter, Write};

// A type alias names the tuple once.
type Cell = (usize, usize);

fn step(live: &HashSet<Cell>, rows: usize, cols: usize) -> HashSet<Cell> {
    // Python's `Counter`. At most 8 neighbors are counted, so `u8` is enough.
    let mut counts: HashMap<Cell, u8> = HashMap::new();
    for &(r, c) in live {
        for dr in -1..=1 {
            for dc in -1..=1 {
                if (dr, dc) == (0, 0) {
                    continue;
                }
                // `checked_add_signed` adds -1, 0, or 1 to a `usize`, giving `None` below 0
                // (std: usize::checked_add_signed).
                if let (Some(nr), Some(nc)) = (r.checked_add_signed(dr), c.checked_add_signed(dc)) {
                    // `entry` finds or inserts the key, and `or_default` starts it at 0: Python's
                    // `counts[cell] += 1` on a `Counter` (Rust Book 8.3).
                    *counts.entry((nr, nc)).or_default() += 1;
                }
            }
        }
    }
    counts
        .into_iter()
        .filter(|&(cell, n)| n == 3 || (n == 2 && live.contains(&cell)))
        .map(|(cell, _)| cell)
        // Python's `0 <= r < rows`: with `usize` the lower bound always holds.
        .filter(|&(r, c)| r < rows && c < cols)
        .collect()
}

struct World {
    rows: usize,
    cols: usize,
    generations: usize,
    live: HashSet<Cell>,
}

// Python's `parse_input`, returning the live set rather than grid lines.
fn parse_input(text: &str) -> Result<World, String> {
    // Python's `splitlines()`: `lines` drops each `\n` and a `\r\n`.
    let mut lines = text.lines();
    // `ok_or` turns `None` into an `Err`, and `?` converts the `&str` into the
    // `String` the function returns.
    let header = lines.next().ok_or("empty input")?;
    // Python's `map(int, header.split())`. Collecting an iterator of `Result`s
    // into one `Result` stops at the first field that isn't a number. `parse`
    // infers `usize` from the annotation, so `-1` fails here, and a number too
    // big for `usize` is an `Err`, not a wrap.
    let numbers: Vec<usize> = header
        .split_whitespace()
        .map(str::parse)
        .collect::<Result<_, _>>()
        .map_err(|err| format!("header: {err}"))?;
    // A slice pattern in a `let…else`: exactly three numbers, or the `else`
    // branch (Rust Book 6.3).
    let [rows, cols, generations] = numbers[..] else {
        return Err(format!("header needs rows cols generations: {header:?}"));
    };
    if !(1..=100).contains(&rows) || !(1..=100).contains(&cols) || generations > 1000 {
        return Err(format!(
            "need 1-100 rows and cols, 0-1000 generations: {header:?}"
        ));
    }
    let grid: Vec<&str> = lines.collect();
    if grid.len() != rows {
        return Err(format!("expected {rows} grid lines, got {}", grid.len()));
    }
    let mut live = HashSet::new();
    for (r, line) in grid.iter().enumerate() {
        if line.len() != cols || !line.bytes().all(|b| b == b'#' || b == b'.') {
            return Err(format!("row {r} must be {cols} of '#' or '.': {line:?}"));
        }
        live.extend(
            line.bytes()
                .enumerate()
                .filter(|&(_, b)| b == b'#')
                .map(|(c, _)| (r, c)),
        );
    }
    Ok(World {
        rows,
        cols,
        generations,
        live,
    })
}

fn main() {
    // Python's `sys.stdin.read()`. Input that isn't UTF-8 is an `Err` here, and
    // `and_then` runs the parser only on `Ok`.
    let world = io::read_to_string(io::stdin())
        .map_err(|err| err.to_string())
        .and_then(|text| parse_input(&text));
    // Destructuring takes the fields out of the struct (Rust Book 19.3).
    let World {
        rows,
        cols,
        generations,
        mut live,
    } = match world {
        Ok(world) => world,
        Err(message) => {
            println!("error: {message}");
            return;
        }
    };
    let mut out = BufWriter::new(io::stdout().lock());
    for generation in 0..=generations {
        if generation > 0 {
            live = step(&live, rows, cols);
        }
        writeln!(out, "gen {generation}").unwrap();
        for r in 0..rows {
            // Python's `"".join(...)`: collecting `char`s builds a `String`.
            let line: String = (0..cols)
                .map(|c| if live.contains(&(r, c)) { '#' } else { '.' })
                .collect();
            writeln!(out, "{line}").unwrap();
        }
    }
}
