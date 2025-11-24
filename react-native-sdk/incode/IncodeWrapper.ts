/**
 * Incode SDK Wrapper for React Native
 * 
 * Provides React Native bindings for Incode's biometric onboarding SDK
 * including document scan, face capture, and liveness checks.
 */

import { NativeModules, NativeEventEmitter, Platform } from 'react-native';

const { IncodeSDK } = NativeModules;
const incodeEventEmitter = new NativeEventEmitter(IncodeSDK);

/**
 * Configuration options for Incode SDK
 */
export interface IncodeConfig {
  apiKey: string;
  apiURL: string;
  flowId?: string;
  region?: 'US' | 'EU' | 'APAC';
  enableLogging?: boolean;
}

/**
 * Document scan result
 */
export interface DocumentScanResult {
  success: boolean;
  documentType: 'passport' | 'driver_license' | 'id_card';
  documentNumber?: string;
  expiryDate?: string;
  issuingCountry?: string;
  verified: boolean;
  confidence: number;
  incodeId?: string;
}

/**
 * Face capture result
 */
export interface FaceCaptureResult {
  success: boolean;
  faceMatch: boolean;
  faceMatchScore: number;
  incodeId?: string;
  imageData?: string; // Base64 encoded
}

/**
 * Liveness check result
 */
export interface LivenessCheckResult {
  success: boolean;
  livenessPassed: boolean;
  livenessConfidence: number;
  incodeId?: string;
}

/**
 * Complete onboarding session result from Incode
 */
export interface IncodeOnboardingResult {
  sessionId: string;
  documentScan: DocumentScanResult;
  faceCapture: FaceCaptureResult;
  livenessCheck: LivenessCheckResult;
  overallScore: number;
  timestamp: string;
}

/**
 * Incode SDK Wrapper Class
 * 
 * Provides methods to interact with Incode's native biometric SDK
 */
class IncodeWrapper {
  private config: IncodeConfig | null = null;
  private sessionId: string | null = null;

  /**
   * Initialize Incode SDK with configuration
   * @param config Configuration options
   */
  async initialize(config: IncodeConfig): Promise<void> {
    this.config = config;
    
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      await IncodeSDK.initialize(config);
    } else {
      console.warn('Incode SDK is only available on iOS and Android');
    }
  }

  /**
   * Start a new onboarding session
   * @returns Session ID from Incode
   */
  async startSession(): Promise<string> {
    if (!this.config) {
      throw new Error('Incode SDK not initialized. Call initialize() first.');
    }

    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      this.sessionId = await IncodeSDK.startSession();
      return this.sessionId;
    } else {
      // Mock session ID for development/testing
      this.sessionId = `INCODE-MOCK-${Date.now()}`;
      return this.sessionId;
    }
  }

  /**
   * Capture and verify identity document
   * @param documentType Type of document to scan
   * @returns Document scan result
   */
  async scanDocument(
    documentType: 'passport' | 'driver_license' | 'id_card' = 'id_card'
  ): Promise<DocumentScanResult> {
    if (!this.sessionId) {
      throw new Error('No active session. Call startSession() first.');
    }

    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      return await IncodeSDK.scanDocument(documentType);
    } else {
      // Mock result for development/testing
      return {
        success: true,
        documentType,
        documentNumber: 'DOC123456789',
        expiryDate: '2030-12-31',
        issuingCountry: 'US',
        verified: true,
        confidence: 0.95,
        incodeId: this.sessionId
      };
    }
  }

  /**
   * Capture selfie and perform face matching
   * @returns Face capture result
   */
  async captureFace(): Promise<FaceCaptureResult> {
    if (!this.sessionId) {
      throw new Error('No active session. Call startSession() first.');
    }

    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      return await IncodeSDK.captureFace();
    } else {
      // Mock result for development/testing
      return {
        success: true,
        faceMatch: true,
        faceMatchScore: 0.92,
        incodeId: this.sessionId
      };
    }
  }

  /**
   * Perform liveness check (anti-spoofing)
   * @returns Liveness check result
   */
  async checkLiveness(): Promise<LivenessCheckResult> {
    if (!this.sessionId) {
      throw new Error('No active session. Call startSession() first.');
    }

    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      return await IncodeSDK.checkLiveness();
    } else {
      // Mock result for development/testing
      return {
        success: true,
        livenessPassed: true,
        livenessConfidence: 0.97,
        incodeId: this.sessionId
      };
    }
  }

  /**
   * Complete onboarding flow (document + face + liveness)
   * @returns Complete onboarding result
   */
  async completeOnboarding(): Promise<IncodeOnboardingResult> {
    const sessionId = await this.startSession();
    
    const documentScan = await this.scanDocument();
    const faceCapture = await this.captureFace();
    const livenessCheck = await this.checkLiveness();

    // Calculate overall score (weighted average)
    const overallScore = (
      documentScan.confidence * 0.4 +
      faceCapture.faceMatchScore * 0.3 +
      livenessCheck.livenessConfidence * 0.3
    );

    return {
      sessionId,
      documentScan,
      faceCapture,
      livenessCheck,
      overallScore,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return this.sessionId;
  }

  /**
   * Add event listener for Incode SDK events
   * @param eventName Event name
   * @param listener Event listener function
   * @returns Subscription object
   */
  addListener(
    eventName: string,
    listener: (event: any) => void
  ): { remove: () => void } {
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      return incodeEventEmitter.addListener(eventName, listener);
    } else {
      // Mock subscription for development
      return { remove: () => {} };
    }
  }

  /**
   * Remove all event listeners
   */
  removeAllListeners(): void {
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      incodeEventEmitter.removeAllListeners();
    }
  }

  /**
   * Cleanup and end current session
   */
  async endSession(): Promise<void> {
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      await IncodeSDK.endSession();
    }
    this.sessionId = null;
  }
}

// Export singleton instance
export const IncodeSDKWrapper = new IncodeWrapper();

// Export types
export type {
  IncodeConfig,
  DocumentScanResult,
  FaceCaptureResult,
  LivenessCheckResult,
  IncodeOnboardingResult
};
