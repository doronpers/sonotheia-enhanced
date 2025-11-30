import React from 'react';
import type { LoadingSpinnerProps } from './types';

/**
 * Loading spinner component.
 *
 * Displays an animated spinner with optional message.
 *
 * @example
 * ```tsx
 * <LoadingSpinner message="Analyzing audio..." />
 * ```
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Analyzing...',
  className = '',
}) => {
  const classes = ['spinner-container', className].filter(Boolean).join(' ');

  return (
    <div className={classes} role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      {message && <p className="spinner-message">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;
