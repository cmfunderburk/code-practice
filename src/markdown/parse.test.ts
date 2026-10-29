import { describe, expect, it } from 'bun:test';
import { bundle } from '../bundle';
import { parseMarkdown, splitRow } from './parse';

describe('parseMarkdown', () => {
  it('parses headings, paragraphs, rules and fenced code', () => {
    expect(parseMarkdown('# Title\n\nOne\ntwo.\n\n---\n\n```python\nx = 1\n\n  y\n```\nafter')).toEqual([
      { type: 'heading', level: 1, text: 'Title' },
      { type: 'paragraph', text: 'One two.' },
      { type: 'rule' },
      { type: 'code', lang: 'python', text: 'x = 1\n\n  y' },
      { type: 'paragraph', text: 'after' },
    ]);
  });

  it('nests lists by indentation and keeps item continuations', () => {
    const blocks = parseMarkdown('1. First\n   more\n   - sub a\n   - sub b\n2. Second\n\n   still second\n\nafter');
    expect(blocks).toEqual([
      {
        type: 'list', ordered: true, start: 1, items: [
          [
            { type: 'paragraph', text: 'First more' },
            { type: 'list', ordered: false, start: 1, items: [
              [{ type: 'paragraph', text: 'sub a' }],
              [{ type: 'paragraph', text: 'sub b' }],
            ] },
          ],
          [{ type: 'paragraph', text: 'Second' }, { type: 'paragraph', text: 'still second' }],
        ],
      },
      { type: 'paragraph', text: 'after' },
    ]);
  });

  it('parses folded callouts and plain quotes', () => {
    expect(parseMarkdown('> [!answer]-\n> 1. Yes.\n>\n> Because.\n\n> just a quote')).toEqual([
      {
        type: 'callout', kind: 'answer', title: 'Answer', folded: true, children: [
          { type: 'list', ordered: true, start: 1, items: [[{ type: 'paragraph', text: 'Yes.' }]] },
          { type: 'paragraph', text: 'Because.' },
        ],
      },
      { type: 'quote', children: [{ type: 'paragraph', text: 'just a quote' }] },
    ]);
    expect(parseMarkdown('> [!note]+ Committee prompt\n> Paste.')[0]).toMatchObject({
      type: 'callout', kind: 'note', title: 'Committee prompt', folded: false,
    });
  });

  it('parses pipe tables, with escaped pipes inside cells', () => {
    expect(parseMarkdown('| Guess | Output |\n| --- | --- |\n| `a\\|b` | clue |\nafter')).toEqual([
      { type: 'table', header: ['Guess', 'Output'], rows: [['`a|b`', 'clue']] },
      { type: 'paragraph', text: 'after' },
    ]);
    expect(splitRow('a | b')).toEqual(['a', 'b']);
  });

  it('parses every corpus document without losing a fence', () => {
    for (const program of bundle.programs) {
      const docs = [program.docs.spec, program.docs.defense, ...program.impls.flatMap((i) => [i.docs.problem, i.docs.notes])];
      for (const doc of docs) {
        const fences = doc.split('\n').filter((line) => /^\s*```/.test(line)).length;
        const count = (blocks: ReturnType<typeof parseMarkdown>): number => blocks.reduce((n, b) =>
          n + (b.type === 'code' ? 1 : b.type === 'list' ? b.items.reduce((m, item) => m + count(item), 0)
            : b.type === 'quote' || b.type === 'callout' ? count(b.children) : 0), 0);
        expect(count(parseMarkdown(doc))).toBe(fences / 2);
      }
    }
  });
});
