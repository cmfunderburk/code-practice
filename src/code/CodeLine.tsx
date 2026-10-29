import type { Token } from './highlight';

/** One source line. Its indent becomes padding, so a long line wraps with a
 * hanging indent under its own code instead of back at the margin. */
export function CodeLine({ tokens, indent, className = '', ...rest }: {
  tokens: Token[];
  indent: number;
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>) {
  let skip = indent;
  const shown: Token[] = [];
  for (const token of tokens) {
    if (skip > 0) {
      const cut = Math.min(skip, token.text.length - token.text.trimStart().length);
      skip -= cut;
      if (cut === token.text.length) continue;
      shown.push({ ...token, text: token.text.slice(cut) });
    } else {
      shown.push(token);
    }
  }
  return (
    <div className={`code-line ${className}`} style={{ '--indent': `${indent}ch` } as React.CSSProperties} {...rest}>
      {shown.length === 0 ? ' ' : shown.map((token, i) =>
        token.kind === 'plain' ? token.text : <span key={i} className={`tk-${token.kind}`}>{token.text}</span>,
      )}
    </div>
  );
}
