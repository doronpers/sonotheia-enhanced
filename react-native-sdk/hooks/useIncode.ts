/**
 * React Hooks for Incode Integration
 * 
 * Provides easy-to-use React hooks for Incode onboarding flow
 */

import { useState, useEffect, useCallback } from 'react';
import {
  IncodeSDKWrapper,
  type IncodeOnboardingResult,
  type DocumentScanResult,
  type FaceCaptureResult,
  type LivenessCheckResult
} from '../incode/IncodeWrapper';

export interface IncodeState {
  isInitialized: boolean;
  sessionId: string | null;
  isLoading: boolean;
  error: Error | null;
  documentResult: DocumentScanResult | null;
  faceResult: FaceCaptureResult | null;
  livenessResult: LivenessCheckResult | null;
  onboardingComplete: boolean;
}

/**
 * Hook for Incode onboarding flow
 * 
 * @param apiKey Incode API key
 * @param apiURL Incode API URL
 * @returns Incode state and control functions
 */
export function useIncode(apiKey: string, apiURL: string) {
  const [state, setState] = useState<IncodeState>({
    isInitialized: false,
    sessionId: null,
    isLoading: false,
    error: null,
    documentResult: null,
    faceResult: null,
    livenessResult: null,
    onboardingComplete: false
  });

  // Initialize SDK
  useEffect(() => {
    const initializeSDK = async () => {
      try {
        await IncodeSDKWrapper.initialize({
          apiKey,
          apiURL,
          enableLogging: __DEV__
        });
        setState(prev => ({ ...prev, isInitialized: true }));
      } catch (error) {
        setState(prev => ({ ...prev, error: error as Error }));
      }
    };

    initializeSDK();

    return () => {
      IncodeSDKWrapper.removeAllListeners();
    };
  }, [apiKey, apiURL]);

  // Start new session
  const startSession = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const sessionId = await IncodeSDKWrapper.startSession();
      setState(prev => ({
        ...prev,
        sessionId,
        isLoading: false
      }));
      return sessionId;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // Scan document
  const scanDocument = useCallback(async (
    documentType: 'passport' | 'driver_license' | 'id_card' = 'id_card'
  ) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const result = await IncodeSDKWrapper.scanDocument(documentType);
      setState(prev => ({
        ...prev,
        documentResult: result,
        isLoading: false
      }));
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // Capture face
  const captureFace = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const result = await IncodeSDKWrapper.captureFace();
      setState(prev => ({
        ...prev,
        faceResult: result,
        isLoading: false
      }));
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // Check liveness
  const checkLiveness = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const result = await IncodeSDKWrapper.checkLiveness();
      setState(prev => ({
        ...prev,
        livenessResult: result,
        isLoading: false
      }));
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // Complete full onboarding flow
  const completeOnboarding = useCallback(async (): Promise<IncodeOnboardingResult> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const result = await IncodeSDKWrapper.completeOnboarding();
      setState(prev => ({
        ...prev,
        sessionId: result.sessionId,
        documentResult: result.documentScan,
        faceResult: result.faceCapture,
        livenessResult: result.livenessCheck,
        onboardingComplete: true,
        isLoading: false
      }));
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // End session
  const endSession = useCallback(async () => {
    try {
      await IncodeSDKWrapper.endSession();
      setState({
        isInitialized: state.isInitialized,
        sessionId: null,
        isLoading: false,
        error: null,
        documentResult: null,
        faceResult: null,
        livenessResult: null,
        onboardingComplete: false
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error
      }));
    }
  }, [state.isInitialized]);

  return {
    ...state,
    startSession,
    scanDocument,
    captureFace,
    checkLiveness,
    completeOnboarding,
    endSession
  };
}

/**
 * Hook for Incode document scanning
 * 
 * @returns Document scan state and control function
 */
export function useIncodeDocument() {
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<DocumentScanResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const scan = useCallback(async (
    documentType: 'passport' | 'driver_license' | 'id_card' = 'id_card'
  ) => {
    setIsScanning(true);
    setError(null);
    try {
      const scanResult = await IncodeSDKWrapper.scanDocument(documentType);
      setResult(scanResult);
      return scanResult;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsScanning(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setIsScanning(false);
  }, []);

  return { isScanning, result, error, scan, reset };
}

/**
 * Hook for Incode face capture
 * 
 * @returns Face capture state and control function
 */
export function useIncodeFace() {
  const [isCapturing, setIsCapturing] = useState(false);
  const [result, setResult] = useState<FaceCaptureResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const capture = useCallback(async () => {
    setIsCapturing(true);
    setError(null);
    try {
      const captureResult = await IncodeSDKWrapper.captureFace();
      setResult(captureResult);
      return captureResult;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsCapturing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setIsCapturing(false);
  }, []);

  return { isCapturing, result, error, capture, reset };
}

/**
 * Hook for Incode liveness check
 * 
 * @returns Liveness check state and control function
 */
export function useIncodeLiveness() {
  const [isChecking, setIsChecking] = useState(false);
  const [result, setResult] = useState<LivenessCheckResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const check = useCallback(async () => {
    setIsChecking(true);
    setError(null);
    try {
      const checkResult = await IncodeSDKWrapper.checkLiveness();
      setResult(checkResult);
      return checkResult;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsChecking(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setIsChecking(false);
  }, []);

  return { isChecking, result, error, check, reset };
}
