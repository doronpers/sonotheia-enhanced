"""
Enhanced MFA Orchestrator
Comprehensive multi-factor authentication with detailed factor validation,
risk scoring, and SAR trigger detection
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import base64
import yaml
from pathlib import Path

from .voice_factor import VoiceAuthenticator
from .device_factor import DeviceValidator

logger = logging.getLogger(__name__)


class AuthDecision(Enum):
    APPROVE = "APPROVE"
    DECLINE = "DECLINE"
    STEP_UP = "STEP_UP"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TransactionContext:
    """Transaction context for authentication"""
    transaction_id: str
    customer_id: str
    transaction_type: str
    amount_usd: float
    destination_country: str
    is_new_beneficiary: bool
    channel: str


@dataclass
class AuthenticationFactors:
    """Authentication factors to validate"""
    voice: Optional[Dict] = None
    device: Optional[Dict] = None
    knowledge: Optional[Dict] = None
    behavioral: Optional[Dict] = None


class MFAOrchestrator:
    """Multi-factor authentication decision engine."""
    
    def __init__(self, config: Optional[Dict] = None):
        if config is None:
            config = self._load_default_config()
        
        self.config = config
        
        # Initialize factor validators
        self.voice_auth = VoiceAuthenticator(config.get('voice', {}))
        self.device_validator = DeviceValidator(config.get('device', {}))
        
        logger.info("MFAOrchestrator initialized")
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from settings.yaml"""
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {
            'voice': {'deepfake_threshold': 0.3, 'speaker_threshold': 0.85},
            'device': {'trust_score_threshold': 0.8},
            'high_risk_countries': []
        }
    
    def authenticate(self, context: TransactionContext, 
                    factors: AuthenticationFactors) -> Dict:
        """Evaluate authentication request and make decision."""
        
        logger.info(f"Starting authentication for transaction {context.transaction_id}")
        
        # Step 1: Validate each provided factor
        factor_results = {}
        
        if factors.voice:
            factor_results['voice'] = self._validate_voice_factor(
                factors.voice, context
            )
        
        if factors.device:
            factor_results['device'] = self._validate_device_factor(
                factors.device, context
            )
        
        # Step 2: Compute transaction risk
        transaction_risk = self._compute_transaction_risk(
            context, factor_results
        )
        
        # Step 3: Apply MFA policy
        decision, confidence = self._apply_mfa_policy(
            factor_results, transaction_risk, context
        )
        
        # Step 4: Check if SAR investigation needed
        sar_flags = self._check_sar_triggers(context, factor_results)
        
        result = {
            'decision': decision.value,
            'confidence': confidence,
            'risk_score': transaction_risk['overall_risk'],
            'risk_level': transaction_risk['risk_level'].value,
            'factor_results': factor_results,
            'transaction_risk': transaction_risk,
            'sar_flags': sar_flags
        }
        
        logger.info(f"Authentication complete: {decision.value} with confidence {confidence}")
        return result
    
    def _validate_voice_factor(self, voice_data: Dict, 
                               context: TransactionContext) -> Dict:
        """Validate voice authentication factor."""
        logger.info("Validating voice factor")
        
        # Decode audio if base64 encoded
        audio_bytes = voice_data.get('audio_data')
        if isinstance(audio_bytes, str):
            try:
                audio_bytes = base64.b64decode(audio_bytes)
            except Exception as e:
                logger.error(f"Failed to decode audio data: {e}")
                return {
                    'decision': 'FAIL',
                    'explanation': 'Invalid audio data format'
                }
        
        # Use VoiceAuthenticator to validate
        return self.voice_auth.validate(audio_bytes, context.customer_id)
    
    def _validate_device_factor(self, device_data: Dict,
                               context: TransactionContext) -> Dict:
        """Validate device trust factor."""
        logger.info("Validating device factor")
        return self.device_validator.get_details(device_data, context.customer_id)
    
    def _compute_transaction_risk(self, context: TransactionContext,
                                  factor_results: Dict) -> Dict:
        """Compute overall transaction risk."""
        risk_score = 0.0
        risk_factors = []
        
        # High value adds risk
        if context.amount_usd > 50000:
            risk_score += 0.3
            risk_factors.append(f"High value transaction: ${context.amount_usd:,.2f}")
        elif context.amount_usd > 10000:
            risk_score += 0.2
            risk_factors.append(f"Medium value transaction: ${context.amount_usd:,.2f}")
        
        # New beneficiary adds risk
        if context.is_new_beneficiary:
            risk_score += 0.2
            risk_factors.append("New beneficiary")
        
        # High-risk country adds risk
        high_risk_countries = self.config.get('high_risk_countries', [])
        if context.destination_country in high_risk_countries:
            risk_score += 0.3
            risk_factors.append(f"High-risk destination: {context.destination_country}")
        
        # Failed factors add risk
        for factor, result in factor_results.items():
            if result.get('decision') == 'FAIL':
                risk_score += 0.3
                risk_factors.append(f"Failed {factor} authentication")
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return {
            'overall_risk': min(risk_score, 1.0),
            'risk_level': risk_level,
            'risk_factors': risk_factors
        }
    
    def _apply_mfa_policy(self, factor_results: Dict,
                         transaction_risk: Dict,
                         context: TransactionContext) -> Tuple[AuthDecision, float]:
        """Apply MFA policy to make authentication decision."""
        passed_factors = [
            f for f, r in factor_results.items() 
            if r.get('decision') == 'PASS'
        ]
        
        risk_level = transaction_risk['risk_level']
        
        # Rule 1: Insufficient factors
        if len(passed_factors) < 2:
            logger.info("Insufficient factors passed")
            return AuthDecision.DECLINE, 0.0
        
        # Rule 2: Voice factor MUST pass for high-value transactions
        if context.amount_usd > 10000:
            if 'voice' not in passed_factors:
                logger.info("Voice factor required for high-value transaction")
                return AuthDecision.STEP_UP, 0.0
        
        # Rule 3: Critical risk requires manual review
        if risk_level == RiskLevel.CRITICAL:
            logger.info("Critical risk level - manual review required")
            return AuthDecision.MANUAL_REVIEW, 0.5
        
        # Rule 4: High risk requires 3+ factors
        if risk_level == RiskLevel.HIGH:
            if len(passed_factors) < 3:
                logger.info("High risk requires additional factors")
                return AuthDecision.STEP_UP, 0.5
        
        # Rule 5: Compute overall confidence
        confidence = len(passed_factors) / max(len(factor_results), 2)
        
        if confidence > 0.7:
            return AuthDecision.APPROVE, confidence
        else:
            return AuthDecision.DECLINE, confidence
    
    def _check_sar_triggers(self, context: TransactionContext,
                           factor_results: Dict) -> List[str]:
        """Check if transaction triggers SAR investigation."""
        flags = []
        
        # Voice deepfake detected
        if 'voice' in factor_results:
            deepfake_score = factor_results['voice'].get('deepfake_score', 0)
            if deepfake_score > 0.7:
                flags.append('SYNTHETIC_VOICE_DETECTED')
        
        # High-value to high-risk jurisdiction
        if context.amount_usd > 50000:
            high_risk_countries = self.config.get('high_risk_countries', [])
            if context.destination_country in high_risk_countries:
                flags.append('HIGH_VALUE_HIGH_RISK_DESTINATION')
        
        # Multiple failed authentication factors
        failed_factors = [
            f for f, r in factor_results.items()
            if r.get('decision') == 'FAIL'
        ]
        if len(failed_factors) >= 2:
            flags.append('MULTIPLE_AUTHENTICATION_FAILURES')
        
        return flags
