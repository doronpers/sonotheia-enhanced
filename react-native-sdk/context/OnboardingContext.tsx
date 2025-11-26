/**
 * Onboarding Context for React Native
 * 
 * Provides a unified context for orchestrating Incode biometric onboarding
 * and Sonotheia voice capture with backend session management.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { IncodeSDKWrapper, type IncodeOnboardingResult } from '../incode/IncodeWrapper';
import { SonotheiaSDKWrapper, type VoiceAnalysisResult } from '../sonotheia/SonotheiaWrapper';

/**
 * Onboarding step enumeration
 */
export enum OnboardingStep {
  INIT = 'init',
  DOCUMENT_SCAN = 'document_scan',
  FACE_CAPTURE = 'face_capture',
  LIVENESS_CHECK = 'liveness_check',
  VOICE_CAPTURE = 'voice_capture',
  RISK_EVALUATION = 'risk_evaluation',
  COMPLETE = 'complete',
  ERROR = 'error'
}

/**
 * Onboarding session data
 */
export interface OnboardingSession {
  sessionId: string | null;
  incodeSessionId: string | null;
  currentStep: OnboardingStep;
  userId: string;
  incodeResult: IncodeOnboardingResult | null;
  voiceResult: VoiceAnalysisResult | null;
  riskScore: number | null;
  riskLevel: string | null;
  decision: string | null;
  error: Error | null;
}

/**
 * Context value interface
 */
interface OnboardingContextValue {
  session: OnboardingSession;
  isLoading: boolean;
  
  // Lifecycle methods
  startOnboarding: (userId: string) => Promise<string>;
  completeOnboarding: () => Promise<OnboardingSession>;
  resetOnboarding: () => void;
  
  // Individual step methods
  performBiometricOnboarding: () => Promise<IncodeOnboardingResult>;
  captureVoice: (prompt?: string) => Promise<VoiceAnalysisResult>;
  evaluateRisk: () => Promise<any>;
  
  // Progress tracking
  goToStep: (step: OnboardingStep) => void;
  getCurrentStep: () => OnboardingStep;
}

/**
 * Context configuration
 */
