import { useState, useCallback } from 'react';
import type { UploadState, AnalysisResult } from '../types';
import { buildApiUrl } from '../utils';

/**
 * Hook return type for file upload.
 */
export interface UseFileUploadReturn {
  /** Current upload state */
  state: UploadState;
  /** Handle file selection */
  handleFiles: (files: FileList) => Promise<void>;
  /** Reset state */
  reset: () => void;
  /** Whether upload is in progress */
  isUploading: boolean;
  /** Whether there's an error */
  hasError: boolean;
  /** Whether there's a result */
  hasResult: boolean;
}

/**
 * Hook options for file upload.
 */
export interface UseFileUploadOptions {
  /** Base URL for API */
  baseUrl?: string;
  /** API endpoint path */
  endpoint?: string;
  /** Callback on success */
  onSuccess?: (result: AnalysisResult) => void;
  /** Callback on error */
  onError?: (error: string) => void;
}

/**
 * Custom hook for file upload operations.
 *
 * Manages upload state, API calls, and error handling.
 *
 * @param options - Configuration options
 * @returns Upload state and handlers
 *
 * @example
 * ```tsx
 * const { state, handleFiles, reset } = useFileUpload({
 *   baseUrl: 'https://api.example.com',
 *   endpoint: '/api/v2/detect/quick',
 *   onSuccess: (result) => console.log('Result:', result),
 * });
 *
 * return (
 *   <div>
 *     {!state.uploading && !state.result && (
 *       <UploadArea onFileSelect={handleFiles} />
 *     )}
 *     {state.uploading && <LoadingSpinner />}
 *     {state.error && <ErrorDisplay error={state.error} onReset={reset} />}
 *     {state.result && <VerdictDisplay verdict={state.result.verdict} />}
 *   </div>
 * );
 * ```
 */
export function useFileUpload(options: UseFileUploadOptions = {}): UseFileUploadReturn {
  const {
    baseUrl = '',
    endpoint = '/api/v2/detect/quick',
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<UploadState>({
    uploading: false,
    result: null,
    error: '',
  });

  const apiUrl = buildApiUrl(baseUrl, endpoint);

  const reset = useCallback(() => {
    setState({
      uploading: false,
      result: null,
      error: '',
    });
  }, []);

  const handleFiles = useCallback(
    async (files: FileList) => {
      const file = files[0];
      if (!file) return;

      setState({
        uploading: true,
        result: null,
        error: '',
      });

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(apiUrl, {
          method: 'POST',
          body: formData,
        });

        const contentType = response.headers.get('content-type');
        const isJson = contentType?.includes('application/json');
        const payload = isJson ? await response.json() : await response.text();

        if (!response.ok) {
          const errorMessage =
            isJson && payload?.detail ? payload.detail : String(payload);
          throw new Error(errorMessage);
        }

        setState({
          uploading: false,
          result: payload as AnalysisResult,
          error: '',
        });

        onSuccess?.(payload as AnalysisResult);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unexpected error';

        setState({
          uploading: false,
          result: null,
          error: errorMessage,
        });

        onError?.(errorMessage);
      }
    },
    [apiUrl, onSuccess, onError]
  );

  return {
    state,
    handleFiles,
    reset,
    isUploading: state.uploading,
    hasError: state.error !== '',
    hasResult: state.result !== null,
  };
}

export default useFileUpload;
