import { describe, expect, it } from 'bun:test';
import { bundle } from '../bundle';
import { highlight, highlightPython, type Token } from './highlight';

const kinds = (tokens: Token[]) => tokens.filter((t) => t.text.trim()).map((t) => [t.text, t.kind]);

describe('highlightPython', () => {
  it('classifies keywords, definitions, builtins, constants, numbers and comments', () => {
    const [line] = highlightPython('def f(x): return len(x) + 1.5 if x else None  # why');
    expect(kinds(line!)).toEqual([
      ['def', 'keyword'], ['f', 'definition'], ['(', 'plain'], ['x', 'plain'], [')', 'plain'], [':', 'plain'],
      ['return', 'keyword'], ['len', 'builtin'], ['(', 'plain'], ['x', 'plain'], [')', 'plain'],
      ['+', 'plain'], ['1.5', 'number'], ['if', 'keyword'], ['x', 'plain'], ['else', 'keyword'],
      ['None', 'constant'], ['# why', 'comment'],
    ]);
  });

  it('keeps string prefixes and escapes inside the string', () => {
    const [line] = highlightPython(`x = f"a{b}\\"c" + rb'd'`);
    expect(kinds(line!)).toEqual([
      ['x', 'plain'], ['=', 'plain'], ['f"a{b}\\"c"', 'string'], ['+', 'plain'], ["rb'd'", 'string'],
    ]);
  });

  it('splits a triple-quoted string across lines', () => {
    const lines = highlightPython('def f():\n    """One.\n\n    Two."""\n    return 1');
    expect(lines).toHaveLength(5);
    expect(kinds(lines[1]!)).toEqual([['"""One.', 'string']]);
    expect(lines[2]).toEqual([]);
    expect(lines[3]).toEqual([{ text: '    Two."""', kind: 'string' }]); // the indent is inside the string
    expect(kinds(lines[4]!)).toEqual([['return', 'keyword'], ['1', 'number']]);
  });

  it('marks decorators only at the start of a line', () => {
    expect(kinds(highlightPython('@dataclass(frozen=True)')[0]!)[0]).toEqual(['@dataclass', 'decorator']);
    expect(kinds(highlightPython('a @ b')[0]!)[1]).toEqual(['@', 'plain']);
  });

  it('treats match and case as keywords only when they open a block', () => {
    expect(kinds(highlightPython('match node:')[0]!)[0]).toEqual(['match', 'keyword']);
    expect(kinds(highlightPython('    case ("num", v):  # leaf')[0]!)[0]).toEqual(['case', 'keyword']);
    expect(kinds(highlightPython('match = pattern.match(s)')[0]!)[0]).toEqual(['match', 'plain']);
  });

  it('reproduces every corpus source exactly, line for line', () => {
    for (const program of bundle.programs) {
      for (const impl of program.impls) {
        const lines = highlight(impl.readSource, impl.lang);
        expect(lines.map((tokens) => tokens.map((t) => t.text).join(''))).toEqual(impl.readSource.split('\n'));
      }
    }
  });
});

describe('highlight (Rust)', () => {
  const rust = (source: string) => highlight(source, 'rust').map(kinds);

  it('classifies keywords, definitions, types, macros, constants and numbers', () => {
    expect(rust('pub fn roll(state: PigState, die: u64) -> Option<u8> { println!("{die}"); Some(1u8) }')[0]).toEqual([
      ['pub', 'keyword'], ['fn', 'keyword'], ['roll', 'definition'], ['(', 'plain'], ['state', 'plain'], [':', 'plain'],
      ['PigState', 'plain'], [',', 'plain'], ['die', 'plain'], [':', 'plain'], ['u64', 'builtin'], [')', 'plain'],
      ['-', 'plain'], ['>', 'plain'], ['Option', 'builtin'], ['<', 'plain'], ['u8', 'builtin'], ['>', 'plain'],
      ['{', 'plain'], ['println!', 'builtin'], ['(', 'plain'], ['"{die}"', 'string'], [')', 'plain'], [';', 'plain'],
      ['Some', 'constant'], ['(', 'plain'], ['1u8', 'number'], [')', 'plain'], ['}', 'plain'],
    ]);
  });

  it('tells chars from lifetimes, and reads raw and byte strings', () => {
    expect(rust("fn f<'a>(x: &'a str) -> char { 'x' }")[0]).toContainEqual(["'a", 'constant']);
    expect(rust("let c = b'\\n';")[0]).toContainEqual(["b'\\n'", 'string']);
    expect(rust('let s = r#"a "quoted" }"#;')[0]).toContainEqual(['r#"a "quoted" }"#', 'string']);
    expect(rust('b"hold" => 1,')[0]![0]).toEqual(['b"hold"', 'string']);
  });

  it('marks attributes, comments, and ranges without eating dots', () => {
    expect(rust('#[derive(Clone, Copy)]')[0]).toEqual([['#[derive(Clone, Copy)]', 'decorator']]);
    expect(rust('x /* a\nb */ y').map((line) => line.map(([, kind]) => kind))).toEqual([['plain', 'comment'], ['comment', 'plain']]);
    expect(rust('0..10')[0]).toEqual([['0', 'number'], ['.', 'plain'], ['.', 'plain'], ['10', 'number']]);
    expect(rust('if a != b {}')[0]![1]).toEqual(['a', 'plain']);
  });
});

describe('highlight (C)', () => {
  const c = (source: string) => highlight(source, 'c').map(kinds);

  it('marks directives and headers, function definitions, types and constants', () => {
    expect(c('#include <stdio.h>')[0]).toEqual([['#include', 'decorator'], [' <stdio.h>', 'string']]);
    expect(c('static int add(int a) { return printf("%d", a) ? 0 : EOF; }')[0]).toEqual([
      ['static', 'keyword'], ['int', 'builtin'], ['add', 'definition'], ['(', 'plain'], ['int', 'builtin'], ['a', 'plain'],
      [')', 'plain'], ['{', 'plain'], ['return', 'keyword'], ['printf', 'builtin'], ['(', 'plain'], ['"%d"', 'string'],
      [',', 'plain'], ['a', 'plain'], [')', 'plain'], ['?', 'plain'], ['0', 'number'], [':', 'plain'], ['EOF', 'constant'],
      [';', 'plain'], ['}', 'plain'],
    ]);
  });

  it('does not take the field after an anonymous struct for a definition', () => {
    expect(c('typedef struct {\n    int x;\n} P;')[1]).toEqual([['int', 'builtin'], ['x', 'plain'], [';', 'plain']]);
    expect(c("char c = '{';")[0]).toContainEqual(["'{'", 'string']);
  });
});
