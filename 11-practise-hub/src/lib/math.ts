/**
 * Splits a string by inline LaTeX delimiters \( ... \) and returns segments.
 * Each segment is either { type: 'text', value: string } or { type: 'math', value: string }.
 */
export function splitTextAndMath(str: string): Array< { type: 'text' | 'math'; value: string }> {
  if (!str || typeof str !== 'string') return [{ type: 'text', value: '' }];

  const segments: Array< { type: 'text' | 'math'; value: string }> = [];
  let i = 0;

  while (i < str.length) {
    const open = str.indexOf('\\(', i);
    if (open === -1) {
      segments.push({ type: 'text', value: str.slice(i) });
      break;
    }
    if (open > i) {
      segments.push({ type: 'text', value: str.slice(i, open) });
    }
    const close = str.indexOf('\\)', open + 2);
    if (close === -1) {
      // Unclosed \( — treat rest as text
      segments.push({ type: 'text', value: str.slice(open) });
      break;
    }
    segments.push({ type: 'math', value: str.slice(open + 2, close).trim() });
    i = close + 2;
  }

  return segments;
}
