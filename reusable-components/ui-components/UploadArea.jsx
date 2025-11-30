import React, { useRef, useState, useCallback } from 'react';

/**
 * Upload area component with drag-and-drop support.
 *
 * @param {Object} props - Component props
 * @param {Function} props.onFileSelect - Callback when files are selected
 * @param {string} [props.acceptedTypes='audio/*'] - Accepted file types
 * @param {boolean} [props.disabled=false] - Whether upload is disabled
 * @param {string} [props.className=''] - Custom class name
 */
export const UploadArea = ({
  onFileSelect,
  acceptedTypes = 'audio/*',
  disabled = false,
  className = '',
}) => {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleClick = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  const handleDragOver = useCallback(
    (e) => {
      e.preventDefault();
      if (!disabled) {
        setIsDragging(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      if (!disabled && e.dataTransfer.files.length > 0) {
        onFileSelect(e.dataTransfer.files);
      }
    },
    [disabled, onFileSelect]
  );

  const handleChange = useCallback(
    (e) => {
      if (e.target.files && e.target.files.length > 0) {
        onFileSelect(e.target.files);
      }
    },
    [onFileSelect]
  );

  const baseClass = 'upload-area';
  const stateClass = isDragging ? 'dragging' : '';
  const disabledClass = disabled ? 'disabled' : '';
  const classes = [baseClass, stateClass, disabledClass, className]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={classes}
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label="Upload file"
    >
      <div className="upload-instructions">
        <p className="upload-title">UPLOAD FILE</p>
        <span className="upload-subtitle">Drag &amp; Drop or Click to Select</span>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={acceptedTypes}
        hidden
        onChange={handleChange}
        disabled={disabled}
      />
    </div>
  );
};

export default UploadArea;
