"""
Analyze Call Endpoint - Full MVP Pipeline

Implements the complete call analysis pipeline integrating:
- Audio loading and codec simulation
- Feature extraction
- Physics-based spoof detection
- Factor-level risk scoring
- SAR narrative generation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import numpy as np
import tempfile
import logging
from pathlib import Path
import sys
import io
import base64
import yaml

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from data_ingest.loader import AudioLoader
from telephony.pipeline import TelephonyPipeline
from features.extraction import FeatureExtractor
from models.baseline import GMMSpoofDetector
from risk_engine.factors import RiskEngine, FactorScore, RiskResult
from api.middleware import limiter, verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


class CallMetadata(BaseModel):
    """Metadata for call analysis"""
    call_id: str = Field(..., description="Unique call identifier")
    customer_id: str = Field(..., description="Customer identifier")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    amount_usd: Optional[float] = Field(None, gt=0, description="Transaction amount if applicable")
    destination_country: Optional[str] = Field(None, description="Destination country")
    channel: str = Field(default="phone", description="Call channel (phone, voip, etc.)")
    codec: str = Field(default="landline", description="Codec to simulate: landline, mobile, voip, clean")


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    call_id: str
    risk_result: RiskResult
    audio_metadata: Dict[str, Any]
    visualization_data: Dict[str, Any]
    sar_narrative: Optional[str] = None


class CallAnalyzer:
    """Main call analysis pipeline"""

    def __init__(self, model_path: Optional[str] = None, config_path: Optional[Path] = None):
        """
        Initialize analyzer

        Args:
            model_path: Optional path to trained spoof detection model
        """
        # Load config
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"

        voice_cfg = {}
        if config_path.exists():
            try:
                with open(config_path) as f:
                    settings = yaml.safe_load(f)
                    voice_cfg = settings.get("voice", {})
            except Exception as e:  # pragma: no cover - defensive logging
                logger.warning(f"Could not load settings from {config_path}: {e}")

        self.sample_rate = voice_cfg.get("sample_rate", 16000)
        self.feature_types = voice_cfg.get("feature_types", ["lfcc", "logspec"])
        self.codec_default = voice_cfg.get("codec", "landline")
        self.spoof_threshold = voice_cfg.get("deepfake_threshold", 0.30)

        self.loader = AudioLoader(target_sr=self.sample_rate)
        self.telephony = TelephonyPipeline()
        self.feature_extractor = FeatureExtractor(sr=self.sample_rate)
        self.spoof_detector = GMMSpoofDetector()

        # Try to load model if path provided
        self.model_loaded = False

        resolved_model_path = Path(model_path) if model_path else Path(voice_cfg.get("model_path", ""))
        if resolved_model_path and resolved_model_path.exists():
            try:
                self.spoof_detector.load(str(resolved_model_path))
                self.model_loaded = True
                logger.info(f"Loaded spoof detection model from {resolved_model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")

    def analyze_call(
        self,
        audio_data: bytes,
        metadata: CallMetadata
    ) -> AnalysisResult:
        """
        Run full analysis pipeline on audio call

        Args:
            audio_data: Raw audio bytes
            metadata: Call metadata

        Returns:
            Complete analysis result
        """
        logger.info(f"Analyzing call: {metadata.call_id}")

        # Step 1: Load audio
        audio, sr = self.loader.load_from_bytes(audio_data)
        duration = len(audio) / sr

        logger.info(f"Loaded audio: duration={duration:.2f}s, sr={sr}")

        # Step 2: Apply codec simulation
        codec_name = metadata.codec or self.codec_default
        if codec_name not in ['landline', 'mobile', 'voip', 'clean']:
            logger.warning(f"Unknown codec {codec_name}, using {self.codec_default}")
            codec_name = self.codec_default

        audio_coded = self.telephony.apply_codec_by_name(audio, sr, codec_name)

        logger.info(f"Applied {codec_name} codec simulation")

        # Step 3: Extract features
        features = self.feature_extractor.extract_feature_stack(
            audio_coded,
            feature_types=['lfcc', 'logspec']
        )

        logger.info(f"Extracted features: shape={features.shape}")

        # Step 4: Predict spoof score
        if self.model_loaded:
            spoof_score = self.spoof_detector.predict_score(features)
        else:
            # Placeholder: use simple heuristic based on feature statistics
            spoof_score = self._placeholder_spoof_score(features)
            logger.warning("No trained model, using placeholder spoof score")

        logger.info(f"Spoof score: {spoof_score:.3f}")

        # Step 5: Create factor-level risk assessment
        factors = self._create_factors(spoof_score, codec_name, metadata)
        risk_result = RiskEngine.compute_overall_risk(factors)

        # Step 6: Generate visualization data
        viz_data = self._create_visualization_data(audio, audio_coded, sr)

        # Step 7: Generate SAR narrative if high risk
        sar_narrative = None
        if risk_result.risk_level in ['HIGH', 'CRITICAL']:
            sar_narrative = self._generate_sar_narrative(metadata, risk_result)

        # Compile result
        result = AnalysisResult(
            call_id=metadata.call_id,
            risk_result=risk_result,
            audio_metadata={
                'duration_seconds': float(duration),
                'sample_rate': sr,
                'codec_applied': codec_name,
                'num_frames': features.shape[0],
                'feature_dims': features.shape[1]
            },
            visualization_data=viz_data,
            sar_narrative=sar_narrative
        )

        logger.info(f"Analysis complete: call_id={metadata.call_id}, risk={risk_result.overall_score:.3f}")

        return result

    def _create_factors(self, spoof_score: float, codec_name: str, metadata: CallMetadata) -> List[FactorScore]:
        """Create list of risk factors"""
        factors = []

        # Physics-based deepfake factor
        physics_factor = RiskEngine.create_physics_factor(
            spoof_score=spoof_score,
            codec_name=codec_name,
            threshold=self.spoof_threshold,
            weight=2.0
        )
        factors.append(physics_factor)

        # Placeholder ASV factor
        asv_factor = RiskEngine.create_asv_factor(score=0.15, weight=1.5)
        factors.append(asv_factor)

        # Placeholder liveness factor
        liveness_factor = RiskEngine.create_liveness_factor(score=0.10, weight=1.5)
        factors.append(liveness_factor)

        # Placeholder device factor
        device_factor = RiskEngine.create_device_factor(score=0.20, weight=1.0)
        factors.append(device_factor)

        return factors

    def _placeholder_spoof_score(self, features: np.ndarray) -> float:
        """
        Placeholder spoof score when no model is available

        Uses simple statistical features as a heuristic
        """
        # Use variance and entropy as simple indicators
        variance = np.var(features)
        mean_abs = np.mean(np.abs(features))

        # Normalize to [0, 1] range (very rough heuristic)
        score = min(1.0, max(0.0, variance / 100.0))

        return float(score)

    def _create_visualization_data(self, audio_orig: np.ndarray, audio_coded: np.ndarray, sr: int) -> Dict:
        """Create data for waveform and spectrogram visualization"""
        import librosa

        # Downsample for visualization (max 1000 points)
        max_points = 1000
        if len(audio_orig) > max_points:
            step = len(audio_orig) // max_points
            waveform_orig = audio_orig[::step][:max_points]
            waveform_coded = audio_coded[::step][:max_points]
        else:
            waveform_orig = audio_orig
            waveform_coded = audio_coded

        # Time axis
        time = np.linspace(0, len(audio_orig) / sr, len(waveform_orig))

        # Compute spectrograms
        spec_orig = librosa.stft(audio_orig, n_fft=512, hop_length=160)
        spec_coded = librosa.stft(audio_coded, n_fft=512, hop_length=160)

        # Log magnitude
        spec_orig_db = librosa.amplitude_to_db(np.abs(spec_orig), ref=np.max)
        spec_coded_db = librosa.amplitude_to_db(np.abs(spec_coded), ref=np.max)

        # Downsample spectrograms for visualization
        max_frames = 200
        if spec_orig_db.shape[1] > max_frames:
            step = spec_orig_db.shape[1] // max_frames
            spec_orig_db = spec_orig_db[:, ::step][:, :max_frames]
            spec_coded_db = spec_coded_db[:, ::step][:, :max_frames]

        viz_data = {
            'waveform': {
                'time': time.tolist(),
                'amplitude_original': waveform_orig.tolist(),
                'amplitude_coded': waveform_coded.tolist()
            },
            'spectrogram': {
                'original': spec_orig_db.tolist(),
                'coded': spec_coded_db.tolist(),
                'frequencies': librosa.fft_frequencies(sr=sr, n_fft=512).tolist()
            }
        }

        return viz_data

    def _generate_sar_narrative(self, metadata: CallMetadata, risk_result: RiskResult) -> str:
        """Generate SAR narrative for high-risk calls"""
        narrative = f"""
