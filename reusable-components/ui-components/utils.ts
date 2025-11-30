/**
 * Utility functions for UI components.
 */

import type { SensorEvidence, EvidenceRow } from './types';

/**
 * Build API URL from base URL and endpoint.
 *
 * Handles trailing slashes and empty base URLs.
 *
 * @param baseUrl - Base URL (may be empty for relative URLs)
 * @param endpoint - API endpoint path
 * @returns Full API URL
 *
 * @example
 * buildApiUrl('https://api.example.com/', '/api/detect')
 * // => 'https://api.example.com/api/detect'
 *
 * buildApiUrl('', '/api/detect')
 * // => '/api/detect'
 */
export function buildApiUrl(baseUrl: string | undefined, endpoint: string): string {
  const base = baseUrl && baseUrl.length > 0 ? baseUrl.replace(/\/$/, '') : '';
  return `${base}${endpoint}`;
}

/**
 * Format evidence data into display rows.
 *
 * Transforms sensor evidence into human-readable format.
 *
 * @param evidence - Dictionary of sensor evidence
 * @returns Array of formatted evidence rows
 *
 * @example
 * const rows = formatEvidence(result.evidence);
 * rows.forEach(row => console.log(`${row.label}: ${row.value} (${row.status})`));
 */
export function formatEvidence(evidence: Record<string, SensorEvidence>): EvidenceRow[] {
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
 * @param key - Key to format
 * @returns Formatted label
 *
 * @example
 * formatLabel('breath_sensor')
 * // => 'Breath Sensor'
 */
export function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Get status string from pass/fail value.
 *
 * @param passed - Pass/fail/null value
 * @returns Status string
 */
function getStatus(passed: boolean | null): 'pass' | 'fail' | 'info' {
  if (passed === true) return 'pass';
  if (passed === false) return 'fail';
  return 'info';
}

/**
 * Format file size in human-readable format.
 *
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "2.5 MB")
 *
 * @example
 * formatFileSize(2621440)
 * // => '2.5 MB'
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Format duration in human-readable format.
 *
 * @param seconds - Duration in seconds
 * @returns Formatted string (e.g., "2m 30s")
 *
 * @example
 * formatDuration(150)
 * // => '2m 30s'
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}

/**
 * Format processing time for display.
 *
 * @param seconds - Processing time in seconds
 * @returns Formatted string (e.g., "234ms" or "2.34s")
 *
 * @example
 * formatProcessingTime(0.234)
 * // => '234ms'
 */
export function formatProcessingTime(seconds: number): string {
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`;
  }
  return `${seconds.toFixed(2)}s`;
}

/**
 * Get CSS class for verdict type.
 *
 * @param verdict - Analysis verdict
 * @returns CSS class name
 *
 * @example
 * getVerdictClass('REAL')
 * // => 'verdict-REAL'
 */
export function getVerdictClass(verdict: string): string {
  return `verdict-${verdict}`;
}

/**
 * Check if a file type is accepted.
 *
 * @param file - File to check
 * @param acceptedTypes - Accepted type pattern (e.g., "audio/*")
 * @returns Whether file type is accepted
 *
 * @example
 * isAcceptedFileType(file, 'audio/*')
 */
export function isAcceptedFileType(file: File, acceptedTypes: string): boolean {
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
