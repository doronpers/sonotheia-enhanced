/**
 * Sonotheia Voice Capture SDK Wrapper for React Native
 * 
 * Provides React Native bindings for Sonotheia's voice capture and
 * deepfake detection functionality.
 */

import { NativeModules, NativeEventEmitter, Platform, PermissionsAndroid } from 'react-native';

const { SonotheiaSDK } = NativeModules;
const sonotheiaEventEmitter = new NativeEventEmitter(SonotheiaSDK);

/**
 * Configuration options for Sonotheia SDK
 */
export interface SonotheiaConfig {
  apiURL: string;
  apiKey?: string;
  sampleRate?: number; // Default: 16000 Hz
  minDuration?: number; // Minimum recording duration in seconds
  maxDuration?: number; // Maximum recording duration in seconds
  enableLogging?: boolean;
}

/**
 * Voice capture options
 */
export interface VoiceCaptureOptions {
  prompt?: string; // Text prompt for user to read
  duration?: number; // Recording duration in seconds
  autoStop?: boolean; // Auto-stop when duration reached
}

/**
 * Voice analysis result from Sonotheia
 */
export interface VoiceAnalysisResult {
  success: boolean;
  deepfakeScore: number; // 0-1, higher = more likely synthetic
  deepfakePassed: boolean;
  speakerScore: number; // 0-1, speaker verification confidence
  speakerVerified: boolean;
  livenessScore: number; // 0-1, liveness confidence
  livenessPassed: boolean;
  audioQuality: number; // 0-1, audio quality score
  audioDuration: number; // Duration in seconds
  metadata: {
    sampleRate: number;
    channels: number;
    format: string;
  };
}

/**
 * Voice recording metadata
 */
export interface VoiceRecording {
  recordingId: string;
  audioData: string; // Base64 encoded audio
  duration: number;
  sampleRate: number;
  timestamp: string;
}

/**
 * Recording state
 */
export enum RecordingState {
  IDLE = 'idle',
  RECORDING = 'recording',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  ERROR = 'error'
}

/**
 * Sonotheia SDK Wrapper Class
 * 
 * Provides methods to capture and analyze voice samples for deepfake detection
 */
class SonotheiaWrapper {
  private config: SonotheiaConfig | null = null;
  private recordingState: RecordingState = RecordingState.IDLE;
  private currentRecordingId: string | null = null;

