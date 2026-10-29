// Syntax highlighting by a small hand-written tokenizer: enough classes to read
// code comfortably (keywords, strings, comments, numbers, names being defined),
// not a parser. It runs over a whole source so strings can span lines, and
// returns the tokens line by line.

export type TokenKind = 'plain' | 'keyword' | 'constant' | 'builtin' | 'string' | 'comment' | 'number' | 'decorator' | 'definition';

export interface Token {
  text: string;
  kind: TokenKind;
}

const PY_KEYWORDS = new Set([
  'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else',
  'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
  'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
]);
// Keywords only when they open a line that ends in a colon; elsewhere they're names.
const PY_SOFT_KEYWORDS = new Set(['match', 'case']);
const PY_CONSTANTS = new Set(['True', 'False', 'None', 'self', 'cls']);
const PY_BUILTINS = new Set([
  'abs', 'all', 'any', 'bool', 'bytes', 'callable', 'dict', 'divmod', 'enumerate', 'filter', 'float',
  'frozenset', 'getattr', 'hasattr', 'hash', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
  'list', 'map', 'max', 'min', 'next', 'object', 'open', 'ord', 'chr', 'print', 'range', 'repr',
  'reversed', 'round', 'set', 'setattr', 'sorted', 'str', 'sum', 'super', 'tuple', 'type', 'zip',
  'ValueError', 'KeyError', 'IndexError', 'TypeError', 'Exception', 'StopIteration', 'EOFError',
  'RuntimeError', 'NotImplementedError', 'AssertionError',
]);

