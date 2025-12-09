# Underutilized Opportunities & New Sensor Detection Methods

**Analysis Date:** December 9, 2025
**Status:** Trial Implementation Recommendations
**Priority:** High - Accuracy Enhancement Initiative

---

## Executive Summary

This document identifies **underutilized detection opportunities** and **new sensor methods** that could significantly improve Sonotheia's deepfake detection accuracy. The analysis reveals:

1. **2 existing sensors not activated** in the default pipeline (ENF, Breathing Pattern)
2. **1 disabled sensor** needing calibration improvements (Two-Mouth)
3. **3 low-weight sensors** that may be undervalued
4. **4 new sensor candidates** based on speech science literature

**Estimated Impact:** Implementing these recommendations could improve detection accuracy by 10-25% while maintaining patent safety.

---

## Part 1: Underutilized Existing Sensors

### 1.1 ENF Sensor (Electrical Network Frequency) ⭐⭐⭐⭐⭐

**Status:** Implemented but NOT in default pipeline
**Location:** `backend/sensors/enf.py` (327 lines)
**Trial Priority:** HIGH

#### The Opportunity

The ENF sensor is fully implemented but **not registered** in `get_default_sensors()`. This is a significant missed opportunity because:

- **Unique differentiator**: No known competitor uses ENF for voice deepfake detection
- **Complementary signal**: Detects environmental authenticity, not voice characteristics
- **Hard to spoof**: Attackers would need to synthesize correct grid frequency variations

#### How It Works

```
Real recordings from electrical devices contain 50/60Hz power grid frequency
embedded in the audio. This frequency varies slightly over time with grid load.

Detection Strategy:
1. Extract narrow-band signal around 50/60Hz
2. Analyze frequency stability (real = natural variations)
3. Check phase continuity (synthetic = discontinuities)
4. Compare to known ENF databases (future: geolocation verification)
```

#### Patent Safety

✅ **SAFE** - ENF analysis is:
- Not covered by Pindrop patents (focuses on voice, not environmental signals)
- Uses frequency-domain analysis, not LPC
- Independent of source-filter modeling

#### Recommended Trial Implementation

```python
# In backend/sensors/registry.py, add to get_default_sensors():
from .enf import ENFSensor

return [
    # ... existing sensors ...
    ENFSensor(category="defense"),  # Trust (Environmental Authenticity)
]
```

#### Expected Benefits

| Metric | Current | With ENF |
|--------|---------|----------|
| Mobile recordings detection | Medium | High |
| Studio/clean deepfakes | Weak | Strong |
| Geographic verification | None | Possible |

#### Caveats

- Requires minimum 2 seconds of audio
- May not work for recordings made on battery-powered devices
- Regional configuration needed (50Hz vs 60Hz)

---

### 1.2 Breathing Pattern Sensor (Regularity Analysis) ⭐⭐⭐⭐

**Status:** Implemented but NOT in default pipeline
**Location:** `backend/sensors/breathing_pattern.py` (335 lines)
**Trial Priority:** HIGH

#### The Opportunity

This sensor analyzes breathing **regularity**, complementing the existing `BreathSensor` which checks phonation duration. Key insight:

- **Real breathing**: Naturally irregular timing (coefficient of variation > 0.3)
- **Synthetic breathing**: Often unnaturally regular or absent

#### How It Works

```
1. Bandpass filter audio to 20-300Hz (breathing frequency range)
2. Detect breath events using energy envelope peaks
3. Calculate inter-breath interval variance
4. High variance = irregular = authentic
5. Low variance = regular = synthetic

Includes SNR gating to reject noisy recordings.
```

#### Patent Safety

✅ **SAFE** - Uses:
- Spectral filtering (not LPC)
- Temporal pattern analysis (not source-filter)
- Energy envelope detection

#### Recommended Trial Implementation

