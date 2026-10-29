//! Game of Life: whole program.

use std::collections::{HashMap, HashSet};
use std::io::{self, BufWriter, Write};

type Cell = (usize, usize);

fn step(live: &HashSet<Cell>, rows: usize, cols: usize) -> HashSet<Cell> {
    let mut counts: HashMap<Cell, u8> = HashMap::new();
    for &(r, c) in live {
        for dr in -1..=1 {
            for dc in -1..=1 {
                if (dr, dc) == (0, 0) {
                    continue;
                }
                if let (Some(nr), Some(nc)) = (r.checked_add_signed(dr), c.checked_add_signed(dc)) {
                    *counts.entry((nr, nc)).or_default() += 1;
                }
            }
        }
    }
    counts
        .into_iter()
        .filter(|&(cell, n)| n == 3 || (n == 2 && live.contains(&cell)))
        .map(|(cell, _)| cell)
        .filter(|&(r, c)| r < rows && c < cols)
        .collect()
}

struct World {
    rows: usize,
    cols: usize,
    generations: usize,
    live: HashSet<Cell>,
}

fn parse_input(text: &str) -> Result<World, String> {
    let mut lines = text.lines();
    let header = lines.next().ok_or("empty input")?;
    let numbers: Vec<usize> = header
        .split_whitespace()
        .map(str::parse)
        .collect::<Result<_, _>>()
        .map_err(|err| format!("header: {err}"))?;
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
    let world = io::read_to_string(io::stdin())
        .map_err(|err| err.to_string())
        .and_then(|text| parse_input(&text));
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
            let line: String = (0..cols)
                .map(|c| if live.contains(&(r, c)) { '#' } else { '.' })
                .collect();
            writeln!(out, "{line}").unwrap();
        }
    }
}
