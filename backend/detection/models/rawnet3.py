"""
RawNet3 Model

Deep learning model for end-to-end audio deepfake detection.
Based on sinc filters and residual blocks for raw waveform processing.
"""

import logging
from typing import Dict, Optional, Tuple, Any
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class SincConv(nn.Module):
    """Sinc-based convolutional layer for raw waveform processing."""

    def __init__(
        self,
        out_channels: int,
        kernel_size: int,
        sample_rate: int = 16000,
        in_channels: int = 1,
        stride: int = 1,
        padding: int = 0,
        min_low_hz: float = 50,
        min_band_hz: float = 50,
    ):
        super().__init__()

        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.sample_rate = sample_rate
        self.stride = stride
        self.padding = padding

        # Ensure odd kernel size
        if kernel_size % 2 == 0:
            kernel_size = kernel_size + 1

        self.kernel_size = kernel_size

        # Initialize filterbank parameters
        low_hz = min_low_hz
        high_hz = sample_rate / 2 - min_band_hz

        # Mel scale initialization
        mel = self._hz_to_mel(torch.linspace(low_hz, high_hz, out_channels + 1))
        hz = self._mel_to_hz(mel)

        # Learnable parameters
        self.low_hz_ = nn.Parameter(hz[:-1].unsqueeze(1))
        self.band_hz_ = nn.Parameter((hz[1:] - hz[:-1]).unsqueeze(1))

        # Hamming window
        n_lin = torch.linspace(0, kernel_size / 2 - 1, kernel_size // 2)
        window = 0.54 - 0.46 * torch.cos(2 * np.pi * n_lin / kernel_size)
        self.register_buffer("window", window)

        # Time axis
        n = (kernel_size - 1) / 2
        t = 2 * np.pi * torch.arange(-n, n + 1) / sample_rate
        self.register_buffer("t", t)

    def _hz_to_mel(self, hz: torch.Tensor) -> torch.Tensor:
        """Convert Hz to Mel scale."""
        return 2595 * torch.log10(1 + hz / 700)

    def _mel_to_hz(self, mel: torch.Tensor) -> torch.Tensor:
        """Convert Mel scale to Hz."""
        return 700 * (10 ** (mel / 2595) - 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through sinc filterbank."""
        # Compute filter frequencies
        low = self.low_hz_
        high = torch.clamp(low + torch.abs(self.band_hz_), 50, self.sample_rate / 2)
        low = torch.clamp(low, 50, self.sample_rate / 2 - 50)

        # Compute bandpass filters
        f_times_t_low = self.t * low
        f_times_t_high = self.t * high

        band_pass_left = (
            (torch.sin(f_times_t_high) - torch.sin(f_times_t_low))
            / (self.t / 2 + 1e-8)
        )
        band_pass_center = 2 * (high - low)
        band_pass_right = (
            (torch.sin(f_times_t_high) - torch.sin(f_times_t_low))
            / (self.t / 2 + 1e-8)
        )

        # Combine and apply window
        band_pass = torch.cat(
            [band_pass_left, band_pass_center, band_pass_right], dim=1
        )
        band_pass = band_pass / (2 * band_pass_center + 1e-8)

        # Reshape for convolution
        filters = band_pass.view(self.out_channels, 1, self.kernel_size)

        return F.conv1d(
            x, filters, stride=self.stride, padding=self.padding, groups=1
        )


class ResidualBlock(nn.Module):
    """Residual block with batch normalization."""

    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()

        self.conv1 = nn.Conv1d(
            in_channels, out_channels, kernel_size=3, stride=stride, padding=1
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.conv2 = nn.Conv1d(
            out_channels, out_channels, kernel_size=3, stride=1, padding=1
        )
        self.bn2 = nn.BatchNorm1d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm1d(out_channels),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through residual block."""
        out = F.leaky_relu(self.bn1(self.conv1(x)), 0.3)
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.leaky_relu(out, 0.3)
        return out


class AttentionPooling(nn.Module):
    """Self-attention pooling layer."""

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply attention pooling.

        Args:
            x: Input tensor (batch, time, features)

        Returns:
            Pooled tensor (batch, features)
        """
        attn_weights = F.softmax(self.attention(x), dim=1)
        return (attn_weights * x).sum(dim=1)


class RawNet3(nn.Module):
    """
    RawNet3 architecture for audio deepfake detection.

    Processes raw audio waveforms using sinc filters and residual blocks.
    """

    def __init__(
        self,
        sinc_out_channels: int = 128,
        sinc_kernel_size: int = 251,
        encoder_channels: list = None,
        num_classes: int = 2,
        attention_dim: int = 128,
        sample_rate: int = 16000,
    ):
        super().__init__()

        if encoder_channels is None:
            encoder_channels = [128, 256, 512, 512]

        # Sinc convolution front-end
        self.sinc_conv = SincConv(
            out_channels=sinc_out_channels,
            kernel_size=sinc_kernel_size,
            sample_rate=sample_rate,
            padding=sinc_kernel_size // 2,
        )
        self.bn_sinc = nn.BatchNorm1d(sinc_out_channels)
        self.pool_sinc = nn.MaxPool1d(3)

        # Encoder blocks
        self.encoder_blocks = nn.ModuleList()
        in_ch = sinc_out_channels
        for out_ch in encoder_channels:
            self.encoder_blocks.append(
                nn.Sequential(
                    ResidualBlock(in_ch, out_ch, stride=2),
                    ResidualBlock(out_ch, out_ch),
                )
            )
            in_ch = out_ch

        # Attention pooling
        self.attention_pool = AttentionPooling(encoder_channels[-1], attention_dim)

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(encoder_channels[-1], 256),
            nn.LeakyReLU(0.3),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(
        self, x: torch.Tensor, return_embedding: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass through RawNet3.

        Args:
            x: Input waveform (batch, samples) or (batch, 1, samples)
            return_embedding: Whether to return intermediate embedding

        Returns:
            Tuple of (logits, embedding if return_embedding else None)
        """
        # Ensure 3D input
        if x.dim() == 2:
            x = x.unsqueeze(1)

        # Sinc convolution
        x = self.sinc_conv(x)
        x = F.leaky_relu(self.bn_sinc(x), 0.3)
        x = self.pool_sinc(x)

        # Encoder
        for block in self.encoder_blocks:
            x = block(x)

        # Attention pooling (reshape to batch, time, features)
        x = x.transpose(1, 2)
        embedding = self.attention_pool(x)

        # Classification
        logits = self.classifier(embedding)

        if return_embedding:
            return logits, embedding
        return logits, None

    def get_score(self, x: torch.Tensor) -> torch.Tensor:
        """Get spoof probability score.

        Args:
            x: Input waveform

        Returns:
            Spoof probability (0=genuine, 1=spoof)
        """
        logits, _ = self.forward(x)
        probs = F.softmax(logits, dim=-1)
        return probs[:, 1]  # Return spoof class probability


class RawNet3Detector:
    """
    RawNet3-based detector wrapper with model loading and inference.

    DEMO MODE: In demo mode, returns placeholder scores without running the model.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "auto",
        demo_mode: bool = True,
        sample_rate: int = 16000,
    ):
        """
        Initialize RawNet3 detector.

        Args:
            model_path: Path to model weights (None for random initialization)
            device: Device to use ("cpu", "cuda", or "auto")
            demo_mode: Whether to use demo mode (placeholder scores)
            sample_rate: Expected audio sample rate
        """
        self.demo_mode = demo_mode
        self.sample_rate = sample_rate
        self.model = None
        self.device = self._get_device(device)

        if not demo_mode:
            self._load_model(model_path)

        logger.info(
            f"RawNet3Detector initialized: demo_mode={demo_mode}, device={self.device}"
        )

    def _get_device(self, device: str) -> torch.device:
        """Determine device to use."""
        if device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            return torch.device("cpu")
        return torch.device(device)

    def _load_model(self, model_path: Optional[str]) -> None:
        """Load model weights."""
        self.model = RawNet3(sample_rate=self.sample_rate)

        if model_path and Path(model_path).exists():
            try:
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                logger.info(f"Loaded model weights from {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load model weights: {e}")
                logger.warning("Using random initialization")

        self.model = self.model.to(self.device)
        self.model.eval()

    def detect(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Run detection on audio.

        Args:
            audio: Audio waveform (numpy array)

        Returns:
            Detection result with score and confidence
        """
        if self.demo_mode:
            return self._demo_detect(audio)

        return self._model_detect(audio)

    def _demo_detect(self, audio: np.ndarray) -> Dict[str, Any]:
        """Demo mode detection with placeholder scores."""
        # Generate deterministic but varied score based on audio characteristics
        if audio is None or len(audio) == 0:
            score = 0.5
        else:
            # Use audio statistics to generate consistent demo score
            audio_mean = np.mean(np.abs(audio))
            audio_std = np.std(audio)
            score = 0.15 + 0.1 * (audio_mean / (audio_std + 1e-8))
            score = float(np.clip(score, 0.0, 1.0))

        return {
            "score": score,
            "confidence": 0.85,
            "is_spoof": score > 0.5,
            "demo_mode": True,
            "message": "DEMO MODE - placeholder score, not for production",
        }

    def _model_detect(self, audio: np.ndarray) -> Dict[str, Any]:
        """Run actual model detection."""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        with torch.no_grad():
            if audio.ndim == 2:
                if audio.shape[0] <= audio.shape[1]:
                    audio = audio.mean(axis=0)
                else:
                    audio = audio.mean(axis=1)
            x = torch.from_numpy(audio).float().unsqueeze(0).to(self.device)
            score = self.model.get_score(x)
            score = float(score.cpu().numpy()[0])

        return {
            "score": score,
            "confidence": min(abs(score - 0.5) * 2 + 0.5, 1.0),
            "is_spoof": score > 0.5,
            "demo_mode": False,
        }

    def detect_batch(self, audio_list: list) -> list:
        """
        Run detection on multiple audio samples.

        Args:
            audio_list: List of audio waveforms

        Returns:
            List of detection results
        """
        return [self.detect(audio) for audio in audio_list]
