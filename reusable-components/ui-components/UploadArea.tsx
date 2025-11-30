import React, { useRef, useState, useCallback } from 'react';
import type { UploadAreaProps } from './types';

/**
 * Upload area component with drag-and-drop support.
 *
 * Provides a user-friendly interface for file selection via
 * click or drag-and-drop.
 *
 * @example
 * ```tsx
 * <UploadArea
 *   onFileSelect={(files) => handleFiles(files)}
 *   acceptedTypes="audio/*"
 * />
 * ```
 */
export const UploadArea: React.FC<UploadAreaProps> = ({
  onFileSelect,
  acceptedTypes = 'audio/*',
  disabled = false,
  className = '',
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleClick = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled) {
        setIsDragging(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (!disabled && e.dataTransfer.files.length > 0) {
        onFileSelect(e.dataTransfer.files);
      }
    },
    [disabled, onFileSelect]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
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
