"""
Unified Authentication Orchestrator
Combines patterns from auth-guide with existing detection logic
Created: 2025-11-23 by doronpers
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from enum import Enum
import logging
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
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
class UnifiedContext:
    """Combined context from all repos"""
    # Transaction data
    transaction_id: str
    customer_id: str
    amount_usd: float
    channel: str
    
    # Voice data (from SonoCheck/RecApp)
    voice_sample: Optional[bytes] = None
    voice_metadata: Optional[Dict] = None
    
    # Consent (from RecApp)
    has_consent: bool = False
    consent_timestamp: Optional[str] = None
    
    # Risk factors
    destination_country: str = "US"
    is_new_beneficiary: bool = False
    device_trusted: bool = True

class UnifiedOrchestrator:
    """Main orchestrator combining all authentication logic"""
    
    def __init__(self, config_path: str = "config/unified_config.yaml"):
        self.config = self._load_config(config_path)
        self._initialize_components()
        logger.info("Unified Orchestrator initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        # For now, return default config
        return {
            "mfa": {"min_factors": 2},
            "voice": {"deepfake_threshold": 0.3},
            "risk": {"high_value_threshold": 10000}
        }
    
    def _initialize_components(self):
        """Initialize detection components when available"""
        self.voice_detector = None  # Will import from SonoCheck
        self.consent_manager = None  # Will import from RecApp
        self.sar_generator = None  # Will implement from auth-guide
    
    async def authenticate(self, context: UnifiedContext) -> Dict:
        """Main authentication entry point"""
        logger.info(f"Starting authentication for transaction {context.transaction_id}")
        
        # Step 1: Check consent (from RecApp pattern)
        if not context.has_consent:
            return self._decline("No consent provided")
        
        # Step 2: Calculate risk score
        risk_score, risk_level = self._calculate_risk(context)
        
        # Step 3: Voice authentication if provided
        voice_result = None
        if context.voice_sample:
            voice_result = await self._check_voice(context.voice_sample)
        
        # Step 4: Make decision
        decision = self._make_decision(risk_level, voice_result, context)
        
        # Step 5: Check if SAR needed
        sar_required = self._check_sar_triggers(decision, risk_level, voice_result)
        
        return {
            "decision": decision.value,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "voice_result": voice_result,
            "sar_required": sar_required,
            "transaction_id": context.transaction_id,
            "timestamp": "2025-11-23T19:20:33Z"
        }
    
    def _calculate_risk(self, context: UnifiedContext) -> Tuple[float, RiskLevel]:
        """Calculate transaction risk"""
        risk = 0.0
        
        # Amount-based risk
        if context.amount_usd > 50000:
            risk += 0.4
        elif context.amount_usd > 10000:
            risk += 0.2
        
        # Other factors
        if context.is_new_beneficiary:
            risk += 0.2
        if not context.device_trusted:
            risk += 0.2
        
        # Determine level
        if risk >= 0.6:
            level = RiskLevel.CRITICAL
        elif risk >= 0.4:
            level = RiskLevel.HIGH
        elif risk >= 0.2:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        return min(risk, 1.0), level
    
    async def _check_voice(self, voice_sample: bytes) -> Dict:
        """Placeholder for voice detection"""
        # TODO: Import actual detection from SonoCheck
        return {
            "deepfake_score": 0.15,
            "liveness": True,
            "quality": 0.85
        }
    
    def _make_decision(self, risk_level: RiskLevel, 
                       voice_result: Optional[Dict],
                       context: UnifiedContext) -> AuthDecision:
        """Make authentication decision"""
        
        # High risk requires manual review
        if risk_level == RiskLevel.CRITICAL:
            return AuthDecision.MANUAL_REVIEW
        
        # Voice check failed
        if voice_result and voice_result.get("deepfake_score", 0) > 0.7:
            return AuthDecision.DECLINE
        
        # High value requires voice
        if context.amount_usd > 10000 and not voice_result:
            return AuthDecision.STEP_UP
        
        return AuthDecision.APPROVE
    
    def _check_sar_triggers(self, decision: AuthDecision,
                           risk_level: RiskLevel,
                           voice_result: Optional[Dict]) -> bool:
        """Check if SAR should be filed"""
        if decision == AuthDecision.DECLINE:
            return True
        if risk_level == RiskLevel.CRITICAL:
            return True
        if voice_result and voice_result.get("deepfake_score", 0) > 0.5:
            return True
        return False
    
    def _decline(self, reason: str) -> Dict:
        """Helper to decline with reason"""
        return {
            "decision": AuthDecision.DECLINE.value,
            "reason": reason,
            "sar_required": True
        }

# Test if running directly
if __name__ == "__main__":
    import asyncio
    
    async def test():
        orchestrator = UnifiedOrchestrator()
        test_context = UnifiedContext(
            transaction_id="TEST001",
            customer_id="CUST123",
            amount_usd=15000,
            channel="wire_transfer",
            has_consent=True
        )
        result = await orchestrator.authenticate(test_context)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
