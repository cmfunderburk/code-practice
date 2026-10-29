// Markdown to blocks, covering what the corpus's docs use: headings,
// paragraphs, fenced code, nested lists, block quotes, pipe tables, rules, and
// Obsidian callouts (`> [!answer]- Title`, folded when the sign is `-`).
// Inline syntax is left in the text for the renderer (Markdown.tsx).

export type Block =
  | { type: 'heading'; level: number; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'code'; lang: string; text: string }
  | { type: 'list'; ordered: boolean; start: number; items: Block[][] }
  | { type: 'quote'; children: Block[] }
  | { type: 'callout'; kind: string; title: string; folded: boolean | null; children: Block[] }
  | { type: 'table'; header: string[]; rows: string[][] }
  | { type: 'rule' };

const FENCE = /^(\s*)(`{3,}|~{3,})\s*([\w+-]*)/;
const HEADING = /^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$/;
const RULE = /^ {0,3}([-*_])(?:\s*\1){2,}\s*$/;
const QUOTE = /^ {0,3}> ?/;
const LIST_ITEM = /^(\s*)([-*+]|\d{1,9}[.)])(?:\s+(.*))?$/;
const TABLE_DIVIDER = /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$/;
const CALLOUT_HEADER = /^\[!([\w-]+)\]([-+]?)\s*(.*)$/;

const indentOf = (line: string) => line.length - line.trimStart().length;
const isBlank = (line: string) => !line.trim();

function isTableStart(lines: string[], i: number): boolean {
  return (lines[i] ?? '').includes('|') && TABLE_DIVIDER.test(lines[i + 1] ?? '');
}

function startsBlock(lines: string[], i: number): boolean {
  const line = lines[i]!;
  return FENCE.test(line) || HEADING.test(line) || RULE.test(line) || QUOTE.test(line) ||
    LIST_ITEM.test(line) || isTableStart(lines, i);
}

export function splitRow(line: string): string[] {
  const cells = line.trim().replace(/^\|/, '').replace(/(?<!\\)\|$/, '').split(/(?<!\\)\|/);
  return cells.map((cell) => cell.trim().replace(/\\\|/g, '|'));
}

export function parseMarkdown(source: string): Block[] {
  return parseLines(source.replace(/\r\n?/g, '\n').split('\n'));
}

function parseLines(lines: string[]): Block[] {
  const blocks: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i]!;
    if (isBlank(line)) {
      i += 1;
      continue;
    }

    const fence = line.match(FENCE);
    if (fence) {
      const [, indent, marker, lang] = fence;
      const body: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i]!.trimStart().startsWith(marker!)) {
        body.push(lines[i]!.slice(Math.min(indent!.length, indentOf(lines[i]!))));
        i += 1;
      }
      i += 1; // the closing fence
      blocks.push({ type: 'code', lang: lang ?? '', text: body.join('\n') });
      continue;
    }

    const heading = line.match(HEADING);
    if (heading) {
      blocks.push({ type: 'heading', level: heading[1]!.length, text: heading[2]! });
      i += 1;
      continue;
    }

    if (RULE.test(line)) {
      blocks.push({ type: 'rule' });
      i += 1;
      continue;
    }

    if (QUOTE.test(line)) {
      const inner: string[] = [];
      while (i < lines.length && QUOTE.test(lines[i]!)) {
        inner.push(lines[i]!.replace(QUOTE, ''));
        i += 1;
      }
      const callout = inner[0]!.match(CALLOUT_HEADER);
      if (callout) {
        const [, kind, sign, title] = callout;
        blocks.push({
          type: 'callout',
          kind: kind!.toLowerCase(),
          title: title || kind!.charAt(0).toUpperCase() + kind!.slice(1),
          folded: sign === '-' ? true : sign === '+' ? false : null,
          children: parseLines(inner.slice(1)),
        });
      } else {
        blocks.push({ type: 'quote', children: parseLines(inner) });
      }
      continue;
    }

    if (isTableStart(lines, i)) {
      const header = splitRow(line);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && lines[i]!.includes('|') && !isBlank(lines[i]!)) {
        rows.push(splitRow(lines[i]!));
        i += 1;
      }
      blocks.push({ type: 'table', header, rows });
      continue;
    }

    const item = line.match(LIST_ITEM);
    if (item) {
      const [list, next] = parseList(lines, i);
      blocks.push(list);
      i = next;
      continue;
    }

    const paragraph: string[] = [];
    while (i < lines.length && !isBlank(lines[i]!) && (paragraph.length === 0 || !startsBlock(lines, i))) {
      paragraph.push(lines[i]!.trim());
      i += 1;
    }
    blocks.push({ type: 'paragraph', text: paragraph.join(' ') });
  }
  return blocks;
}

/** A list starting at line `start`, and the line after it. Lines indented past an item's
 * marker belong to it (nested lists, continuation paragraphs, code), as do unindented
 * lines continuing its text. */
function parseList(lines: string[], start: number): [Block, number] {
  const first = lines[start]!.match(LIST_ITEM)!;
  const markerIndent = first[1]!.length;
  const ordered = /\d/.test(first[2]!);
  const items: Block[][] = [];
  let i = start;
  while (i < lines.length) {
    const match = lines[i]!.match(LIST_ITEM);
    if (!match || match[1]!.length !== markerIndent || /\d/.test(match[2]!) !== ordered) break;
    const contentIndent = markerIndent + match[2]!.length + 1;
    const body = [match[3] ?? ''];
    i += 1;
    while (i < lines.length) {
      const line = lines[i]!;
      if (isBlank(line)) {
        // A blank line continues the item only if the item goes on after it.
        let j = i + 1;
        while (j < lines.length && isBlank(lines[j]!)) j += 1;
        if (j < lines.length && indentOf(lines[j]!) > markerIndent) {
          body.push(...lines.slice(i, j).map(() => ''));
          i = j;
          continue;
        }
        break;
      }
      if (indentOf(line) > markerIndent) {
        body.push(line.slice(Math.min(contentIndent, indentOf(line))));
      } else if (!isBlank(body[body.length - 1]!) && !startsBlock(lines, i)) {
        body.push(line.trim()); // lazy continuation of the item's text
      } else {
        break;
      }
      i += 1;
    }
    items.push(parseLines(body));
  }
  return [{ type: 'list', ordered, start: ordered ? parseInt(first[2]!, 10) : 1, items }, i];
}
