/**
 * React Hooks for Sonotheia Voice Capture Integration
 * 
 * Provides easy-to-use React hooks for voice capture and analysis
 */

import { useState, useEffect, useCallback } from 'react';
import {
  SonotheiaSDKWrapper,
  RecordingState,
  type VoiceAnalysisResult,
  type VoiceRecording
} from '../sonotheia/SonotheiaWrapper';

export interface SonotheiaState {
  isInitialized: boolean;
  recordingState: RecordingState;
  currentRecordingId: string | null;
  isAnalyzing: boolean;
  error: Error | null;
  analysisResult: VoiceAnalysisResult | null;
}

/**
 * Hook for Sonotheia voice capture and analysis
 * 
 * @param apiURL Backend API URL
 * @param apiKey Optional API key
 * @returns Sonotheia state and control functions
 */
export function useSonotheia(apiURL: string, apiKey?: string) {
  const [state, setState] = useState<SonotheiaState>({
    isInitialized: false,
    recordingState: RecordingState.IDLE,
    currentRecordingId: null,
    isAnalyzing: false,
    error: null,
    analysisResult: null
  });

  // Initialize SDK
  useEffect(() => {
    const initializeSDK = async () => {
      try {
        await SonotheiaSDKWrapper.initialize({
          apiURL,
          apiKey,
          sampleRate: 16000,
          minDuration: 2.0,
          maxDuration: 30.0,
          enableLogging: __DEV__
        });
        setState(prev => ({ ...prev, isInitialized: true }));
      } catch (error) {
        setState(prev => ({ ...prev, error: error as Error }));
      }
    };

    initializeSDK();

    // Setup event listeners
    const recordingStateListener = SonotheiaSDKWrapper.addListener(
      'recordingStateChanged',
      (event: { state: RecordingState }) => {
        setState(prev => ({ ...prev, recordingState: event.state }));
      }
    );

    return () => {
      recordingStateListener.remove();
      SonotheiaSDKWrapper.removeAllListeners();
    };
  }, [apiURL, apiKey]);

  // Start recording
  const startRecording = useCallback(async (prompt?: string, duration?: number) => {
    setState(prev => ({ ...prev, error: null }));
    try {
      const recordingId = await SonotheiaSDKWrapper.startRecording({
        prompt,
        duration,
        autoStop: true
      });
      setState(prev => ({
        ...prev,
        currentRecordingId: recordingId,
        recordingState: RecordingState.RECORDING
      }));
      return recordingId;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // Stop recording
  const stopRecording = useCallback(async (): Promise<VoiceRecording> => {
    setState(prev => ({ ...prev, error: null }));
    try {
      const recording = await SonotheiaSDKWrapper.stopRecording();
      setState(prev => ({
        ...prev,
        recordingState: RecordingState.COMPLETED
      }));
      return recording;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error,
        recordingState: RecordingState.ERROR
      }));
      throw error;
    }
  }, []);

  // Analyze voice
  const analyzeVoice = useCallback(async (
    audioData: string,
    userId?: string
  ): Promise<VoiceAnalysisResult> => {
    setState(prev => ({
      ...prev,
      isAnalyzing: true,
      error: null
    }));
    try {
      const result = await SonotheiaSDKWrapper.analyzeVoice(audioData, userId);
      setState(prev => ({
        ...prev,
        analysisResult: result,
        isAnalyzing: false
      }));
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isAnalyzing: false,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // Capture and analyze in one step
  const captureAndAnalyze = useCallback(async (
    prompt?: string,
    duration?: number,
    userId?: string
  ): Promise<VoiceAnalysisResult> => {
    setState(prev => ({ ...prev, error: null }));
    try {
      const result = await SonotheiaSDKWrapper.captureAndAnalyze(
        { prompt, duration },
        userId
      );
      setState(prev => ({
        ...prev,
        analysisResult: result,
        recordingState: RecordingState.COMPLETED
      }));
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error,
        recordingState: RecordingState.ERROR
      }));
      throw error;
    }
  }, []);

  // Cancel recording
  const cancelRecording = useCallback(async () => {
    try {
      await SonotheiaSDKWrapper.cancelRecording();
      setState(prev => ({
        ...prev,
        currentRecordingId: null,
        recordingState: RecordingState.IDLE
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error
      }));
    }
  }, []);

  // Upload voice sample to backend
  const uploadVoiceSample = useCallback(async (
    audioData: string,
    sessionId: string
  ) => {
    setState(prev => ({ ...prev, error: null }));
    try {
      const response = await SonotheiaSDKWrapper.uploadVoiceSample(audioData, sessionId);
      return response;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error
      }));
      throw error;
    }
  }, []);

  // Reset state
  const reset = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentRecordingId: null,
      recordingState: RecordingState.IDLE,
      isAnalyzing: false,
      error: null,
      analysisResult: null
    }));
  }, []);

  return {
    ...state,
    startRecording,
    stopRecording,
    analyzeVoice,
    captureAndAnalyze,
    cancelRecording,
    uploadVoiceSample,
    reset
  };
}

/**
 * Hook for simple voice recording
 * 
 * @returns Recording state and control functions
 */
export function useVoiceRecording() {
  const [isRecording, setIsRecording] = useState(false);
  const [recording, setRecording] = useState<VoiceRecording | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const start = useCallback(async (prompt?: string, duration?: number) => {
    setIsRecording(true);
    setError(null);
    try {
      await SonotheiaSDKWrapper.startRecording({ prompt, duration });
    } catch (err) {
      setError(err as Error);
      setIsRecording(false);
      throw err;
    }
  }, []);

  const stop = useCallback(async () => {
    try {
      const rec = await SonotheiaSDKWrapper.stopRecording();
      setRecording(rec);
      setIsRecording(false);
      return rec;
    } catch (err) {
      setError(err as Error);
      setIsRecording(false);
      throw err;
    }
  }, []);

  const cancel = useCallback(async () => {
    try {
      await SonotheiaSDKWrapper.cancelRecording();
      setIsRecording(false);
      setRecording(null);
    } catch (err) {
      setError(err as Error);
    }
  }, []);

  const reset = useCallback(() => {
    setRecording(null);
    setError(null);
    setIsRecording(false);
  }, []);

  return {
    isRecording,
    recording,
    error,
    start,
    stop,
    cancel,
    reset
  };
}

/**
 * Hook for voice analysis
 * 
 * @returns Analysis state and control function
 */
export function useVoiceAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<VoiceAnalysisResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const analyze = useCallback(async (audioData: string, userId?: string) => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const analysisResult = await SonotheiaSDKWrapper.analyzeVoice(audioData, userId);
      setResult(analysisResult);
      return analysisResult;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setIsAnalyzing(false);
  }, []);

  return {
    isAnalyzing,
    result,
    error,
    analyze,
    reset
  };
}
