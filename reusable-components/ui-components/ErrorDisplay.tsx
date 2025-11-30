import React from 'react';
import type { ErrorDisplayProps } from './types';

/**
 * Error display component.
 *
 * Shows error message with optional reset button.
 *
 * @example
 * ```tsx
 * <ErrorDisplay
 *   error="Failed to process file"
 *   onReset={() => setError('')}
 * />
 * ```
 */
export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onReset,
  className = '',
}) => {
  const classes = ['error-display', className].filter(Boolean).join(' ');

  return (
    <div className={classes} role="alert">
      <p className="error-message">{error}</p>
      {onReset && (
        <button
          className="error-reset-button"
          onClick={onReset}
          type="button"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorDisplay;
