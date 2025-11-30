import React from 'react';
import { getVerdictClass } from './utils';

/**
 * Verdict display component.
 *
 * @param {Object} props - Component props
 * @param {string} props.verdict - Analysis verdict
 * @param {string} [props.detail] - Detailed explanation
 * @param {string} [props.className=''] - Custom class name
 */
export const VerdictDisplay = ({
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
