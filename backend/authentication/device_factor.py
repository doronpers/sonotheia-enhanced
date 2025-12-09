"""
Device Authentication Factor Module
Handles device trust validation and fingerprinting
"""

from typing import Dict
import logging

logger = logging.getLogger(__name__)


class DeviceValidator:
    """Device trust factor validator"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.require_enrollment = config.get('require_enrollment', True)
        self.trust_score_threshold = config.get('trust_score_threshold', 0.8)
        self.demo_mode = config.get('demo_mode', True)
        logger.info(f"DeviceValidator initialized with trust_threshold={self.trust_score_threshold}, "
                   f"demo_mode={self.demo_mode}")
    
    def validate(self, device_data: Dict, customer_id: str) -> bool:
        """
        Validate device trust
        Returns True if device is trusted, False otherwise
        """
        if not device_data:
            logger.warning(f"No device data provided for customer {customer_id}")
            return False
        
        device_id = device_data.get('device_id')
        if not device_id:
            logger.warning(f"No device_id in device data for customer {customer_id}")
            return False
        
        # Check if device is enrolled
        is_enrolled = self._check_enrollment(device_id, customer_id)
        
        if self.require_enrollment and not is_enrolled:
            logger.info(f"Device {device_id} not enrolled for customer {customer_id}")
            return False
        
        # Calculate trust score based on various factors
        trust_score = self._calculate_trust_score(device_data, customer_id)
        
        logger.info(f"Device {device_id} trust score: {trust_score}")
        return trust_score >= self.trust_score_threshold
    
    def _check_enrollment(self, device_id: str, customer_id: str) -> bool:
        """
        Check if device is enrolled for customer
        
        DEMO MODE: This is a placeholder that always returns True.
        In production, implement proper device enrollment validation.
        
        TODO: Integrate with device enrollment database
        """
        if self.demo_mode:
            logger.warning("Using demo mode for device enrollment - always returns True")
            return True
        else:
            # TODO: In production, query device enrollment database
            raise NotImplementedError("Production device enrollment check not implemented")
    
    def _calculate_trust_score(self, device_data: Dict, customer_id: str) -> float:
        """
        Calculate device trust score based on various factors
        Returns score from 0.0 to 1.0
        """
        score = 0.5  # Base score
        
        # Factor 1: Device enrollment history
        if self._check_enrollment(device_data.get('device_id'), customer_id):
            score += 0.3
        
        # Factor 2: Device reputation (no malware, no jailbreak)
        if device_data.get('integrity_check', True):
            score += 0.1
        
        # Factor 3: Location consistency
        if device_data.get('location_consistent', True):
            score += 0.1
        
        return min(score, 1.0)
    
    def get_details(self, device_data: Dict, customer_id: str) -> Dict:
        """
        Get detailed device validation results
        """
        device_id = device_data.get('device_id', 'unknown')
        is_trusted = self.validate(device_data, customer_id)
        trust_score = self._calculate_trust_score(device_data, customer_id)
        
        return {
            'device_trusted': is_trusted,
            'device_id': device_id,
            'trust_score': trust_score,
            'decision': 'PASS' if is_trusted else 'FAIL',
            'explanation': 'Known device' if is_trusted else 'New/unknown device'
        }