```python
# In backend/sensors/registry.py:
from .breathing_pattern import BreathingPatternSensor

return [
    # ... existing sensors ...
    BreathingPatternSensor(category="defense"),  # Trust (Natural Variability)
]
```

#### Expected Benefits

| Scenario | Current Detection | With Breathing Pattern |
|----------|-------------------|------------------------|
| TTS with no breathing | Medium (breath sensor) | High |
| TTS with regular breathing | Low | High |
| Clone with irregular breathing | Correct (REAL) | Correct (REAL) |

---

### 1.3 Two-Mouth Sensor (Needs Calibration) ⭐⭐⭐

**Status:** In pipeline but effectively disabled (50% accuracy)
**Location:** `backend/sensors/two_mouth.py` (189 lines)
**Trial Priority:** MEDIUM (after calibration)

#### The Problem

The Two-Mouth sensor detects "anatomical state conflicts" where acoustic features imply contradictory physiological states. However, current thresholds cause:

- 50% false positive rate on real speech
- Disabled in production via arbiter rules

#### Root Cause Analysis

```python
# Current thresholds (too aggressive):
score = min(1.0, max(0.0, (cv - 0.10) * 10))  # VTL variance
score = min(1.0, max(0.0, (conflict_rate - 0.05) * 10))  # Spectral conflict
```

The 0.10 CV threshold for VTL variance is too tight—real speech with emotion, emphasis, or prosodic variation can exceed this.

#### Recommended Calibration

1. **Relax VTL variance threshold**: `0.10 → 0.15`
2. **Relax spectral conflict rate**: `0.05 → 0.08`
3. **Reduce weight in fusion**: `0.15 → 0.08`
4. **Add voice activity gating**: Only analyze voiced segments

```python
# Proposed threshold adjustments:
score = min(1.0, max(0.0, (cv - 0.15) * 8))  # More permissive
score = min(1.0, max(0.0, (conflict_rate - 0.08) * 8))
```

#### Expected Impact After Calibration

| Metric | Before | After |
|--------|--------|-------|
| False Positive Rate | 50% | <15% |
| True Positive Rate | High | High (maintained) |
| Usable in Production | No | Yes |

---

### 1.4 Low-Weight Sensors Analysis

#### Coarticulation Sensor (Weight: 0.05)

**Current State:** Active but minimal influence
**Opportunity:** May be undervalued

The coarticulation sensor detects impossible articulation speeds—a strong synthetic indicator. Current low weight may be due to:
- Conservative tuning during initial development
- Lack of calibration data

**Recommendation:** Trial at 0.10 weight with A/B testing.

#### Breath Sensor (Weight: 0 → fallback 0.30)

**Current State:** Using fallback weight system
**Opportunity:** Simplify weight configuration

**Recommendation:** Set explicit weight of 0.15 instead of relying on fallback logic.

#### Bandwidth Sensor (Weight: 0 → fallback 0.20)

**Current State:** Using fallback weight system
**Opportunity:** Clarify sensor's role

**Recommendation:** Set explicit weight of 0.10 for full-bandwidth audio quality check.

---

## Part 2: New Sensor Candidates for Trial Implementation

### 2.1 Spectral Harmonicity Sensor (HNR) ⭐⭐⭐⭐⭐

**Status:** Not implemented (mentioned in ROADMAP.md)
**Effort:** Medium (2-3 days)
**Trial Priority:** HIGHEST

#### The Physics

Human voice has a characteristic **Harmonic-to-Noise Ratio (HNR)**:
- Real voice: HNR typically 8-25 dB for vowels
- TTS artifacts: Often show abnormally high HNR (too clean)
- Voice conversion: May show abnormally low HNR (artifacts as noise)

#### Detection Strategy