SUSPICIOUS ACTIVITY REPORT - VOICE DEEPFAKE DETECTION

CALL INFORMATION:
- Call ID: {metadata.call_id}
- Customer ID: {metadata.customer_id}
- Transaction ID: {metadata.transaction_id or 'N/A'}
- Amount: ${metadata.amount_usd:,.2f} USD (if applicable)
- Destination: {metadata.destination_country or 'N/A'}
- Channel: {metadata.channel}

RISK ASSESSMENT:
- Overall Risk Score: {risk_result.overall_score:.2%}
- Risk Level: {risk_result.risk_level}
- Recommended Decision: {risk_result.decision}

FACTOR ANALYSIS:
"""
        for factor in risk_result.factors:
            narrative += f"""
- {factor.name.upper()}:
  Score: {factor.score:.2%} (Weight: {factor.weight})
  {factor.explanation}
"""

        narrative += """
RECOMMENDATION:
Based on the risk factors above, this call requires {decision}.
Further investigation and manual review are recommended.

Generated by Sonotheia MVP - Physics-Based Voice Authentication System
"""
        narrative = narrative.format(decision=risk_result.decision)

        return narrative


# Global analyzer instance with trained model from settings
config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
model_path = Path(__file__).parent.parent / "models" / "gmm_test.pkl"
analyzer = CallAnalyzer(
    model_path=str(model_path) if model_path.exists() else None,
    config_path=config_path
)


@router.post(
    "/analyze_call",
    response_model=AnalysisResult,
    summary="Analyze Call for Deepfake Detection",
    description="Complete call analysis pipeline with physics-based spoof detection and risk scoring"
)
@limiter.limit("20/minute")
async def analyze_call(
    request: Request,
    audio_file: UploadFile = File(..., description="Audio file (WAV format)"),
    call_id: str = Form(..., description="Unique call identifier"),
    customer_id: str = Form(..., description="Customer identifier"),
    transaction_id: Optional[str] = Form(None, description="Transaction ID"),
    amount_usd: Optional[float] = Form(None, description="Transaction amount"),
    destination_country: Optional[str] = Form(None, description="Destination country"),
    channel: str = Form("phone", description="Call channel"),
    codec: str = Form("landline", description="Codec: landline, mobile, voip, clean"),
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Analyze audio call for deepfake detection

    **Pipeline:**
    1. Load audio file
    2. Apply telephony codec simulation
    3. Extract LFCC + log-spectrogram features
    4. Run physics-based spoof detection
    5. Compute factor-level risk scores
    6. Generate SAR narrative if high risk

    **Returns:**
    - Risk assessment with factor breakdown
    - Visualization data (waveform, spectrogram)
    - SAR narrative if applicable
    """
    try:
        # Read audio file
        audio_bytes = await audio_file.read()

        # Create metadata
        metadata = CallMetadata(
            call_id=call_id,
            customer_id=customer_id,
            transaction_id=transaction_id,
            amount_usd=amount_usd,
            destination_country=destination_country,
            channel=channel,
            codec=codec
        )

        # Run analysis
        result = analyzer.analyze_call(audio_bytes, metadata)

        return result

    except Exception as e:
        logger.error(f"Error analyzing call: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
