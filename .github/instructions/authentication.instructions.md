---
applyTo: "backend/authentication/**/*.py"
---

# Authentication Component Guidelines

## MFA Orchestrator

### Purpose
The MFA Orchestrator is the central decision engine for multi-factor authentication. It evaluates multiple authentication factors (voice, device, behavioral) and makes authentication decisions based on configured policies.

### Decision Flow
1. Evaluate transaction context (amount, country, channel)
2. Determine required authentication factors based on risk
3. Validate provided factors
4. Calculate combined confidence score
5. Apply business rules and policies
6. Return decision: APPROVE, DENY, or STEP_UP

### Implementation Requirements

#### Factor Evaluation
- Each factor must return a confidence score between 0.0 and 1.0
- Include evidence and reasoning in factor results
- Handle missing factors gracefully
- Support factor combinations (e.g., voice + device)

#### Risk Assessment
```python
def assess_risk(self, context: TransactionContext) -> str:
    """
    Assess transaction risk level.
    
    Returns:
        Risk level: 'low', 'medium', or 'high'
    """
    # Consider amount, country, beneficiary status, etc.
    pass
```

#### Authentication Decision
```python
def authenticate(
    self, 
    context: TransactionContext, 
    factors: AuthenticationFactors
) -> dict:
    """
    Make authentication decision.
    
    Args:
        context: Transaction and user context
        factors: Provided authentication factors
        
    Returns:
        {
            'decision': 'APPROVE' | 'DENY' | 'STEP_UP',
            'confidence': float,
            'factors_evaluated': list[dict],
            'risk_level': str,
            'reason': str,
            'recommendations': list[str]
        }
    """
    pass
```

### Policy Rules

#### Risk-Based Requirements
- Low risk (< $5k): 2 factors from same category OK
- Medium risk ($5k-$25k): 2 factors, prefer different categories
- High risk (> $25k): 3 factors, must include voice

#### Geographic Rules
- High-risk countries require additional scrutiny
- Cross-border transfers need enhanced validation
- Maintain country risk list in config

#### Transaction Patterns
- New beneficiary transactions require higher confidence
- Large amounts need multiple factors
- Unusual patterns trigger step-up authentication

## Voice Authentication

### Core Capabilities
1. **Deepfake Detection**: Identify synthetic/manipulated audio
2. **Speaker Verification**: Match voice to enrolled voiceprint
3. **Liveness Detection**: Ensure audio is live, not replayed
4. **Quality Assessment**: Verify audio quality for reliable processing

### Implementation Pattern

```python
class VoiceAuthenticator:
    """Voice authentication with deepfake detection."""
    
    def __init__(self, config: dict):
        """Initialize with configuration."""
        self.deepfake_threshold = config['voice']['deepfake_threshold']
        self.speaker_threshold = config['voice']['speaker_threshold']
        self.min_quality = config['voice']['min_quality']
    
    async def authenticate(
        self, 
        audio_data: np.ndarray, 
        user_id: str,
        context: dict = None
    ) -> dict:
        """
        Authenticate voice sample.
        
        Returns:
            {
                'passed': bool,
                'confidence': float,
                'deepfake_score': float,
                'speaker_score': float,
                'quality_score': float,
                'evidence': dict,
                'reason': str
            }
        """
        pass
```

### Deepfake Detection
- Extract acoustic features (MFCC, spectral features)
- Analyze frequency artifacts
- Check temporal consistency
- Detect GAN/TTS artifacts
- Return confidence score (higher = more likely synthetic)

### Speaker Verification
- Extract voice embeddings/features
- Compare to enrolled voiceprint
- Calculate similarity score
- Account for channel/noise variations
- Return match confidence

### Quality Checks
- Check sample rate (prefer 16kHz)
- Assess signal-to-noise ratio
- Detect clipping/distortion
- Verify minimum duration
- Reject poor quality samples early

### Error Handling
- Handle invalid audio formats
- Manage missing voiceprints
- Deal with corrupted audio data
- Provide actionable error messages

## Device Authentication

### Purpose
Validate that the device used for the transaction is trusted and properly enrolled.

### Device Trust Factors
1. **Device Recognition**: Is device previously seen?
2. **Device Integrity**: Is device tampered/rooted/jailbroken?
3. **Behavioral Consistency**: Usage patterns match history?
4. **Geolocation**: Location consistent with user profile?

### Implementation Pattern

