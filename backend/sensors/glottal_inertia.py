"""
Glottal Inertia Sensor for detecting impossible amplitude rise velocities.

The Physics:
Human vocal folds have mass. They cannot transition from silence to full vibration instantly—there is a mandatory "rise time" as subglottal pressure overcomes tissue inertia.

The Violation:
Synthetic audio, especially spliced or older vocoder output, exhibits:
- "Digital silence" followed immediately by full-amplitude sound
- "Hard cut" endings lacking natural decay
- Missing the chaotic phase signature of genuine glottal onset

Patent Safety:
- Analyzes amplitude dynamics (velocity), NOT Linear Predictive Coding error signals.
- Focuses on velocity of onset rather than spectral shape.
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from .base import BaseSensor, SensorResult

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

logger = logging.getLogger(__name__)

@dataclass
class GlottalInertiaConfig:
    hop_length_ms: float = 2.5
    window_length_ms: float = 5.0

@dataclass
class Onset:
    time: float
    frame_index: int

class GlottalInertiaSensor(BaseSensor):
    """
    Detects impossible amplitude rise velocities.
    
    PATENT SAFE: Analyzes amplitude dynamics, NOT Linear Predictive Coding error signals.
    Focuses on velocity of onset rather than spectral shape.
    """
    
    # Physiological constraints
    MIN_RISE_TIME_MS = 10.0  # Tissue inertia minimum
    SILENCE_THRESHOLD_DB = -60.0
    SPEECH_THRESHOLD_DB = -20.0
    
    def __init__(self, config: Optional[GlottalInertiaConfig] = None):
        super().__init__("Glottal Inertia Sensor")
        self.config = config or GlottalInertiaConfig()
        
    def analyze(self, audio: np.ndarray, sr: int) -> SensorResult:
        """
        Detect biologically impossible amplitude transitions.
        
        Method: Amplitude Rise Velocity (NOT Linear Predictive Coding error signal analysis)
        """
        if not self.validate_input(audio, sr):
             return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                detail="Invalid or empty audio input."
            )

        violations = []
        
        # Compute frame-level amplitude envelope
        envelope_db = self._compute_envelope(audio, sr)
        
        # Find onset candidates (silence -> speech transitions)
        onsets = self._find_onsets(envelope_db, sr)
        
        for onset in onsets:
            # Measure rise time
            rise_time_ms = self._measure_rise_time(
                envelope_db, onset, sr,
                self.SILENCE_THRESHOLD_DB,
                self.SPEECH_THRESHOLD_DB
            )
            
            # Check for phase chaos at onset (natural glottal burst signature)
            has_phase_chaos = self._check_onset_phase_chaos(audio, sr, onset)
            
            # Violation: Too fast AND missing natural phase signature
            # We only flag if it's significantly faster than the minimum
            # Violation: Too fast AND missing natural phase signature
            # We only flag if it's significantly faster than the minimum
            if rise_time_ms < self.MIN_RISE_TIME_MS and not has_phase_chaos:
                violations.append({
                    'type': 'impossible_rise_time',
                    'time': onset.time,
                    'observed_rise_ms': rise_time_ms,
                    'minimum_rise_ms': self.MIN_RISE_TIME_MS,
                    'has_phase_chaos': has_phase_chaos,
                    'explanation': f"Amplitude rise of {rise_time_ms:.1f}ms at {onset.time:.2f}s "
                                   f"violates glottal inertia constraint (minimum {self.MIN_RISE_TIME_MS}ms). "
                                   f"Human vocal fold tissue cannot accelerate this rapidly."
                })
        
        # Also check for hard cuts (abrupt endings)
        hard_cuts = self._detect_hard_cuts(envelope_db, audio, sr)
        violations.extend(hard_cuts)
        
        score = self._compute_score(violations)
        passed = score < 0.5
        
        detail = f"Glottal inertia analysis passed. Score: {score:.2f}"
        if not passed:
             detail = f"Glottal inertia violations detected. Score: {score:.2f}. " \
                      f"Found {len(violations)} violations."

        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=score,
            threshold=0.5,
            detail=detail,
            metadata={
                "violations": violations,
                "violation_count": len(violations)
            }
        )

    def _compute_envelope(self, audio: np.ndarray, sr: int) -> np.ndarray:
        hop_length = int(self.config.hop_length_ms * sr / 1000)
        frame_length = int(self.config.window_length_ms * sr / 1000)
        
        if HAS_LIBROSA:
             rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
        else:
            # Manual RMS
            rms = []
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i+frame_length]
                rms.append(np.sqrt(np.mean(frame**2)))
            rms = np.array(rms)

        return 20 * np.log10(rms + 1e-10)

    def _find_onsets(self, envelope_db: np.ndarray, sr: int) -> List[Onset]:
        onsets = []
        # Simple threshold-based onset detection on the envelope
        # Look for crossing from below SILENCE to above SPEECH
        
        is_speech = False
        for i in range(len(envelope_db) - 1):
            if not is_speech and envelope_db[i] > self.SILENCE_THRESHOLD_DB:
                # Potential onset start
                # Check if it reaches speech threshold soon
                for j in range(i + 1, min(i + 20, len(envelope_db))): # Look ahead ~50ms
                     if envelope_db[j] > self.SPEECH_THRESHOLD_DB:
                         time = i * self.config.hop_length_ms / 1000.0
                         onsets.append(Onset(time=time, frame_index=i))
                         is_speech = True
                         break
            elif is_speech and envelope_db[i] < self.SILENCE_THRESHOLD_DB:
                is_speech = False
                
        return onsets

    def _measure_rise_time(self, envelope_db: np.ndarray, onset: Onset, sr: int, silence_thresh: float, speech_thresh: float) -> float:
        # Find the exact point it crosses silence threshold
        start_idx = onset.frame_index
        while start_idx > 0 and envelope_db[start_idx] > silence_thresh:
            start_idx -= 1
            
        # Find the point it crosses speech threshold
        end_idx = onset.frame_index
        while end_idx < len(envelope_db) and envelope_db[end_idx] < speech_thresh:
            end_idx += 1
            
        if end_idx >= len(envelope_db):
            return 100.0 # Invalid
            
        frames = end_idx - start_idx
        return frames * self.config.hop_length_ms

    def _check_onset_phase_chaos(self, audio: np.ndarray, sr: int, onset: Onset) -> bool:
        """
        Check for chaotic phase signature of natural glottal burst.
        Natural speech onsets (especially plosives) have high phase entropy
        due to turbulent airflow. Synthetic onsets are often "too clean".
        """
        onset_samples = int(onset.time * sr)
        window_len = int(0.02 * sr) # 20ms
        if onset_samples + window_len > len(audio):
            return True # Cannot check, assume natural
            
        window = audio[onset_samples:onset_samples + window_len]
        
        # Compute phase entropy
        fft = np.fft.fft(window * np.hanning(len(window)))
        phase = np.angle(fft[:len(fft)//2])
        phase_derivative = np.diff(np.unwrap(phase))
        
        # High entropy = natural chaos, low entropy = synthetic
        entropy = self._compute_entropy(phase_derivative)
        
        return entropy > 2.5  # Threshold from empirical analysis

    def _compute_entropy(self, x: np.ndarray) -> float:
        hist, _ = np.histogram(x, bins=50, density=True)
        hist = hist[hist > 0]
        return -np.sum(hist * np.log(hist))

    def _detect_hard_cuts(self, envelope_db: np.ndarray, audio: np.ndarray, sr: int) -> List[Dict]:
        """
        Detect unnatural "hard cut" endings lacking room decay.
        """
        violations = []
        
        # Find offsets (speech -> silence)
        # Similar logic to onsets but reversed
        is_speech = False
        offsets = []
        
        for i in range(len(envelope_db) - 1):
             if envelope_db[i] > self.SPEECH_THRESHOLD_DB:
                 is_speech = True
             elif is_speech and envelope_db[i] < self.SILENCE_THRESHOLD_DB:
                 # Potential offset
                 time = i * self.config.hop_length_ms / 1000.0
                 offsets.append(Onset(time=time, frame_index=i)) # Reusing Onset struct for simplicity
                 is_speech = False


        for offset in offsets:
            decay_time_ms = self._measure_decay_time(envelope_db, offset)
            
            # Smart Hard Cut Logic (2025-12-09)
            # Differentiate "Noise Gate" (Benign) from "Synthetic Chop" (Malicious)
            
            if decay_time_ms < 10:
                # Check energy level just before the cut (at the offset frame)
                # Ensure index is within bounds
                idx = min(offset.frame_index, len(envelope_db) - 1)
                pre_cut_energy = envelope_db[idx]
                
                # "High Energy Cut" Threshold
                # If energy is loud (> -40dB) and cuts instantly, it's suspicious.
                # If energy is quiet (< -40dB) and cuts, it's likely a noise gate.
                SUSPICIOUS_CUT_THRESHOLD_DB = -40.0 
                
                if pre_cut_energy > SUSPICIOUS_CUT_THRESHOLD_DB:
                    violations.append({
                        'type': 'hard_cut_ending',
                        'severity': 'high',
                        'time': offset.time,
                        'observed_decay_ms': decay_time_ms,
                        'pre_cut_energy_db': float(pre_cut_energy),
                        'explanation': f"Unnatural mid-speech termination at {offset.time:.2f}s. "
                                       f"Signal cuts from {pre_cut_energy:.1f}dB to silence in {decay_time_ms:.1f}ms. "
                                       f"Likely synthetic generation artifact."
                    })
                else:
                    # Log as info/low severity but DO NOT flag as violation that affects score
                    # This is the "Smart" ignoring of Noise Gates
                    logger.debug(f"Ignored potential noise gate cut at {offset.time:.2f}s (Energy: {pre_cut_energy:.1f}dB)")

        return violations

    def _measure_decay_time(self, envelope_db: np.ndarray, offset: Onset) -> float:
         # Find point it drops below speech threshold (moving backwards)
         start_idx = offset.frame_index
         while start_idx > 0 and envelope_db[start_idx] < self.SPEECH_THRESHOLD_DB:
             start_idx -= 1
             
         # Find point it drops below silence threshold (moving forwards)
         end_idx = offset.frame_index
         while end_idx < len(envelope_db) and envelope_db[end_idx] > self.SILENCE_THRESHOLD_DB:
             end_idx += 1
             
         frames = end_idx - start_idx
         return frames * self.config.hop_length_ms

    def _compute_score(self, violations: List[Dict]) -> float:
        if not violations:
            return 0.0
        # Simple scoring: more violations = higher score
        # Cap at 1.0
        return min(1.0, len(violations) * 0.6)
