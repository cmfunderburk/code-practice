import { describe, expect, it } from 'bun:test';
import { parseInline } from './inline';

describe('parseInline', () => {
  it('parses code spans, emphasis, and nesting', () => {
    expect(parseInline('a `x*y` **b *c* e** d')).toEqual([
      { type: 'text', text: 'a ' },
      { type: 'code', text: 'x*y' },
      { type: 'text', text: ' ' },
      { type: 'bold', children: [{ type: 'text', text: 'b ' }, { type: 'italic', children: [{ type: 'text', text: 'c' }] }, { type: 'text', text: ' e' }] },
      { type: 'text', text: ' d' },
    ]);
  });

  it('leaves snake_case, lone stars and unclosed markers alone', () => {
    expect(parseInline('wrong_count and _read_line, 2 * 3, **open')).toEqual([
      { type: 'text', text: 'wrong_count and _read_line, 2 * 3, **open' },
    ]);
  });

  it('reduces links to their text', () => {
    expect(parseInline('see [the spec](SPEC.md) and [[notes|the notes]]')).toEqual([
      { type: 'text', text: 'see ' },
      { type: 'text', text: 'the spec' },
      { type: 'text', text: ' and the notes' },
    ]);
  });

  it('keeps emphasis markers inside code spans', () => {
    expect(parseInline('**`a**b`**')).toEqual([{ type: 'bold', children: [{ type: 'code', text: 'a**b' }] }]);
  });

  it('honours backslash escapes', () => {
    expect(parseInline('\\*not italic\\*')).toEqual([{ type: 'text', text: '*not italic*' }]);
  });
});
