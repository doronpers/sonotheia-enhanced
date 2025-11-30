import React from 'react';
import type { VerdictDisplayProps } from './types';
import { getVerdictClass } from './utils';

/**
 * Verdict display component.
 *
 * Shows analysis verdict with color coding and optional details.
 *
 * @example
 * ```tsx
 * <VerdictDisplay
 *   verdict="REAL"
 *   detail="All physics checks passed."
 * />
 * ```
 */
export const VerdictDisplay: React.FC<VerdictDisplayProps> = ({
  verdict,
  detail,
  className = '',
}) => {
  const verdictClass = getVerdictClass(verdict);
  const classes = ['verdict-section', verdictClass, className]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} role="status" aria-live="polite">
      <p className="verdict-label">Verdict</p>
      <p className="verdict-text">{verdict}</p>
      {detail && <p className="verdict-detail">{detail}</p>}
    </div>
  );
};

export default VerdictDisplay;
