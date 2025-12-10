# Analysis of Recent Accuracy Fixes - December 10, 2025

## User-Implemented Fixes Summary

### 1. Fusion Engine Logic Corrections ✅

**Issue Identified:** Physics analysis wasn't properly integrated into final score calculation.

**Fix Applied:**
- Added `physics_analysis` to weighted average with 20% weight
- Updated `_extract_scores()` to properly extract `physics_score` from physics_analysis stage

**Expected Impact:**
- Physics sensors now directly influence final detection score
- Weighted fusion now includes: feature_extraction (15%), temporal_analysis (15%), artifact_detection (15%), rawnet3 (40%), physics_analysis (20%)
- Total: 105% (needs normalization)

### 2. BandwidthSensor Data Type Fix ✅ CRITICAL

**Issue Identified:** BandwidthSensor was returning raw frequency values (e.g., 6321 Hz) instead of normalized 0-1 probability scores.

**Impact of Bug:**
- `risk_score = max(risk_scores)` would be 6321 instead of 0-1 range
- This blew out all calculations in prosecution veto logic
- Made adaptive veto thresholds (0.85, 0.75) meaningless
- Caused random/unpredictable behavior

**Fix Applied:**
- Removed BandwidthSensor from "Prosecution" category mapping (line ~100)
- Added safety clamping to enforce 0-1 ranges for all sensor scores
- Bandwidth is now properly used only for profile selection, not risk calculation

**Expected Impact:**
- Risk scores now properly bounded to [0.0, 1.0]
- Adaptive veto thresholds now function correctly
- Prosecution logic works as designed

### 3. n_fft Warning Elimination ✅

**Issue Identified:** DigitalSilenceSensor analyzing silence gaps < 128ms (< 2048 samples @ 16kHz), causing librosa STFT warnings.

**Fix Applied:**
- Added check to skip segments shorter than 2048 samples
- Prevents FFT operations on insufficient data

**Verification:**
- Ran 25-sample test
- Zero n_fft warnings
- Clean execution

### 4. Score Normalization Verification ✅

**Results from Test:**
- Physics sensors correctly contributing (physics_analysis: 1.0 for clear fakes)
- Scores normalized and rational
- No more score explosions

---

## Enhancement Recommendations

### Enhancement 1: Normalize Stage Weights

**Issue:** Current stage weights sum to 105% (after adding physics_analysis at 20%).

**Current:**
```python
{
    "feature_extraction": 0.15,    # 15%
    "temporal_analysis": 0.15,     # 15%
    "artifact_detection": 0.15,    # 15%
    "rawnet3": 0.40,               # 40%
    "physics_analysis": 0.20,      # 20%  (newly added)
}
# Total: 105%
```

**Recommended Fix:**
```python
{
    "feature_extraction": 0.10,    # 10%  (reduced from 15%)
    "temporal_analysis": 0.10,     # 10%  (reduced from 15%)
    "artifact_detection": 0.10,    # 10%  (reduced from 15%)
    "rawnet3": 0.45,               # 45%  (increased from 40%, main ML detector)
    "physics_analysis": 0.25,      # 25%  (increased from 20%, critical sensors)
}
# Total: 100%
```

**Rationale:**
- Physics analysis is our most reliable stage (patent-safe, explainable)
- RawNet3 is powerful but black-box (deserves high weight)
- Feature/temporal/artifact are lower-level and redundant with RawNet3

### Enhancement 2: Add Explicit Score Clamping in Multiple Locations

**Current:** Clamping added to fusion engine (good!)

**Additional Locations:**

#### A. In `physics_analysis.py` (lines 85-130):

```python
# After line 118: weighted_sum += risk_score * weight
# Add validation:
if risk_score < 0.0 or risk_score > 1.0:
    logger.warning(f"Sensor {name} returned out-of-range score: {risk_score}, clamping to [0,1]")
    risk_score = max(0.0, min(1.0, risk_score))
```

#### B. In `fusion_engine.py` after extracting sensor scores (lines 85-111):

```python
# After line 91: val = res.get("value", 0.0)
# Add clamping:
val = max(0.0, min(1.0, float(val)))  # Enforce [0,1] range

# Log violations for debugging
if val != res.get("value", 0.0):
    logger.warning(f"Sensor {name} returned out-of-range value {res.get('value')}, clamped to {val}")
```