```python
class DeviceValidator:
    """Device trust validation."""
    
    def validate(
        self, 
        device_info: dict, 
        user_id: str
    ) -> dict:
        """
        Validate device trust.
        
        Args:
            device_info: Device fingerprint and metadata
            user_id: User identifier
            
        Returns:
            {
                'passed': bool,
                'trust_score': float,
                'is_enrolled': bool,
                'risk_factors': list[str],
                'evidence': dict
            }
        """
        pass
```

### Device Fingerprinting
- Hardware identifiers (IMEI, serial, etc.)
- Software configuration (OS, browser, app version)
- Network information (IP, WiFi MAC)
- Screen resolution, timezone, language
- Installed apps/extensions (when available)

### Trust Scoring
- Known device: higher base score
- Consistent behavior: increase score
- Suspicious changes: decrease score
- Geolocation anomalies: flag for review
- Device integrity issues: automatic failure

### Enrollment Flow
- First-time device requires explicit enrollment
- Collect comprehensive device fingerprint
- Associate with user account
- Set initial trust score (usually lower)
- Increase trust over time with consistent use

## Behavioral Factors

### Typing Dynamics
- Keystroke timing patterns
- Error rates and corrections
- Typing speed consistency
- Compare to historical baseline

### Navigation Patterns
- Mouse movement characteristics
- Touch gestures (mobile)
- Navigation flow through app
- Time spent on screens

### Transaction Patterns
- Typical transaction times
- Usual transaction amounts
- Preferred payment methods
- Historical beneficiary patterns

## Testing Authentication Components

### Unit Tests
```python
def test_voice_rejects_synthetic():
    """Test voice authenticator rejects synthetic voice."""
    authenticator = VoiceAuthenticator(config)
    synthetic_audio = load_synthetic_sample()
    
    result = await authenticator.authenticate(
        synthetic_audio, 
        user_id="test_user"
    )
    
    assert result['passed'] is False
    assert result['deepfake_score'] > config['voice']['deepfake_threshold']
    assert 'synthetic' in result['reason'].lower()
```

### Integration Tests
```python
def test_mfa_orchestrator_high_risk_transaction():
    """Test orchestrator requires 3 factors for high-risk transaction."""
    orchestrator = MFAOrchestrator(config)
    
    context = TransactionContext(
        amount_usd=75000,  # High amount
        transaction_type='wire_transfer',
        is_new_beneficiary=True
    )
    
    # Provide only 2 factors
    factors = AuthenticationFactors(
        voice={'audio_data': valid_audio},
        device={'device_id': 'known_device'}
    )
    
    result = orchestrator.authenticate(context, factors)
    
    assert result['decision'] == 'STEP_UP'
    assert 'additional factor' in result['reason'].lower()
```

### Mock Data
- Create realistic test audio samples
- Mock device fingerprints
- Simulate various risk scenarios
- Test edge cases (network failures, timeouts)

## Security Considerations

### Sensitive Data
- Never log audio content
- Redact PII in logs
- Encrypt voiceprints at rest
- Use secure channels for transmission

### Rate Limiting
- Limit authentication attempts per user
- Throttle by IP address
- Block after suspicious patterns
- Implement exponential backoff

### Audit Logging
- Log all authentication attempts
- Record decision rationale
- Include timestamps and context
- Enable forensic analysis

### Demo Mode Safety
- Never use real user data in demo
- Add clear watermarks to outputs
- Use synthetic audio samples
- Disable actual authentication in demo

## Configuration

### Thresholds
- Set appropriate confidence thresholds
- Balance security vs. user friction
- Monitor false positive/negative rates
- Adjust based on feedback

### Policy Configuration
```yaml
authentication_policy:
  minimum_factors: 2
  require_different_categories: true
  
  risk_thresholds:
    low:
      factors_required: 2
      max_amount_usd: 5000
    medium:
      factors_required: 2
      max_amount_usd: 25000
    high:
      factors_required: 3
      max_amount_usd: 100000
```

## Performance Optimization

### Async Operations
- Use async/await for I/O operations
- Process factors in parallel when possible
- Set reasonable timeouts
- Handle timeouts gracefully

### Caching
- Cache enrolled voiceprints
- Cache device trust scores (with TTL)
- Cache user behavioral baselines
- Invalidate cache on profile changes

### Resource Management
- Limit concurrent authentications
- Clean up temporary audio files
- Release ML model memory after use
- Monitor memory usage
