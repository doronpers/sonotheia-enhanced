import { useState, useCallback } from 'react';
import { buildApiUrl } from '../utils';
import type { ApiConfig } from '../types';

/**
 * State for API request.
 */
export interface ApiState<T> {
  /** Response data */
  data: T | null;
  /** Loading status */
  loading: boolean;
  /** Error message */
  error: string;
}

/**
 * Hook return type for API.
 */
export interface UseApiReturn<T> {
  /** Current API state */
  state: ApiState<T>;
  /** Execute GET request */
  get: (endpoint: string) => Promise<T | null>;
  /** Execute POST request */
  post: (endpoint: string, body?: unknown) => Promise<T | null>;
  /** Reset state */
  reset: () => void;
  /** Whether request is loading */
  isLoading: boolean;
  /** Whether there's an error */
  hasError: boolean;
}

/**
 * Custom hook for API requests.
 *
 * Provides methods for GET and POST requests with state management.
 *
 * @param config - API configuration
 * @returns API state and methods
 *
 * @example
 * ```tsx
 * const { state, get, post } = useApi({ baseUrl: 'https://api.example.com' });
 *
 * // GET request
 * const data = await get('/api/health');
 *
 * // POST request
 * const result = await post('/api/analyze', { data: 'test' });
 * ```
 */
export function useApi<T = unknown>(config: ApiConfig): UseApiReturn<T> {
  const { baseUrl, timeout = 30000, headers = {} } = config;

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: '',
  });

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: '',
    });
  }, []);

  const handleRequest = useCallback(
    async (
      endpoint: string,
      method: 'GET' | 'POST',
      body?: unknown
    ): Promise<T | null> => {
      setState((prev) => ({ ...prev, loading: true, error: '' }));

      try {
        const url = buildApiUrl(baseUrl, endpoint);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const requestInit: RequestInit = {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...headers,
          },
          signal: controller.signal,
        };

        if (body && method === 'POST') {
          requestInit.body = JSON.stringify(body);
        }

        const response = await fetch(url, requestInit);
        clearTimeout(timeoutId);

        const contentType = response.headers.get('content-type');
        const isJson = contentType?.includes('application/json');
        const payload = isJson ? await response.json() : await response.text();

        if (!response.ok) {
          const errorMessage =
            isJson && payload?.detail
              ? payload.detail
              : `Request failed with status ${response.status}`;
          throw new Error(errorMessage);
        }

        const data = payload as T;
        setState({ data, loading: false, error: '' });
        return data;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unexpected error';

        setState({ data: null, loading: false, error: errorMessage });
        return null;
      }
    },
    [baseUrl, timeout, headers]
  );

  const get = useCallback(
    (endpoint: string) => handleRequest(endpoint, 'GET'),
    [handleRequest]
  );

  const post = useCallback(
    (endpoint: string, body?: unknown) => handleRequest(endpoint, 'POST', body),
    [handleRequest]
  );

  return {
    state,
    get,
    post,
    reset,
    isLoading: state.loading,
    hasError: state.error !== '',
  };
}

export default useApi;