  /**
   * Initialize Sonotheia SDK with configuration
   * @param config Configuration options
   */
  async initialize(config: SonotheiaConfig): Promise<void> {
    this.config = config;
    
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      await SonotheiaSDK.initialize({
        apiURL: config.apiURL,
        apiKey: config.apiKey || '',
        sampleRate: config.sampleRate || 16000,
        minDuration: config.minDuration || 2.0,
        maxDuration: config.maxDuration || 30.0,
        enableLogging: config.enableLogging || false
      });
    } else {
      console.warn('Sonotheia SDK is only available on iOS and Android');
    }
  }

  /**
   * Request microphone permissions
   * @returns Whether permissions were granted
   */
  async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        {
          title: 'Microphone Permission',
          message: 'This app needs access to your microphone for voice authentication',
          buttonPositive: 'Grant',
          buttonNegative: 'Deny'
        }
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    } else if (Platform.OS === 'ios') {
      // iOS handles permissions natively via Info.plist
      return true;
    }
    return false;
  }

  /**
   * Start voice recording
   * @param options Recording options
   * @returns Recording ID
   */
  async startRecording(options?: VoiceCaptureOptions): Promise<string> {
    if (!this.config) {
      throw new Error('Sonotheia SDK not initialized. Call initialize() first.');
    }

    const hasPermission = await this.requestPermissions();
    if (!hasPermission) {
      throw new Error('Microphone permission denied');
    }

    this.recordingState = RecordingState.RECORDING;
    
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      this.currentRecordingId = await SonotheiaSDK.startRecording({
        prompt: options?.prompt || 'Please read the following: "My voice is my password"',
        duration: options?.duration || 5.0,
        autoStop: options?.autoStop !== false
      });
    } else {
      // Mock recording ID for development/testing
      this.currentRecordingId = `REC-${Date.now()}`;
    }

    return this.currentRecordingId;
  }

  /**
   * Stop current voice recording
   * @returns Voice recording data
   */
  async stopRecording(): Promise<VoiceRecording> {
    if (this.recordingState !== RecordingState.RECORDING) {
      throw new Error('No active recording to stop');
    }

    this.recordingState = RecordingState.PROCESSING;

    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      const recording = await SonotheiaSDK.stopRecording();
      this.recordingState = RecordingState.COMPLETED;
      return recording;
    } else {
      // Mock recording for development/testing
      this.recordingState = RecordingState.COMPLETED;
      return {
        recordingId: this.currentRecordingId!,
        audioData: 'base64_encoded_audio_data_here',
        duration: 4.5,
        sampleRate: this.config?.sampleRate || 16000,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Analyze voice sample for deepfake detection
   * @param audioData Base64 encoded audio data
   * @param userId Optional user ID for speaker verification
   * @returns Voice analysis result
   */
  async analyzeVoice(audioData: string, userId?: string): Promise<VoiceAnalysisResult> {
    if (!this.config) {
      throw new Error('Sonotheia SDK not initialized. Call initialize() first.');
    }

    this.recordingState = RecordingState.PROCESSING;

    try {
      if (Platform.OS === 'android' || Platform.OS === 'ios') {
        const result = await SonotheiaSDK.analyzeVoice(audioData, userId);
        this.recordingState = RecordingState.COMPLETED;
        return result;
      } else {
        // Mock analysis result for development/testing
        this.recordingState = RecordingState.COMPLETED;
        return {
          success: true,
          deepfakeScore: 0.15,
          deepfakePassed: true,
          speakerScore: 0.92,
          speakerVerified: true,
          livenessScore: 0.95,
          livenessPassed: true,
          audioQuality: 0.88,
          audioDuration: 4.5,
          metadata: {
            sampleRate: this.config?.sampleRate || 16000,
            channels: 1,
            format: 'wav'
          }
        };
      }
    } catch (error) {
      this.recordingState = RecordingState.ERROR;
      throw error;
    }
  }

  /**
   * Capture and analyze voice in one step
   * @param options Recording options
   * @param userId Optional user ID for speaker verification
   * @returns Voice analysis result
   */
  async captureAndAnalyze(
    options?: VoiceCaptureOptions,
    userId?: string
  ): Promise<VoiceAnalysisResult> {
    await this.startRecording(options);
    
    // Wait for recording duration
    const duration = options?.duration || 5.0;
    await new Promise(resolve => setTimeout(resolve, duration * 1000));
    
    const recording = await this.stopRecording();
    return await this.analyzeVoice(recording.audioData, userId);
  }

  /**
   * Get current recording state
   */
  getRecordingState(): RecordingState {
    return this.recordingState;
  }

  /**
   * Get current recording ID
   */
  getCurrentRecordingId(): string | null {
    return this.currentRecordingId;
  }

  /**
   * Cancel current recording
   */
  async cancelRecording(): Promise<void> {
    if (this.recordingState !== RecordingState.RECORDING) {
      return;
    }

    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      await SonotheiaSDK.cancelRecording();
    }

    this.recordingState = RecordingState.IDLE;
    this.currentRecordingId = null;
  }

  /**
   * Add event listener for Sonotheia SDK events
   * @param eventName Event name
   * @param listener Event listener function
   * @returns Subscription object
   */
  addListener(
    eventName: string,
    listener: (event: any) => void
  ): { remove: () => void } {
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      return sonotheiaEventEmitter.addListener(eventName, listener);
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
      sonotheiaEventEmitter.removeAllListeners();
    }
  }

  /**
   * Upload voice sample to backend API
   * @param audioData Base64 encoded audio data
   * @param sessionId Session identifier
   * @returns API response
   */
  async uploadVoiceSample(audioData: string, sessionId: string): Promise<any> {
    if (!this.config) {
      throw new Error('Sonotheia SDK not initialized. Call initialize() first.');
    }

    const response = await fetch(`${this.config.apiURL}/api/session/${sessionId}/voice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey ? { 'X-API-Key': this.config.apiKey } : {})
      },
      body: JSON.stringify({
        audio_data: audioData,
        timestamp: new Date().toISOString()
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to upload voice sample: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Export singleton instance
export const SonotheiaSDKWrapper = new SonotheiaWrapper();

// Export types and enums
export type {
  SonotheiaConfig,
  VoiceCaptureOptions,
  VoiceAnalysisResult,
  VoiceRecording
};

export { RecordingState };
