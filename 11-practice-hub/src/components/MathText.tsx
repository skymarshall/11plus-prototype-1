import { useMemo } from 'react';
import katex from 'katex';
import { splitTextAndMath } from '@/lib/math';
import 'katex/dist/katex.min.css';

const MAX_MATH_LENGTH = 500;

interface MathTextProps {
  /** Text that may contain inline LaTeX in \( ... \) */
  children: string;
  className?: string;
  component?: keyof JSX.IntrinsicElements;
}

/**
 * Renders text with optional inline LaTeX. Plain text is escaped; segments inside \( ... \) are rendered with KaTeX.
 */
export function MathText({ children, className, component: Component = 'span' }: MathTextProps) {
  const safeText = children ?? '';
  const segments = useMemo(() => splitTextAndMath(safeText), [safeText]);

  const nodes = useMemo(() => {
    return segments.map((seg, i) => {
      if (seg.type === 'text') {
        return <span key={i}>{seg.value}</span>;
      }
      if (seg.value.length > MAX_MATH_LENGTH) {
        return <span key={i} className="text-destructive">[Math too long]</span>;
      }
      try {
        const html = katex.renderToString(seg.value, {
          throwOnError: false,
          displayMode: false,
          output: 'html',
        });
        return (
          <span
            key={i}
            className="katex-inline"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        );
      } catch {
        return <span key={i} className="text-destructive">[Invalid math]</span>;
      }
    });
  }, [segments]);

  return <Component className={className}>{nodes}</Component>;
}
