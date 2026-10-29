// Inline Markdown: code spans, **bold**, *italic*, ~~strike~~, ==highlight==,
// and links reduced to their text ([text](url), [[target|alias]]). The docs'
// links point at sibling files the app doesn't have, so none are followed.

export type Inline =
  | { type: 'text'; text: string }
  | { type: 'code'; text: string }
  | { type: 'bold' | 'italic' | 'strike' | 'highlight'; children: Inline[] };

const DELIMITERS: [string, 'bold' | 'italic' | 'strike' | 'highlight'][] = [
  ['**', 'bold'],
  ['__', 'bold'],
  ['~~', 'strike'],
  ['==', 'highlight'],
  ['*', 'italic'],
  ['_', 'italic'],
];

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  let plain = '';
  const flush = () => {
    if (plain) out.push({ type: 'text', text: plain });
    plain = '';
  };

  let i = 0;
  outer: while (i < text.length) {
    const ch = text[i]!;
    const rest = text.slice(i);

    if (ch === '\\' && /[\\`*_{}[\]()#+\-.!|~=<>]/.test(text[i + 1] ?? '')) {
      plain += text[i + 1];
      i += 2;
      continue;
    }

    if (ch === '`') {
      const run = rest.match(/^`+/)![0];
      const end = text.indexOf(run, i + run.length);
      if (end > 0) {
        flush();
        const code = text.slice(i + run.length, end);
        out.push({ type: 'code', text: run.length > 1 ? code.trim() : code });
        i = end + run.length;
        continue;
      }
      plain += run;
      i += run.length;
      continue;
    }

    const wiki = rest.match(/^\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]/);
    if (wiki) {
      plain += wiki[2] ?? wiki[1];
      i += wiki[0].length;
      continue;
    }

    const link = rest.match(/^!?\[([^\]]*)\]\([^)]*\)/);
    if (link) {
      flush();
      out.push(...parseInline(link[1]!));
      i += link[0].length;
      continue;
    }

    for (const [marker, type] of DELIMITERS) {
      if (!rest.startsWith(marker)) continue;
      const after = text[i + marker.length];
      // An opener is followed by non-space; `_` must not sit inside a word (snake_case).
      if (!after || /\s/.test(after)) break;
      if (marker[0] === '_' && /\w/.test(text[i - 1] ?? '')) break;
      const close = findCloser(text, i + marker.length, marker);
      if (close < 0) break;
      flush();
      out.push({ type, children: parseInline(text.slice(i + marker.length, close)) });
      i = close + marker.length;
      continue outer;
    }

    plain += ch;
    i += 1;
  }
  flush();
  return out;
}

/** The index of the marker closing one opened before `from`, skipping code spans. */
function findCloser(text: string, from: number, marker: string): number {
  let i = from;
  while (i < text.length) {
    if (text[i] === '`') {
      const run = text.slice(i).match(/^`+/)![0];
      const end = text.indexOf(run, i + run.length);
      i = end < 0 ? i + run.length : end + run.length;
      continue;
    }
    if (text.startsWith(marker, i) && !/\s/.test(text[i - 1] ?? ' ')) {
      // `*` must not be the start of `**`, and `_` must not sit inside a word.
      const single = marker.length === 1;
      if (single && text[i + 1] === marker) {
        i += 2;
        continue;
      }
      if (marker[0] === '_' && /\w/.test(text[i + marker.length] ?? '')) {
        i += 1;
        continue;
      }
      return i;
    }
    i += 1;
  }
  return -1;
}