```python
class SpectralHarmonicitySensor(BaseSensor):
    """
    Measures Harmonic-to-Noise Ratio to detect TTS artifacts.

    The Physics:
    - Human voice has natural jitter/shimmer creating baseline noise
    - TTS often produces "too perfect" harmonics (high HNR)
    - Voice conversion may introduce artifacts (low HNR)

    Detection:
    - Extract F0 contour using autocorrelation
    - Separate harmonic and noise components
    - Calculate HNR per frame
    - Flag if HNR variance is too low (synthetic consistency)
    """

    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        # 1. Extract F0 using autocorrelation (NOT LPC)
        f0_contour = self._extract_f0_autocorrelation(audio_data, samplerate)

        # 2. Calculate frame-wise HNR
        hnr_values = self._calculate_hnr(audio_data, samplerate, f0_contour)

        # 3. Analyze HNR statistics
        mean_hnr = np.mean(hnr_values)
        hnr_variance = np.var(hnr_values)

        # 4. Flag synthetic patterns:
        #    - Abnormally high mean HNR (too clean)
        #    - Abnormally low HNR variance (too consistent)
        synthetic_score = 0.0
        if mean_hnr > 20.0:  # Too clean
            synthetic_score += 0.4
        if hnr_variance < 5.0:  # Too consistent
            synthetic_score += 0.4

        return SensorResult(...)
```

#### Patent Safety

✅ **SAFE**:
- Uses autocorrelation for F0 (not LPC)
- Analyzes noise characteristics (not source-filter)
- Measures statistical properties (not spectral templates)

#### Expected Impact

| Deepfake Type | Current Detection | With HNR |
|---------------|-------------------|----------|
| High-quality TTS | Medium | High |
| Neural vocoders | Low | High |
| Voice conversion | Medium | High |

---

### 2.2 Micro-Prosody Sensor (Jitter/Shimmer) ⭐⭐⭐⭐

**Status:** Not implemented
**Effort:** Medium (2-3 days)
**Trial Priority:** HIGH

#### The Physics

Natural voice has micro-variations called **jitter** (frequency perturbation) and **shimmer** (amplitude perturbation):

- **Jitter**: Cycle-to-cycle F0 variation (healthy range: 0.5-1.0%)
- **Shimmer**: Cycle-to-cycle amplitude variation (healthy range: 3-7%)

Synthetic voices often have:
- Too little jitter/shimmer (TTS)
- Abnormal jitter/shimmer patterns (voice conversion)

#### Detection Strategy

```python
class MicroProsodySensor(BaseSensor):
    """
    Analyzes voice quality micro-perturbations (jitter/shimmer).

    The Physics:
    - Real voice has natural F0/amplitude micro-variations
    - TTS produces too-smooth pitch contours
    - Voice conversion introduces characteristic artifacts

    Patent Safety: Uses cycle-to-cycle analysis (kinematic), not LPC.
    """

    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        # 1. Extract voiced segments
        voiced_frames = self._extract_voiced(audio_data, samplerate)

        # 2. Calculate local jitter (cycle-to-cycle F0 variation)
        jitter = self._calculate_jitter(voiced_frames, samplerate)

        # 3. Calculate local shimmer (cycle-to-cycle amplitude variation)
        shimmer = self._calculate_shimmer(voiced_frames)

        # 4. Score based on expected ranges
        # Too low jitter/shimmer = synthetic
        # Abnormal patterns = artifacts
```

#### Patent Safety

✅ **SAFE**:
- Cycle-to-cycle analysis (kinematic)
- No spectral modeling required
- Uses time-domain perturbation measures

---

### 2.3 Prosodic Velocity Sensor (F0 Dynamics) ⭐⭐⭐⭐

**Status:** Not implemented
**Effort:** Low (1-2 days)
**Trial Priority:** HIGH

#### The Physics

Extends the existing **Pitch Velocity Sensor** to analyze F0 contour dynamics more comprehensively:

- **F0 acceleration**: Rate of pitch change velocity
- **F0 reset patterns**: How pitch resets between phrases
- **Declination patterns**: Natural pitch lowering over utterances

#### Detection Strategy

