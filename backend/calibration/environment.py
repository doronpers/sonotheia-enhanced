"""
Environment Analyzer for Dynamic Calibration.

Calculates acoustic properties of the audio channel (Noise Floor, SNR)
to allow sensors to adapt their thresholds in real-time.
"""

import numpy as np
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class EnvironmentAnalyzer:
    """
    Analyzes audio environment characteristics.
    """
    
    @staticmethod
    def analyze(audio: np.ndarray, sr: int) -> Dict[str, float]:
        """
        Calculate environmental metrics.
        
        Args:
            audio: Audio samples (float array)
            sr: Sample rate
            
        Returns:
            Dictionary with 'noise_floor_db', 'snr_db', 'is_noisy'
        """
        if len(audio) == 0:
            return {"noise_floor_db": -90.0, "snr_db": 100.0, "is_noisy": False}
            
        # Calculate RMS energy profile
        # Use small frames to track energy envelope
        frame_len = int(0.02 * sr) # 20ms
        hop_len = int(0.01 * sr)   # 10ms
        
        if len(audio) < frame_len:
             # Too short, assume clean
             return {"noise_floor_db": -90.0, "snr_db": 100.0, "is_noisy": False}
        
        # Simple manual framing to avoid dependency on librosa if not needed
        # But we can use np.lib.stride_tricks or simple loop
        num_frames = (len(audio) - frame_len) // hop_len + 1
        rms_values = []
        
        for i in range(num_frames):
            frame = audio[i*hop_len : i*hop_len + frame_len]
            rms = np.sqrt(np.mean(frame**2))
            rms_values.append(rms)
            
        rms_values = np.array(rms_values)
        rms_db = 20 * np.log10(rms_values + 1e-10)
        
        # Noise Floor Estimation
        # Assumption: The quietest 10% of frames represent the background noise
        # This works for speech which has pauses
        noise_floor_db = np.percentile(rms_db, 10)
        
        # Peak Signal Estimation
        # The loudest 95% represents the speech peak (ignoring outliers)
        peak_signal_db = np.percentile(rms_db, 95)
        
        # SNR
        snr_db = peak_signal_db - noise_floor_db
        
        # Heuristic for "Noisy"
        # If Noise Floor > -40dB OR SNR < 10dB
        is_noisy = (noise_floor_db > -40.0) or (snr_db < 10.0)
        
        return {
            "noise_floor_db": float(noise_floor_db),
            "peak_signal_db": float(peak_signal_db),
            "snr_db": float(snr_db),
            "is_noisy": bool(is_noisy)
        }
