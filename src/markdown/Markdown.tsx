import { Fragment, useMemo, type ReactNode } from 'react';
import { CodeLine } from '../code/CodeLine';
import { highlight } from '../code/highlight';
import { parseInline, type Inline } from './inline';
import { parseMarkdown, type Block } from './parse';

function renderInline(nodes: Inline[]): ReactNode {
  return nodes.map((node, i) => {
    switch (node.type) {
      case 'text': return <Fragment key={i}>{node.text}</Fragment>;
      case 'code': return <code key={i}>{node.text}</code>;
      case 'bold': return <strong key={i}>{renderInline(node.children)}</strong>;
      case 'italic': return <em key={i}>{renderInline(node.children)}</em>;
      case 'strike': return <s key={i}>{renderInline(node.children)}</s>;
      case 'highlight': return <mark key={i}>{renderInline(node.children)}</mark>;
    }
  });
}

const inline = (text: string) => renderInline(parseInline(text));

function CodeBlock({ lang, text }: { lang: string; text: string }) {
  const lines = useMemo(() => highlight(text, lang), [text, lang]);
  return (
    <div className="md-code">
      {lines.map((tokens, i) => {
        const line = tokens.map((t) => t.text).join('');
        return <CodeLine key={i} tokens={tokens} indent={line.length - line.trimStart().length} />;
      })}
    </div>
  );
}

function renderBlocks(blocks: Block[]): ReactNode {
  return blocks.map((block, i) => {
    switch (block.type) {
      case 'heading': {
        const Tag = `h${Math.min(block.level + 1, 6)}` as 'h2';
        return <Tag key={i}>{inline(block.text)}</Tag>;
      }
      case 'paragraph': return <p key={i}>{inline(block.text)}</p>;
      case 'code': return <CodeBlock key={i} lang={block.lang} text={block.text} />;
      case 'rule': return <hr key={i} />;
      case 'quote': return <blockquote key={i}>{renderBlocks(block.children)}</blockquote>;
      case 'list': {
        const items = block.items.map((item, j) => <li key={j}>{renderBlocks(item)}</li>);
        return block.ordered ? <ol key={i} start={block.start}>{items}</ol> : <ul key={i}>{items}</ul>;
      }
      case 'table':
        return (
          <div key={i} className="md-table">
            <table>
              <thead><tr>{block.header.map((cell, j) => <th key={j}>{inline(cell)}</th>)}</tr></thead>
              <tbody>
                {block.rows.map((row, j) => <tr key={j}>{row.map((cell, k) => <td key={k}>{inline(cell)}</td>)}</tr>)}
              </tbody>
            </table>
          </div>
        );
      case 'callout': {
        const className = `md-callout md-callout-${block.kind}`;
        if (block.folded === null) {
          return (
            <div key={i} className={className}>
              <div className="md-callout-title">{inline(block.title)}</div>
              {renderBlocks(block.children)}
            </div>
          );
        }
        return (
          <details key={i} className={className} open={!block.folded}>
            <summary className="md-callout-title">{inline(block.title)}</summary>
            {renderBlocks(block.children)}
          </details>
        );
      }
    }
  });
}

export function Markdown({ source }: { source: string }) {
  const blocks = useMemo(() => parseMarkdown(source), [source]);
  return <div className="markdown">{renderBlocks(blocks)}</div>;
}
