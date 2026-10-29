use super::*;

fn int(text: &str) -> i64 {
    match calculate(text) {
        Ok(Value::Int(v)) => v,
        other => panic!("{text}: {other:?}"),
    }
}

fn float(text: &str) -> f64 {
    match calculate(text) {
        Ok(Value::Float(v)) => v,
        other => panic!("{text}: {other:?}"),
    }
}

#[test]
fn precedence_parentheses_and_left_associativity() {
    assert_eq!(int("2+3*4"), 14);
    assert_eq!(int("(2+3)*4"), 20);
    assert_eq!(int("20-5-3"), 12);
    assert_eq!(int("2-3+4"), 3);
    assert_eq!(float("100/5/2"), 10.0);
}

#[test]
fn unary_minus_nests() {
    assert_eq!(int("--3"), 3);
    assert_eq!(int("2*-3"), -6);
    assert_eq!(int("-(2+3)"), -5);
    assert_eq!(int("2--3"), 5);
}

#[test]
fn integers_stay_integers_and_division_is_true_division() {
    assert_eq!(calculate("2+3"), Ok(Value::Int(5)));
    assert_eq!(float("7/2"), 3.5);
    assert_eq!(float("8/2"), 4.0);
    assert_eq!(float("7/2*2"), 7.0);
    assert!((float("1/3") - 1.0 / 3.0).abs() < 1e-15);
}

#[test]
fn spaces_tabs_and_leading_zeros() {
    assert_eq!(int("  2 +\t3 "), 5);
    assert_eq!(int("007+1"), 8);
}

#[test]
fn division_by_zero_is_an_error() {
    for text in ["1/0", "0/0", "1/(1/2-1/2)"] {
        assert!(calculate(text).is_err(), "{text}");
    }
}

#[test]
fn lines_outside_the_grammar_are_errors() {
    for text in [
        "", "   ", "2+", "(2", "2)*3", "1 2", "2^3", "*3", "()", "2//3", "2 + x", "２+1",
    ] {
        assert!(calculate(text).is_err(), "{text:?}");
    }
}

#[test]
fn i64_overflow_is_an_error_not_a_panic() {
    assert_eq!(int("9223372036854775807"), i64::MAX);
    assert!(calculate("9223372036854775808").is_err());
    assert!(calculate("9223372036854775807+1").is_err());
    assert!(calculate("-9223372036854775807-2").is_err());
}
