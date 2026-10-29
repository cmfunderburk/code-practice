use super::*;

// SPEC §1's place-value table, a different algorithm from the greedy walk.
fn positional(n: i64) -> String {
    const PLACES: [[&str; 10]; 4] = [
        ["", "M", "MM", "MMM", "", "", "", "", "", ""],
        ["", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"],
        ["", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"],
        ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"],
    ];
    let digits = [n / 1000, n / 100 % 10, n / 10 % 10, n % 10];
    PLACES
        .iter()
        .zip(digits)
        .map(|(place, d)| place[d as usize])
        .collect()
}

#[test]
fn every_number_renders_and_parses_back() {
    for n in 1..=3999 {
        let numeral = positional(n);
        assert_eq!(to_roman(n).as_deref(), Some(numeral.as_str()), "{n}");
        assert_eq!(from_roman(&numeral), Some(n), "{numeral}");
        assert_eq!(canonical(&numeral), Some(n), "{numeral}");
    }
}

#[test]
fn render_refuses_numbers_outside_the_domain() {
    for n in [0, 4000, -1, i64::MAX] {
        assert_eq!(to_roman(n), None, "{n}");
    }
}

#[test]
fn the_scan_totals_any_letters_and_refuses_others() {
    assert_eq!(from_roman("IIII"), Some(4));
    assert_eq!(from_roman("IM"), Some(999));
    assert_eq!(from_roman("MMMMMMMMMMMMMMM"), Some(15000));
    assert_eq!(from_roman(""), Some(0));
    assert_eq!(from_roman("XLZ"), None);
    assert_eq!(from_roman("xl"), None);
}

#[test]
fn canonical_is_the_round_trip() {
    for numeral in [
        "IIII",
        "IC",
        "VX",
        "XM",
        "MMMM",
        "IXIX",
        "",
        "M".repeat(40).as_str(),
    ] {
        assert_eq!(canonical(numeral), None, "{numeral}");
    }
}

#[test]
fn answers_in_the_rust_wording() {
    assert_eq!(answer("1990"), "MCMXC");
    assert_eq!(answer("MCMXC"), "1990");
    assert_eq!(answer(" 0042 "), "XLII");
    assert_eq!(answer("mcmxc"), "1990");
    assert_eq!(answer("+12"), "XII");
    assert_eq!(answer("4000"), "error: 4000 is not in 1-3999");
    assert_eq!(answer("-1"), "error: -1 is not in 1-3999");
    for line in ["IIII", "hello", "", "99999999999999999999", "٤٢"] {
        assert!(answer(line).starts_with("error: "), "{line:?}");
    }
}
