/**
 * Utility functions for UI components.
 * JavaScript version - no types required.
 */

/**
 * Build API URL from base URL and endpoint.
 *
 * @param {string|undefined} baseUrl - Base URL (may be empty for relative URLs)
 * @param {string} endpoint - API endpoint path
 * @returns {string} Full API URL
 */
export function buildApiUrl(baseUrl, endpoint) {
  const base = baseUrl && baseUrl.length > 0 ? baseUrl.replace(/\/$/, '') : '';
  return `${base}${endpoint}`;
}

/**
 * Format evidence data into display rows.
 *
 * @param {Object} evidence - Dictionary of sensor evidence
 * @returns {Array} Array of formatted evidence rows
 */
export function formatEvidence(evidence) {
  return Object.entries(evidence)
    .filter(([_, value]) => value !== null && value !== undefined)
    .map(([key, value]) => ({
      label: formatLabel(key),
      value: value.detail || `${value.value} (threshold: ${value.threshold})`,
      status: getStatus(value.passed),
    }));
}

/**
 * Format a snake_case key into Title Case label.
 *
 * @param {string} key - Key to format
 * @returns {string} Formatted label
 */
export function formatLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Get status string from pass/fail value.
 *
 * @param {boolean|null} passed - Pass/fail/null value
 * @returns {string} Status string
 */
function getStatus(passed) {
  if (passed === true) return 'pass';
  if (passed === false) return 'fail';
  return 'info';
}

/**
 * Format file size in human-readable format.
 *
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted string
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Format duration in human-readable format.
 *
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted string
 */
export function formatDuration(seconds) {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}

/**
 * Format processing time for display.
 *
 * @param {number} seconds - Processing time in seconds
 * @returns {string} Formatted string
 */
export function formatProcessingTime(seconds) {
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`;
  }
  return `${seconds.toFixed(2)}s`;
}

/**
 * Get CSS class for verdict type.
 *
 * @param {string} verdict - Analysis verdict
 * @returns {string} CSS class name
 */
export function getVerdictClass(verdict) {
  return `verdict-${verdict}`;
}

/**
 * Check if a file type is accepted.
 *
 * @param {File} file - File to check
 * @param {string} acceptedTypes - Accepted type pattern
 * @returns {boolean} Whether file type is accepted
 */
export function isAcceptedFileType(file, acceptedTypes) {
  if (acceptedTypes === '*') return true;

  const parts = acceptedTypes.split('/');
  
  // If no '/' in acceptedTypes, do exact match
  if (parts.length < 2) {
    return file.type === acceptedTypes;
  }

  const [type, subtype] = parts;

  if (subtype === '*') {
    return file.type.startsWith(`${type}/`);
  }

  return file.type === acceptedTypes;
}