interface OnboardingConfig {
  backendURL: string;
  incodeAPIKey: string;
  incodeAPIURL: string;
  apiKey?: string;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

/**
 * Provider Props
 */
interface OnboardingProviderProps {
  children: ReactNode;
  config: OnboardingConfig;
}

/**
 * Onboarding Context Provider
 * 
 * Orchestrates the complete onboarding flow including:
 * 1. Backend session initiation
 * 2. Incode biometric capture (document, face, liveness)
 * 3. Sonotheia voice capture and analysis
 * 4. Risk evaluation
 */
export function OnboardingProvider({ children, config }: OnboardingProviderProps) {
  const [session, setSession] = useState<OnboardingSession>({
    sessionId: null,
    incodeSessionId: null,
    currentStep: OnboardingStep.INIT,
    userId: '',
    incodeResult: null,
    voiceResult: null,
    riskScore: null,
    riskLevel: null,
    decision: null,
    error: null
  });

  const [isLoading, setIsLoading] = useState(false);

  /**
   * Start new onboarding session
   */
  const startOnboarding = useCallback(async (userId: string): Promise<string> => {
    setIsLoading(true);
    try {
      // Initialize SDKs
      await IncodeSDKWrapper.initialize({
        apiKey: config.incodeAPIKey,
        apiURL: config.incodeAPIURL,
        enableLogging: __DEV__
      });

      await SonotheiaSDKWrapper.initialize({
        apiURL: config.backendURL,
        apiKey: config.apiKey,
        sampleRate: 16000,
        minDuration: 2.0,
        maxDuration: 30.0,
        enableLogging: __DEV__
      });

      // Start backend session
      const response = await fetch(`${config.backendURL}/api/session/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(config.apiKey ? { 'X-API-Key': config.apiKey } : {})
        },
        body: JSON.stringify({
          user_id: userId,
          session_type: 'onboarding',
          metadata: {
            platform: 'react-native',
            timestamp: new Date().toISOString()
          }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to start session');
      }

      const sessionData = await response.json();

      setSession({
        sessionId: sessionData.session_id,
        incodeSessionId: null,
        currentStep: OnboardingStep.DOCUMENT_SCAN,
        userId,
        incodeResult: null,
        voiceResult: null,
        riskScore: null,
        riskLevel: null,
        decision: null,
        error: null
      });

      return sessionData.session_id;
    } catch (error) {
      setSession(prev => ({
        ...prev,
        currentStep: OnboardingStep.ERROR,
        error: error as Error
      }));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [config]);

  /**
   * Perform complete Incode biometric onboarding
   */
  const performBiometricOnboarding = useCallback(async (): Promise<IncodeOnboardingResult> => {
    setIsLoading(true);
    try {
      setSession(prev => ({ ...prev, currentStep: OnboardingStep.DOCUMENT_SCAN }));
      
      // Complete Incode flow (document + face + liveness)
      const incodeResult = await IncodeSDKWrapper.completeOnboarding();

      // Upload biometric data to backend
      if (session.sessionId) {
        await fetch(`${config.backendURL}/api/session/${session.sessionId}/biometric`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(config.apiKey ? { 'X-API-Key': config.apiKey } : {})
          },
          body: JSON.stringify({
            document_verified: incodeResult.documentScan.verified,
            face_match_score: incodeResult.faceCapture.faceMatchScore,
            liveness_passed: incodeResult.livenessCheck.livenessPassed,
            incode_session_id: incodeResult.sessionId,
            metadata: {
              overall_score: incodeResult.overallScore,
              timestamp: incodeResult.timestamp
            }
          })
        });
      }

      setSession(prev => ({
        ...prev,
        incodeSessionId: incodeResult.sessionId,
        incodeResult,
        currentStep: OnboardingStep.VOICE_CAPTURE
      }));

      return incodeResult;
    } catch (error) {
      setSession(prev => ({
        ...prev,
        currentStep: OnboardingStep.ERROR,
        error: error as Error
      }));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [session.sessionId, config]);

  /**
   * Capture and analyze voice
   */
  const captureVoice = useCallback(async (prompt?: string): Promise<VoiceAnalysisResult> => {
    setIsLoading(true);
    try {
      setSession(prev => ({ ...prev, currentStep: OnboardingStep.VOICE_CAPTURE }));

      const defaultPrompt = prompt || 'Please say: "My voice is my password for authentication"';
      const voiceResult = await SonotheiaSDKWrapper.captureAndAnalyze(
        { prompt: defaultPrompt, duration: 5.0 },
        session.userId
      );

      // Upload voice data to backend
      if (session.sessionId) {
        await fetch(`${config.backendURL}/api/session/${session.sessionId}/voice`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(config.apiKey ? { 'X-API-Key': config.apiKey } : {})
          },
          body: JSON.stringify({
            deepfake_score: voiceResult.deepfakeScore,
            speaker_verified: voiceResult.speakerVerified,
            speaker_score: voiceResult.speakerScore,
            audio_quality: voiceResult.audioQuality,
            audio_duration_seconds: voiceResult.audioDuration,
            metadata: voiceResult.metadata
          })
        });
      }

      setSession(prev => ({
        ...prev,
        voiceResult,
        currentStep: OnboardingStep.RISK_EVALUATION
      }));

      return voiceResult;
    } catch (error) {
      setSession(prev => ({
        ...prev,
        currentStep: OnboardingStep.ERROR,
        error: error as Error
      }));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [session.sessionId, session.userId, config]);

  /**
   * Evaluate composite risk
   */
  const evaluateRisk = useCallback(async () => {
    setIsLoading(true);
    try {
      if (!session.sessionId) {
        throw new Error('No active session');
      }

      setSession(prev => ({ ...prev, currentStep: OnboardingStep.RISK_EVALUATION }));

      const response = await fetch(
        `${config.backendURL}/api/session/${session.sessionId}/evaluate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(config.apiKey ? { 'X-API-Key': config.apiKey } : {})
          },
          body: JSON.stringify({
            session_id: session.sessionId,
            include_factors: true
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to evaluate risk');
      }

      const riskData = await response.json();

      setSession(prev => ({
        ...prev,
        riskScore: riskData.composite_risk_score,
        riskLevel: riskData.risk_level,
        decision: riskData.decision,
        currentStep: OnboardingStep.COMPLETE
      }));

      return riskData;
    } catch (error) {
      setSession(prev => ({
        ...prev,
        currentStep: OnboardingStep.ERROR,
        error: error as Error
      }));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [session.sessionId, config]);

  /**
   * Complete full onboarding flow
   */
  const completeOnboarding = useCallback(async (): Promise<OnboardingSession> => {
    try {
      // Step 1: Biometric onboarding
      await performBiometricOnboarding();

      // Step 2: Voice capture
      await captureVoice();

      // Step 3: Risk evaluation
      await evaluateRisk();

      return session;
    } catch (error) {
      throw error;
    }
  }, [performBiometricOnboarding, captureVoice, evaluateRisk, session]);

  /**
   * Go to specific step
   */
  const goToStep = useCallback((step: OnboardingStep) => {
    setSession(prev => ({ ...prev, currentStep: step }));
  }, []);

  /**
   * Get current step
   */
  const getCurrentStep = useCallback(() => {
    return session.currentStep;
  }, [session.currentStep]);

  /**
   * Reset onboarding state
   */
  const resetOnboarding = useCallback(() => {
    setSession({
      sessionId: null,
      incodeSessionId: null,
      currentStep: OnboardingStep.INIT,
      userId: '',
      incodeResult: null,
      voiceResult: null,
      riskScore: null,
      riskLevel: null,
      decision: null,
      error: null
    });
  }, []);

  const value: OnboardingContextValue = {
    session,
    isLoading,
    startOnboarding,
    completeOnboarding,
    resetOnboarding,
    performBiometricOnboarding,
    captureVoice,
    evaluateRisk,
    goToStep,
    getCurrentStep
  };

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
}

/**
 * Hook to use Onboarding Context
 */
export function useOnboarding(): OnboardingContextValue {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within OnboardingProvider');
  }
  return context;
}

// Export types
export type { OnboardingConfig, OnboardingContextValue };