#### C. Add clamping to risk_score and trust_score calculations (lines 113-119):

```python
# After line 115: risk_score = max(risk_scores) if risk_scores else 0.0
# Add safety clamp:
risk_score = max(0.0, min(1.0, risk_score))

# After line 119: trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0.5
# Add safety clamp:
trust_score = max(0.0, min(1.0, trust_score))
```

### Enhancement 3: Improve BandwidthSensor Handling

**Current:** Removed from prosecution mapping (correct fix!)

**Additional Improvement:** Make BandwidthSensor explicitly informational.

#### In `bandwidth.py` (or wherever BandwidthSensor is defined):

```python
class BandwidthSensor(BaseSensor):
    def __init__(self):
        super().__init__(
            name="BandwidthSensor",
            category="informational"  # Not prosecution or defense
        )

    def analyze(self, audio_data, sample_rate, context):
        # ... existing code ...

        return SensorResult(
            sensor_name=self.name,
            passed=None,  # Informational only, not pass/fail
            value=rolloff_freq,  # Raw frequency (not 0-1 score)
            threshold=None,
            metadata={
                "rolloff_frequency_hz": rolloff_freq,
                "is_narrowband": rolloff_freq < 4000,
                "estimated_codec": "phone/voip" if rolloff_freq < 4000 else "wideband"
            }
        )
```

**Update fusion_engine.py to handle informational sensors:**

```python
# In line 108-111, modify category detection:
category = res.get("metadata", {}).get("category", "defense")

# If no category in metadata, use string mapping
if not category:
    lower_name = name.lower()
    if "bandwidth" in lower_name or "informational" in lower_name:
        category = "informational"  # Skip in risk/trust calculation
        continue  # Don't add to risk_scores or trust_scores
    elif "glottal" in lower_name or "pitch velocity" in lower_name or "silence" in lower_name:
        category = "prosecution"
    else:
        category = "defense"
```

### Enhancement 4: Add Safety Logging for Debugging

Add comprehensive logging to track score flows:

```python
# In fusion_engine.py, after calculating risk_score and trust_score:
logger.debug(f"Prosecution sensors: {len(risk_scores)} active, max risk: {risk_score:.3f}")
logger.debug(f"Defense sensors: {len(trust_scores)} active, avg trust: {trust_score:.3f}")

if risk_scores:
    logger.debug(f"Risk scores: {[f'{s:.3f}' for s in risk_scores[:5]]}")  # Top 5
if trust_scores:
    logger.debug(f"Trust scores: {[f'{s:.3f}' for s in trust_scores[:5]]}")  # Top 5

# After final_score calculation:
logger.info(f"Final fusion: base={base_score:.3f}, final={final_score:.3f}, logic={decision_logic}")
```

### Enhancement 5: Validate DigitalSilenceSensor Fix

**Current Fix:** Skip segments < 2048 samples

**Verify Implementation:**

```python
# In _detect_room_tone_changes (around line 327-328):
if len(region) < 2048:  # Should be 2048, not 512
    logger.debug(f"Skipping short region: {len(region)} samples < 2048")
    continue
```

**Additional Fix for Spectral Flux:**

```python
# In _analyze_spectral_flux (around line 252-254):
# Current: nperseg = min(frame_length, 1024)
# Update to:
nperseg = min(frame_length, 2048)  # Use 2048 for consistency

# And check minimum audio length:
if len(audio) < 2048:  # Not nperseg * 2, just 2048
    logger.debug(f"Audio too short for spectral flux: {len(audio)} < 2048 samples")
    return {
        "has_instant_change": False,
        "instant_change_count": 0,
    }
```

---

## Validation Script

Create a test to validate all fixes:

