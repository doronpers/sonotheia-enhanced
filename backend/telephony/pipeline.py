"""
Telephony Codec Simulation Pipeline

Simulates various telephony codecs and channel effects for robust deepfake detection.
"""

import numpy as np
from scipy import signal
import logging

logger = logging.getLogger(__name__)


class TelephonyPipeline:
    """Simulate telephony codec effects on audio"""

    @staticmethod
    def apply_bandpass_filter(audio: np.ndarray, sr: int, low_freq: float = 300.0, high_freq: float = 3400.0) -> np.ndarray:
        """
        Apply bandpass filter to simulate narrowband telephony

        Args:
            audio: Input audio array
            sr: Sample rate
            low_freq: Lower cutoff frequency (Hz)
            high_freq: Upper cutoff frequency (Hz)

        Returns:
            Filtered audio
        """
        # Design Butterworth bandpass filter
        nyquist = sr / 2
        low = low_freq / nyquist
        high = high_freq / nyquist

        # Ensure frequencies are in valid range
        low = max(0.001, min(low, 0.999))
        high = max(0.001, min(high, 0.999))

        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, audio)

        return filtered

    @staticmethod
    def g711_ulaw_quantize(audio: np.ndarray, mu: float = 255.0) -> np.ndarray:
        """
        Apply G.711 μ-law quantization

        Args:
            audio: Input audio array (normalized to [-1, 1])
            mu: μ-law compression parameter

        Returns:
            Quantized audio
        """
        # μ-law compression
        sign = np.sign(audio)
        abs_audio = np.abs(audio)

        # Compress
        compressed = sign * np.log1p(mu * abs_audio) / np.log1p(mu)

        # Quantize to 8-bit (256 levels)
        quantized = np.round(compressed * 127).astype(np.int8)

        # Expand back
        expanded = quantized.astype(np.float32) / 127

        # μ-law expansion
        sign = np.sign(expanded)
        abs_expanded = np.abs(expanded)
        decompressed = sign * (np.exp(abs_expanded * np.log1p(mu)) - 1) / mu

        return decompressed

    @staticmethod
    def g711_alaw_quantize(audio: np.ndarray, A: float = 87.6) -> np.ndarray:
        """
        Apply G.711 A-law quantization

        Args:
            audio: Input audio array (normalized to [-1, 1])
            A: A-law compression parameter

        Returns:
            Quantized audio
        """
        sign = np.sign(audio)
        abs_audio = np.abs(audio)

        # A-law compression
        compressed = np.zeros_like(abs_audio)
        threshold = 1.0 / A

        # Two regions
        low_mask = abs_audio < threshold
        high_mask = ~low_mask

        compressed[low_mask] = A * abs_audio[low_mask] / (1 + np.log(A))
        compressed[high_mask] = (1 + np.log(A * abs_audio[high_mask])) / (1 + np.log(A))

        compressed = sign * compressed

        # Quantize to 8-bit
        quantized = np.round(compressed * 127).astype(np.int8)

        # Expand back
        expanded = quantized.astype(np.float32) / 127
        sign = np.sign(expanded)
        abs_expanded = np.abs(expanded)

        # A-law expansion
        decompressed = np.zeros_like(abs_expanded)
        threshold_exp = 1.0 / (1 + np.log(A))

        low_mask = abs_expanded < threshold_exp
        high_mask = ~low_mask

        decompressed[low_mask] = abs_expanded[low_mask] * (1 + np.log(A)) / A
        decompressed[high_mask] = np.exp(abs_expanded[high_mask] * (1 + np.log(A)) - 1) / A

        decompressed = sign * decompressed

        return decompressed

    @staticmethod
    def simulate_packet_loss(audio: np.ndarray, sr: int, loss_rate: float = 0.05, packet_size_ms: float = 20.0) -> np.ndarray:
        """
        Simulate packet loss in VoIP

        Args:
            audio: Input audio array
            sr: Sample rate
            loss_rate: Probability of packet loss (0-1)
            packet_size_ms: Packet size in milliseconds

        Returns:
            Audio with simulated packet loss
        """
        # Calculate packet size in samples
        packet_size = int(sr * packet_size_ms / 1000)
        num_packets = len(audio) // packet_size

        result = audio.copy()

        # Randomly drop packets
        for i in range(num_packets):
            if np.random.random() < loss_rate:
                start_idx = i * packet_size
                end_idx = min((i + 1) * packet_size, len(audio))

                # Simple packet loss concealment: repeat previous packet or fill with zeros
                if i > 0:
                    prev_start = (i - 1) * packet_size
                    prev_end = i * packet_size
                    result[start_idx:end_idx] = result[prev_start:prev_end][:end_idx-start_idx]
                else:
                    result[start_idx:end_idx] = 0

        return result

    @staticmethod
    def apply_landline_chain(audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply landline telephony effects

        Args:
            audio: Input audio
            sr: Sample rate

        Returns:
            Processed audio simulating landline telephony
        """
        logger.info("Applying landline codec chain")

        # Bandpass filter (300-3400 Hz)
        audio = TelephonyPipeline.apply_bandpass_filter(audio, sr, 300, 3400)

        # A-law quantization (common in Europe)
        audio = TelephonyPipeline.g711_alaw_quantize(audio)

        return audio

    @staticmethod
    def apply_mobile_chain(audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply mobile telephony effects

        Args:
            audio: Input audio
            sr: Sample rate

        Returns:
            Processed audio simulating mobile telephony
        """
        logger.info("Applying mobile codec chain")

        # Slightly wider bandpass (200-3800 Hz for modern mobile)
        audio = TelephonyPipeline.apply_bandpass_filter(audio, sr, 200, 3800)

        # μ-law quantization (common in North America)
        audio = TelephonyPipeline.g711_ulaw_quantize(audio)

        return audio

    @staticmethod
    def apply_voip_chain(audio: np.ndarray, sr: int, packet_loss_rate: float = 0.02) -> np.ndarray:
        """
        Apply VoIP telephony effects

        Args:
            audio: Input audio
            sr: Sample rate
            packet_loss_rate: Packet loss probability

        Returns:
            Processed audio simulating VoIP
        """
        logger.info("Applying VoIP codec chain")

        # Bandpass filter (50-7000 Hz for wideband VoIP)
        audio = TelephonyPipeline.apply_bandpass_filter(audio, sr, 50, 7000)

        # Simulate packet loss
        audio = TelephonyPipeline.simulate_packet_loss(audio, sr, packet_loss_rate, packet_size_ms=20.0)

        # Light quantization (VoIP codecs are better than G.711 but still lossy)
        audio = TelephonyPipeline.g711_ulaw_quantize(audio)

        return audio

    @staticmethod
    def apply_codec_by_name(audio: np.ndarray, sr: int, codec_name: str) -> np.ndarray:
        """
        Apply codec by name

        Args:
            audio: Input audio
            sr: Sample rate
            codec_name: One of 'landline', 'mobile', 'voip', 'clean'

        Returns:
            Processed audio
        """
        if codec_name == 'landline':
            return TelephonyPipeline.apply_landline_chain(audio, sr)
        elif codec_name == 'mobile':
            return TelephonyPipeline.apply_mobile_chain(audio, sr)
        elif codec_name == 'voip':
            return TelephonyPipeline.apply_voip_chain(audio, sr)
        elif codec_name == 'clean':
            return audio
        else:
            raise ValueError(f"Unknown codec: {codec_name}")
