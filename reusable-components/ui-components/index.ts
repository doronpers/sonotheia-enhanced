/**
 * UI Components - Reusable React patterns for file upload, analysis, and results display.
 *
 * This module provides production-ready React component patterns including:
 * - File upload with drag-and-drop
 * - API integration utilities
 * - State management patterns
 * - Dynamic evidence display
 * - Loading and error states
 *
 * @packageDocumentation
 */

// Components
export { UploadArea } from './UploadArea';
export { LoadingSpinner } from './LoadingSpinner';
export { VerdictDisplay } from './VerdictDisplay';
export { ErrorDisplay } from './ErrorDisplay';

// Hooks
export { useFileUpload } from './hooks/useFileUpload';
export { useApi } from './hooks/useApi';

// Utilities
export { buildApiUrl, formatEvidence } from './utils';

// Types
export type { UploadState, ApiConfig, EvidenceRow, VerdictType } from './types';
