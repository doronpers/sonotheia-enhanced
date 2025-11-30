/**
 * TypeScript type definitions for UI components.
 */

/**
 * State for file upload operations.
 */
export interface UploadState {
  /** Whether upload is in progress */
  uploading: boolean;
  /** Analysis result data */
  result: AnalysisResult | null;
  /** Error message if any */
  error: string;
}

/**
 * API configuration options.
 */
export interface ApiConfig {
  /** Base URL for API requests */
  baseUrl: string;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Additional headers */
  headers?: Record<string, string>;
}

/**
 * Single row of evidence for display.
 */
export interface EvidenceRow {
  /** Human-readable label */
  label: string;
  /** Value to display */
  value: string;
  /** Status indicator */
  status: 'pass' | 'fail' | 'info';
}

/**
 * Analysis verdict types.
 */
export type VerdictType = 'REAL' | 'SYNTHETIC' | 'UNKNOWN';

/**
 * Analysis result from the API.
 */
export interface AnalysisResult {
  /** Analysis verdict */
  verdict: VerdictType;
  /** Detailed explanation */
  detail: string;
  /** Processing time in seconds */
  processing_time_seconds: number;
  /** Evidence dictionary */
  evidence: Record<string, SensorEvidence>;
  /** Model version used */
  model_version?: string;
}

/**
 * Evidence from a single sensor.
 */
export interface SensorEvidence {
  /** Sensor name */
  sensor_name: string;
  /** Pass/fail/null result */
  passed: boolean | null;
  /** Measured value */
  value: number;
  /** Decision threshold */
  threshold: number;
  /** Failure reason code */
  reason?: string;
  /** Human-readable detail */
  detail?: string;
}

/**
 * Props for UploadArea component.
 */
export interface UploadAreaProps {
  /** Callback when files are selected */
  onFileSelect: (files: FileList) => void;
  /** Accepted file types (default: "audio/*") */
  acceptedTypes?: string;
  /** Whether upload is disabled */
  disabled?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Props for VerdictDisplay component.
 */
export interface VerdictDisplayProps {
  /** Analysis verdict */
  verdict: VerdictType;
  /** Detailed explanation */
  detail?: string;
  /** Custom class name */
  className?: string;
}

/**
 * Props for LoadingSpinner component.
 */
export interface LoadingSpinnerProps {
  /** Message to display */
  message?: string;
  /** Custom class name */
  className?: string;
}

/**
 * Props for ErrorDisplay component.
 */
export interface ErrorDisplayProps {
  /** Error message */
  error: string;
  /** Callback to reset/dismiss error */
  onReset?: () => void;
  /** Custom class name */
  className?: string;
}