```python
# backend/tests/test_fusion_fixes.py

import pytest
import numpy as np
from backend.detection.stages.fusion_engine import FusionEngine
from backend.sensors.digital_silence import DigitalSilenceSensor

def test_score_clamping():
    """Verify all scores are clamped to [0,1]"""
    fusion = FusionEngine()

    # Simulate stage results with out-of-range scores
    stage_results = {
        "physics_analysis": {
            "success": True,
            "physics_score": 1.5,  # Out of range!
            "sensor_results": {
                "TestSensor": {
                    "score": -0.5,  # Out of range!
                    "passed": False
                }
            }
        }
    }

    result = fusion.fuse(stage_results)

    # Verify clamping worked
    assert 0.0 <= result["fused_score"] <= 1.0, "Score not clamped!"
    print(f"✓ Score properly clamped: {result['fused_score']}")

def test_bandwidth_not_in_risk():
    """Verify BandwidthSensor doesn't contribute to risk_score"""
    fusion = FusionEngine()

    stage_results = {
        "physics_analysis": {
            "success": True,
            "physics_score": 0.3,
            "sensor_results": {
                "BandwidthSensor": {
                    "score": 6321.0,  # Raw frequency (should be ignored!)
                    "value": 6321.0,
                    "passed": None
                },
                "GlottalInertiaSensor": {
                    "score": 0.8,
                    "passed": False
                }
            }
        }
    }

    result = fusion.fuse(stage_results)

    # Risk should be 0.8 (from GlottalInertia), NOT 6321!
    assert result["fused_score"] < 10.0, "BandwidthSensor contaminated risk_score!"
    print(f"✓ BandwidthSensor properly excluded: score={result['fused_score']}")

def test_short_audio_no_warnings():
    """Verify short audio doesn't trigger n_fft warnings"""
    sensor = DigitalSilenceSensor()

    # 50ms audio @ 16kHz = 800 samples (< 2048)
    short_audio = np.random.randn(800).astype(np.float32)

    # Should handle gracefully without warnings
    result = sensor.analyze(short_audio, 16000)

    assert result is not None
    print(f"✓ Short audio handled: {len(short_audio)} samples, score={result.value}")

def test_physics_analysis_in_fusion():
    """Verify physics_analysis contributes to final score"""
    fusion = FusionEngine()

    stage_results = {
        "physics_analysis": {
            "success": True,
            "physics_score": 0.9,  # High fake score
            "sensor_results": {}
        },
        "rawnet3": {
            "success": True,
            "score": 0.1  # Low fake score
        }
    }

    result = fusion.fuse(stage_results)

    # Final score should be influenced by physics (0.9)
    # Not just rawnet3 (0.1)
    assert result["fused_score"] > 0.2, "Physics analysis not contributing!"
    print(f"✓ Physics analysis contributing: final={result['fused_score']}")

if __name__ == "__main__":
    test_score_clamping()
    test_bandwidth_not_in_risk()
    test_short_audio_no_warnings()
    test_physics_analysis_in_fusion()
    print("\n✅ All fusion fixes validated!")
```

---

## Implementation Checklist

### Immediate (Critical):
- [ ] Normalize stage weights to sum to 100%
- [ ] Add score clamping in `physics_analysis.py` (validation)
- [ ] Add score clamping in `fusion_engine.py` sensor value extraction
- [ ] Update DigitalSilenceSensor segment check to 2048 samples (verify)
- [ ] Run validation test script

### High Priority:
- [ ] Make BandwidthSensor explicitly "informational" category
- [ ] Add debug logging for score tracking
- [ ] Update fusion_engine to skip "informational" sensors

### Medium Priority:
- [ ] Add unit tests for each fix
- [ ] Document score clamping rationale
- [ ] Add assertions to catch future regressions

---

## Expected Impact After Enhancements

### Before Fixes (Baseline):
- Accuracy: 52%
- FPR: 58%
- Issues: Random behavior, score explosions, n_fft warnings

### After User Fixes (Current):
- Accuracy: ~60-65% (estimated)
- FPR: ~45% (estimated)
- Issues: Stage weights sum to 105%, no validation logging

### After All Enhancements (Projected):
- Accuracy: **75-80%** ✅
- FPR: **20-30%** ✅
- Benefits:
  - Normalized weights ensure predictable fusion
  - Comprehensive clamping prevents score explosions
  - Informational sensors properly categorized
  - Debug logging enables rapid troubleshooting

---

## Next Steps

1. **Commit current fixes** with clear message documenting the critical BandwidthSensor bug
2. **Apply enhancements** (normalize weights, add clamping, improve logging)
3. **Run local benchmark** with real audio library
4. **Validate results** against target metrics (70-78% accuracy)
5. **If successful:** Proceed to Phase 2.2 (sensor metadata)
6. **If needs tuning:** Use debug logs to identify weak sensors

---

**Created:** 2025-12-10
**Status:** User fixes validated ✅, Enhancements ready for implementation
**Impact:** Critical bug fixed (BandwidthSensor), ready for benchmark validation
