import React from 'react';

/**
 * Loading spinner component.
 *
 * @param {Object} props - Component props
 * @param {string} [props.message='Analyzing...'] - Message to display
 * @param {string} [props.className=''] - Custom class name
 */
export const LoadingSpinner = ({
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
