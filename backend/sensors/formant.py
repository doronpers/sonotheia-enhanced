"""
Formant trajectory sensor inspired by SFAT-Net.

The sensor tracks F0/F1/F2 trajectories and flags regions where the dynamics
violate smooth physiological constraints that are hard for neural TTS systems
to reproduce after telephony compression.

PATENT SAFE IMPLEMENTATION:
- Uses Cepstral Analysis (Homomorphic Filtering) for spectral envelope estimation.
- STRICTLY AVOIDS Linear Predictive Coding (LPC).
- Focuses on trajectory velocity (dF/dt), not static values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np
from scipy import signal

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_LIBROSA = False

from .base import BaseSensor, SensorResult


def _frame_audio(audio: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    if not HAS_LIBROSA or len(audio) < frame_length:
        num_frames = max(1, (len(audio) - frame_length) // hop_length + 1)
        frames = np.zeros((num_frames, frame_length), dtype=np.float32)
        for idx in range(num_frames):
            start = idx * hop_length
            end = start + frame_length
            frame = audio[start:end]
            if len(frame) < frame_length:
                frame = np.pad(frame, (0, frame_length - len(frame)))
            frames[idx] = frame * np.hamming(frame_length)
        return frames
    framed = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length).T
    return framed * np.hamming(frame_length)


def _estimate_formants_cepstral(frame: np.ndarray, samplerate: int) -> Tuple[float, float, float]:
    """
    Estimate formants using Cepstral Analysis (Homomorphic Filtering).
    PATENT SAFE: Does NOT use LPC.
    """
    if np.max(np.abs(frame)) < 1e-3:
        return 500.0, 1500.0, 2500.0

    # 1. Compute Log Magnitude Spectrum
    n_fft = 1024
    spectrum = np.fft.rfft(frame, n=n_fft)
    log_spectrum = np.log(np.abs(spectrum) + 1e-10)

    # 2. Compute Real Cepstrum (IDFT of Log Spectrum)
    cepstrum = np.fft.irfft(log_spectrum)

    # 3. Lifter the Cepstrum (Low-pass filter in quefrency domain)
    # Keep only low quefrencies to represent the spectral envelope (vocal tract)
    # Discard high quefrencies which represent the excitation (glottal source)
    lifter_cutoff = 15 # Adjust based on expected F0 range
    liftered_cepstrum = np.zeros_like(cepstrum)
    liftered_cepstrum[:lifter_cutoff] = cepstrum[:lifter_cutoff]
    liftered_cepstrum[-lifter_cutoff+1:] = cepstrum[-lifter_cutoff+1:] # Symmetry

    # 4. Compute Spectral Envelope (DFT of liftered cepstrum)
    envelope = np.abs(np.fft.rfft(liftered_cepstrum, n=n_fft))
    
    # 5. Find Peaks in the Envelope
    freqs_bins = np.fft.rfftfreq(n_fft, d=1/samplerate)
    peaks, _ = signal.find_peaks(envelope)
    
    formant_freqs = freqs_bins[peaks]
    
    # Filter reasonable formant ranges (50Hz - 5000Hz)
    formant_freqs = formant_freqs[(formant_freqs > 50) & (formant_freqs < 5000)]
    
    # Sort and pick top 3
    formant_freqs = np.sort(formant_freqs)
    
    defaults = [500.0, 1500.0, 2500.0]
    if len(formant_freqs) < 3:
        # Pad with defaults if not enough peaks found
        formant_freqs = np.concatenate([formant_freqs, defaults[len(formant_freqs):]])
        
    return tuple(formant_freqs[:3].tolist())


@dataclass
class FormantTrajectorySensor(BaseSensor):
    """Sensor detecting implausible F0/Formant trajectories."""

    window_ms: float = 30.0
    hop_ms: float = 15.0
    deviation_threshold: float = 220.0  # Hz jump allowed between adjacent frames
    max_anomaly_ratio: float = 0.25

    def __post_init__(self):
        super().__init__("formant_trajectory")

    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=self.max_anomaly_ratio,
                detail="Invalid or empty audio input",
            )

        frame_length = max(32, int(self.window_ms / 1000 * samplerate))
        hop_length = max(16, int(self.hop_ms / 1000 * samplerate))
        frames = _frame_audio(audio_data, frame_length, hop_length)
        
        segments: List[dict] = []
        f0_track = self._estimate_f0(audio_data, samplerate, hop_length, frame_length)

        for idx, frame in enumerate(frames):
            # Use Cepstral Analysis instead of LPC
            f1, f2, f3 = _estimate_formants_cepstral(frame, samplerate)
            
            f0_val = f0_track[idx] if idx < len(f0_track) else None
            segments.append(
                {
                    "index": idx,
                    "start_s": round((idx * hop_length) / samplerate, 3),
                    "end_s": round(((idx * hop_length) + frame_length) / samplerate, 3),
                    "f0": None if f0_val is None else round(float(f0_val), 2),
                    "f1": round(f1, 2),
                    "f2": round(f2, 2),
                    "f3": round(f3, 2),
                }
            )

        anomaly_ratio, jump_counts = self._compute_anomaly_ratio(segments)
        passed = anomaly_ratio <= self.max_anomaly_ratio
        detail = (
            "Formant trajectories stable across utterance."
            if passed
            else f"{jump_counts} abrupt trajectory jumps detected (ratio={anomaly_ratio:.2f})."
        )

        metadata = {
            "segments": segments[:128],  # cap payload
            "anomaly_ratio": round(anomaly_ratio, 3),
            "jump_counts": jump_counts,
            "window_ms": self.window_ms,
            "hop_ms": self.hop_ms,
        }

        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=round(anomaly_ratio, 3),
            threshold=self.max_anomaly_ratio,
            detail=detail,
            metadata=metadata,
            reason=None if passed else "FORMANT_DYNAMICS_ANOMALY",
        )

    def _estimate_f0(
        self,
        audio: np.ndarray,
        samplerate: int,
        hop_length: int,
        frame_length: int,
    ) -> List[Optional[float]]:
        if not HAS_LIBROSA:
            return [None] * max(1, len(audio) // hop_length)
        f0, _, _ = librosa.pyin(
            audio,
            fmin=60,
            fmax=400,
            sr=samplerate,
            frame_length=frame_length,
            hop_length=hop_length,
        )
        # Replace NaNs with previous value for smoother trace
        cleaned = []
        last_valid = None
        for value in f0:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                cleaned.append(last_valid)
            else:
                cleaned.append(float(value))
                last_valid = float(value)
        return cleaned

    def _compute_anomaly_ratio(self, segments: List[dict]) -> Tuple[float, int]:
        if len(segments) < 2:
            return 0.0, 0
        f1 = np.array([seg["f1"] for seg in segments])
        f2 = np.array([seg["f2"] for seg in segments])
        f3 = np.array([seg["f3"] for seg in segments])

        jump_mask = (
            (np.abs(np.diff(f1)) > self.deviation_threshold)
            | (np.abs(np.diff(f2)) > self.deviation_threshold * 0.8)
            | (np.abs(np.diff(f3)) > self.deviation_threshold * 0.6)
        )
        jump_counts = int(jump_mask.sum())
        anomaly_ratio = jump_counts / max(1, len(segments) - 1)
        for idx, is_jump in enumerate(jump_mask):
            if is_jump:
                segments[idx]["anomaly"] = True
        return anomaly_ratio, jump_counts