```python
class ProsodicVelocitySensor(BaseSensor):
    """
    Analyzes pitch contour dynamics for naturalness.

    Complements PitchVelocitySensor by examining:
    - F0 acceleration (second derivative)
    - Phrase-boundary pitch patterns
    - Natural declination trends

    Patent Safety: Uses velocity/acceleration (kinematics), not static values.
    """

    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        # 1. Extract F0 contour
        f0 = self._extract_f0(audio_data, samplerate)

        # 2. Calculate F0 velocity (already done by PitchVelocitySensor)
        f0_velocity = np.gradient(f0)

        # 3. Calculate F0 acceleration (new)
        f0_acceleration = np.gradient(f0_velocity)

        # 4. Check acceleration limits (human physiology)
        # Max laryngeal acceleration ~50 semitones/sec²
        max_acceleration = np.max(np.abs(f0_acceleration))

        # 5. Analyze phrase patterns
        declination = self._analyze_declination(f0)
```

#### Patent Safety

✅ **SAFE**: Uses kinematic analysis (derivatives), not static spectral values.

---

### 2.4 Temporal Envelope Sensor (Attack/Decay) ⭐⭐⭐

**Status:** Not implemented
**Effort:** Low (1-2 days)
**Trial Priority:** MEDIUM

#### The Physics

Complements the **Glottal Inertia Sensor** by analyzing the complete temporal envelope:

- **Attack time**: How quickly sounds begin
- **Decay time**: How sounds fade
- **Attack-decay ratio**: Characteristic of different phonemes

#### Detection Strategy

```python
class TemporalEnvelopeSensor(BaseSensor):
    """
    Analyzes attack/decay patterns of audio segments.

    The Physics:
    - Biological articulators have inertia affecting attack/decay
    - Different phonemes have characteristic envelope shapes
    - Synthetic audio may have unnatural envelope patterns

    Complements GlottalInertiaSensor with broader envelope analysis.
    """
```

#### Patent Safety

✅ **SAFE**: Temporal envelope analysis is kinematic/dynamic, not spectral.

---

## Part 3: Implementation Roadmap

### Phase 1: Quick Wins (Week 1)

| Task | Effort | Impact | Risk |
|------|--------|--------|------|
| Activate ENF Sensor | 1 hour | High | Low |
| Activate Breathing Pattern Sensor | 1 hour | High | Low |
| Adjust sensor weights | 2 hours | Medium | Low |

### Phase 2: Calibration (Week 2)

| Task | Effort | Impact | Risk |
|------|--------|--------|------|
| Two-Mouth threshold tuning | 4 hours | High | Medium |
| Coarticulation weight testing | 4 hours | Medium | Low |
| A/B testing framework | 8 hours | High | Low |

### Phase 3: New Sensors (Weeks 3-4)

| Task | Effort | Impact | Risk |
|------|--------|--------|------|
| Spectral Harmonicity Sensor | 16 hours | High | Medium |
| Micro-Prosody Sensor | 16 hours | High | Medium |
| Prosodic Velocity Sensor | 8 hours | Medium | Low |
| Temporal Envelope Sensor | 8 hours | Medium | Low |

---

## Part 4: Testing Strategy

### Calibration Dataset Requirements

Current dataset: ~50 samples (insufficient)

**Recommended expansion:**

| Category | Current | Target | Source |
|----------|---------|--------|--------|
| Real speech | ~25 | 200 | Common Voice, LibriSpeech |
| TTS synthetic | ~15 | 100 | Various TTS engines |
| Voice conversion | ~10 | 50 | Voice cloning services |
| Real with noise | 0 | 50 | Augmented real samples |

### A/B Testing Framework

```python
# Proposed testing approach:
class SensorABTest:
    def __init__(self, sensor_a: BaseSensor, sensor_b: BaseSensor):
        self.sensor_a = sensor_a
        self.sensor_b = sensor_b

    def run_comparison(self, test_samples: List[LabeledSample]):
        results_a = []
        results_b = []

        for sample in test_samples:
            result_a = self.sensor_a.analyze(sample.audio, sample.sr)
            result_b = self.sensor_b.analyze(sample.audio, sample.sr)

            results_a.append((result_a.passed, sample.is_real))
            results_b.append((result_b.passed, sample.is_real))

        return self.calculate_metrics(results_a, results_b)
```

