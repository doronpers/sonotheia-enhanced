import React from 'react';

/**
 * Error display component.
 *
 * @param {Object} props - Component props
 * @param {string} props.error - Error message
 * @param {Function} [props.onReset] - Callback to reset/dismiss error
 * @param {string} [props.className=''] - Custom class name
 */
export const ErrorDisplay = ({
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