// A string's opening: optional prefix letters, then a triple or single quote.
const PY_STRING_START = /^([rRbBuUfF]{0,2})("""|'''|"|')/;
const PY_NUMBER = /^(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|(?:\d[\d_]*)?\.?\d[\d_]*(?:[eE][+-]?\d+)?j?)/;
const IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_]*/;

/** Lines of tokens, and a push that splits multi-line tokens (strings, block comments)
 * across lines. */
function tokenLines(): [Token[][], (text: string, kind: TokenKind) => void] {
  const lines: Token[][] = [[]];
  let current = lines[0]!;
  const push = (text: string, kind: TokenKind) => {
    const pieces = text.split('\n');
    pieces.forEach((piece, i) => {
      if (i > 0) {
        current = [];
        lines.push(current);
      }
      if (piece) current.push({ text: piece, kind });
    });
  };
  return [lines, push];
}

/** Tokens per line of `source` (split on \n), for Python. */
export function highlightPython(source: string): Token[][] {
  const [lines, push] = tokenLines();

  let i = 0;
  let defining = false; // the previous word was `def` or `class`
  let lineStart = true; // only whitespace so far on this line
  while (i < source.length) {
    const rest = source.slice(i);
    const ch = source[i]!;

    if (ch === '\n') {
      push('\n', 'plain');
      lineStart = true;
      i += 1;
      continue;
    }
    if (ch === '#') {
      const end = source.indexOf('\n', i);
      const text = end < 0 ? rest : source.slice(i, end);
      push(text, 'comment');
      i += text.length;
      continue;
    }
    const string = rest.match(PY_STRING_START);
    if (string) {
      const quote = string[2]!;
      let j = string[0].length;
      while (j < rest.length) {
        if (rest[j] === '\\') j += 2;
        else if (rest.startsWith(quote, j)) {
          j += quote.length;
          break;
        } else if (rest[j] === '\n' && quote.length === 1) break; // unterminated
        else j += 1;
      }
      push(rest.slice(0, j), 'string');
      i += j;
      lineStart = false;
      continue;
    }
    if (ch === '@' && lineStart) {
      const name = rest.slice(1).match(/^[A-Za-z_][\w.]*/);
      const text = '@' + (name?.[0] ?? '');
      push(text, 'decorator');
      i += text.length;
      lineStart = false;
      continue;
    }
    const word = rest.match(IDENTIFIER);
    if (word) {
      const text = word[0];
      let kind: TokenKind = 'plain';
      if (defining) kind = 'definition';
      else if (PY_KEYWORDS.has(text)) kind = 'keyword';
      else if (PY_SOFT_KEYWORDS.has(text) && lineStart && opensBlock(rest)) kind = 'keyword';
      else if (PY_CONSTANTS.has(text)) kind = 'constant';
      else if (PY_BUILTINS.has(text)) kind = 'builtin';
      defining = text === 'def' || text === 'class';
      push(text, kind);
      i += text.length;
      lineStart = false;
      continue;
    }
    if (/\d/.test(ch) || (ch === '.' && /\d/.test(source[i + 1] ?? ''))) {
      const text = rest.match(PY_NUMBER)?.[0] || ch;
      push(text, 'number');
      i += text.length;
      lineStart = false;
      continue;
    }
    push(ch, 'plain');
    if (ch !== ' ' && ch !== '\t') lineStart = false;
    i += 1;
  }
  return lines;
}

/** Whether the line starting at `rest` ends in a colon (ignoring a trailing comment). */
function opensBlock(rest: string): boolean {
  const line = rest.split('\n', 1)[0]!.replace(/#.*$/, '');
  return line.trimEnd().endsWith(':');
}

interface BraceLang {
  keywords: Set<string>;
  constants: Set<string>;
  builtins: Set<string>;
  /** Words whose next name is being defined. */
  definers: Set<string>;
  rust: boolean;
}

const words = (text: string) => new Set(text.split(/\s+/).filter(Boolean));

const RUST: BraceLang = {
  keywords: words(`as async await break const continue crate dyn else enum extern fn for if impl in let loop
    match mod move mut pub ref return static struct super trait type union unsafe use where while`),
  constants: words('true false self Self None Some Ok Err'),
  builtins: words(`u8 u16 u32 u64 u128 usize i8 i16 i32 i64 i128 isize f32 f64 bool char str String Vec
    Option Result Box Rc RefCell HashMap HashSet BTreeMap BTreeSet VecDeque`),
  definers: words('fn struct enum trait type mod union'),
  rust: true,
};

const C: BraceLang = {
  keywords: words(`auto break case const constexpr continue default do else enum extern for goto if inline
    register restrict return sizeof static static_assert struct switch typedef typeof union volatile while`),
  constants: words('true false nullptr NULL EOF EXIT_SUCCESS EXIT_FAILURE stdin stdout stderr'),
  builtins: words(`void char short int long float double signed unsigned bool size_t ptrdiff_t
    int8_t int16_t int32_t int64_t uint8_t uint16_t uint32_t uint64_t intmax_t uintmax_t char32_t FILE
    printf fprintf snprintf puts fputs putchar getchar fgets malloc calloc realloc free exit
    memcpy memmove memcmp memset strlen strcmp strncmp strchr strcpy isdigit isspace isalpha toupper tolower`),
  definers: words('struct enum union'),
  rust: false,
};

const BRACE_NUMBER = /^(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?)\w*/;
const RUST_CHAR = /^b?'(?:\\(?:u\{[0-9a-fA-F]+\}|x[0-9a-fA-F]{2}|.)|[^\\'\n])'/;
const C_CHAR = /^'(?:\\.|[^\\'\n])+'/;
const RUST_RAW = /^b?r(#*)"/;

/** Tokens per line of `source`, for Rust or C. */
export function highlightBraces(source: string, lang: BraceLang): Token[][] {
  const [lines, push] = tokenLines();
  let i = 0;
  let defining = false;  // the previous word was a definer (`fn`, `struct`, ...)
  let lineStart = true;
  let depth = 0;         // braces open, for spotting C function definitions
  while (i < source.length) {
    const rest = source.slice(i);
    const ch = source[i]!;
    const take = (text: string, kind: TokenKind) => {
      push(text, kind);
      i += text.length;
      lineStart = text.endsWith('\n');
    };

    if (ch === '\n') {
      take('\n', 'plain');
      continue;
    }
    if (rest.startsWith('//')) {
      const end = source.indexOf('\n', i);
      take(end < 0 ? rest : source.slice(i, end), 'comment');
      continue;
    }
    if (rest.startsWith('/*')) {
      const end = source.indexOf('*/', i + 2);
      take(end < 0 ? rest : source.slice(i, end + 2), 'comment');
      continue;
    }
    if (ch === '#' && lineStart) {
      // A Rust attribute to its closing bracket, or a C directive word.
      const text = lang.rust ? (rest.match(/^#!?\[[^\n]*\](?=[ \t]*(?:\/\/|\n|$))/)?.[0] ?? '#') : (rest.match(/^#\s*\w+/)?.[0] ?? '#');
      take(text, 'decorator');
      if (!lang.rust) {
        const header = source.slice(i).match(/^\s*<[^>\n]*>/);
        if (header) take(header[0], 'string');
      }
      continue;
    }
    const raw = lang.rust && !/\w/.test(source[i - 1] ?? '') ? rest.match(RUST_RAW) : null;
    if (raw) {
      const close = '"' + raw[1]!;
      const end = source.indexOf(close, i + raw[0].length);
      take(end < 0 ? rest : source.slice(i, end + close.length), 'string');
      continue;
    }
    if (ch === '"' || (lang.rust && rest.startsWith('b"'))) {
      let j = ch === '"' ? 1 : 2;
      while (j < rest.length && rest[j] !== '"') j += rest[j] === '\\' ? 2 : 1;
      take(rest.slice(0, j + 1), 'string');
      continue;
    }
    if (ch === "'" || (lang.rust && rest.startsWith("b'"))) {
      const char = rest.match(lang.rust ? RUST_CHAR : C_CHAR);
      if (char) {
        take(char[0], 'string');
        continue;
      }
      // A Rust lifetime or loop label.
      const lifetime = rest.match(/^'\w+/);
      if (lifetime) {
        take(lifetime[0], 'constant');
        continue;
      }
    }
    const word = rest.match(IDENTIFIER);
    if (word) {
      const text = word[0];
      const after = source.slice(i + text.length);
      let kind: TokenKind = 'plain';
      if (defining) kind = 'definition';
      else if (lang.keywords.has(text)) kind = 'keyword';
      else if (lang.constants.has(text)) kind = 'constant';
      else if (lang.rust && /^![^=]/.test(after)) {
        take(text + '!', 'builtin');  // a macro
        defining = false;
        continue;
      } else if (!lang.rust && depth === 0 && /^\s*\(/.test(after) && !lang.builtins.has(text)) kind = 'definition';
      else if (lang.builtins.has(text)) kind = 'builtin';
      defining = lang.definers.has(text);
      take(text, kind);
      continue;
    }
    if (/\d/.test(ch)) {
      take(rest.match(BRACE_NUMBER)![0], 'number');
      continue;
    }
    if (ch === '{') depth += 1;
    else if (ch === '}') depth = Math.max(0, depth - 1);
    push(ch, 'plain');
    if (ch !== ' ' && ch !== '\t') lineStart = defining = false;
    i += 1;
  }
  return lines;
}

export function highlight(source: string, lang: string): Token[][] {
  if (lang === 'python') return highlightPython(source);
  if (lang === 'rust') return highlightBraces(source, RUST);
  if (lang === 'c') return highlightBraces(source, C);
  return source.split('\n').map((line) => (line ? [{ text: line, kind: 'plain' as const }] : []));
}