---

## Part 5: Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| New sensors decrease accuracy | Medium | High | A/B testing, gradual rollout |
| ENF not present in all recordings | High | Medium | Make optional, document limitations |
| Breathing pattern fails on short audio | High | Low | Minimum duration check (exists) |
| Two-Mouth still too aggressive | Medium | Medium | Conservative threshold adjustment |

### Patent Risks

| New Sensor | Patent Risk | Mitigation |
|------------|-------------|------------|
| Spectral Harmonicity | Low | Uses autocorrelation, not LPC |
| Micro-Prosody | Low | Kinematic analysis only |
| Prosodic Velocity | Low | Extends existing safe approach |
| Temporal Envelope | Low | Time-domain only |

All proposed sensors use **kinematic/dynamic analysis** (velocities, accelerations, variances) rather than **static spectral values**, maintaining the patent-safe "Motor-Planning & Phase-Physics Model."

---

## Appendix A: Configuration Changes

### Recommended settings.yaml Updates

```yaml
sensors:
  enf:
    enabled: true
    nominal_frequency: 60.0  # 50.0 for EU/Asia
    min_duration_sec: 2.0
    category: "defense"
    weight: 0.08

  breathing_pattern:
    enabled: true
    min_variance: 0.3
    snr_threshold_db: 10.0
    category: "defense"
    weight: 0.08

  two_mouth:
    enabled: true  # Re-enable after calibration
    vtl_variance_threshold: 0.15  # Relaxed from 0.10
    spectral_conflict_threshold: 0.08  # Relaxed from 0.05
    category: "prosecution"
    weight: 0.08  # Reduced from 0.15

  coarticulation:
    weight: 0.10  # Increased from 0.05

  # New sensors (Phase 3)
  spectral_harmonicity:
    enabled: false  # Enable after implementation
    hnr_max_threshold: 20.0
    hnr_variance_min: 5.0
    category: "prosecution"
    weight: 0.12
```

---

## Appendix B: Quick Activation Script

```python
# Script to activate underutilized sensors for trial
# Run: python scripts/activate_trial_sensors.py

def update_registry():
    """Add ENF and Breathing Pattern sensors to default pipeline."""

    # Backup current registry.py
    # Edit get_default_sensors() to include:

    new_imports = """
from .enf import ENFSensor
from .breathing_pattern import BreathingPatternSensor
"""

    new_sensors = """
        ENFSensor(category="defense"),              # Trust (Environmental)
        BreathingPatternSensor(category="defense"), # Trust (Natural Timing)
"""

    print("Add to backend/sensors/registry.py:")
    print(new_imports)
    print("Add to sensor list:")
    print(new_sensors)

if __name__ == "__main__":
    update_registry()
```

---

## Conclusion

The Sonotheia codebase contains **significant untapped detection potential**:

1. **2 fully-implemented sensors** (ENF, Breathing Pattern) can be activated immediately
2. **1 disabled sensor** (Two-Mouth) can be rehabilitated with calibration
3. **4 new sensor candidates** can expand detection coverage within 2-4 weeks

The recommended approach is:
1. **Week 1**: Activate existing sensors, adjust weights
2. **Week 2**: Calibrate Two-Mouth, build A/B testing framework
3. **Weeks 3-4**: Implement Spectral Harmonicity and Micro-Prosody sensors
4. **Ongoing**: Expand calibration dataset, measure accuracy improvements

All recommendations maintain **patent safety** by using kinematic/dynamic analysis rather than static spectral or LPC-based methods.

---

**Document Maintainer:** Sonotheia Development Team
**Next Review:** After Phase 1 implementation
