# Detection System Improvement Plan

**Date:** 2025-12-10
**Current Accuracy:** 52% (Random Baseline)
**Target Accuracy:** 85%+ (Production Ready)

---

## 🎯 Executive Summary

The Sonotheia Enhanced detection system is currently performing at **near-random levels (52% accuracy, 0.54 AUC)**. This analysis identifies 7 critical architectural flaws and provides a prioritized roadmap for achieving production-grade performance.

**Key Findings:**
- Physics sensor fusion uses naive equal weighting (ignores calibrated weights)
- SAFE MODE disabled critical detection logic (veto threshold: 0.98)
- Configuration mismatches across 3 files (settings.yaml, fusion.py, physics_analysis.py)
- False positive rate: 58% (unacceptable for production)

**Target Outcomes:**
- ✅ Accuracy: 85%+
- ✅ False Positive Rate: <5%
- ✅ AUC: >0.90
- ✅ Real-time performance maintained (<3s per sample)

---

## 📊 Current State Analysis

### Performance Metrics (2025-12-10 Benchmark)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Accuracy | 52% | 85%+ | ❌ CRITICAL |
| Precision | 51.7% | 90%+ | ❌ CRITICAL |
| Recall | 62% | 85%+ | ❌ CRITICAL |
| AUC | 0.5392 | 0.90+ | ❌ CRITICAL |
| FPR | 58% | <5% | ❌ CRITICAL |
| FNR | 38% | <15% | ❌ CRITICAL |

### Active Sensors (13 Total)

**Defense Sensors (7)** - Indicate REAL audio:
```
1. BreathSensor          - Phonation duration analysis
2. DynamicRangeSensor    - Crest factor analysis
3. BandwidthSensor       - Codec/quality detection
4. GlobalFormantSensor   - Resonance patterns
5. CoarticulationSensor  - Motor planning continuity
6. FormantTrajectorySensor - Fluid motion analysis (35% weight in config)
7. ENFSensor             - Electrical network frequency
```

**Prosecution Sensors (6)** - Indicate FAKE audio:
```
8. PitchVelocitySensor     - Impossible laryngeal motion
9. GlottalInertiaSensor    - Tissue physics violations (35% weight in config)
10. DigitalSilenceSensor   - Non-biological silence
11. TwoMouthSensor         - Anatomical conflicts (DISABLED: weight=0.00)
12. PhaseCoherenceSensor   - Vocoder artifacts
13. HFEnsembleSensor       - AI model detection (DISABLED: weight=0.00)
```

---

## 🔍 Root Cause Analysis

### Issue #1: Naive Physics Fusion ⚠️ CRITICAL

**Location:** `/backend/detection/stages/physics_analysis.py:86-93`

**Current Code:**
```python
if res.passed is False:
    total_score += 0.2  # Each failure adds 20% risk
```

**Problems:**
- All sensor failures weighted equally
- Ignores calibrated weights from `settings.yaml`
- No differentiation between high-confidence vs low-confidence sensors
- Maximum 5 failures = 100% fake (arbitrary cap)

**Impact:**
- GlottalInertiaSensor (should be 35% weight) treated same as ENFSensor (0% weight)
- Low-confidence sensors can trigger false positives
- No consensus mechanism

---

### Issue #2: SAFE MODE Over-Tuning ⚠️ CRITICAL

**Location:** `/backend/detection/stages/fusion_engine.py:130`

**Current Code:**
```python
if risk_score > 0.98:  # Was 0.8, raised to 0.98 (effectively disabled)
    final_score = max(final_score, risk_score)
    decision_logic = "Prosecution Veto (High Risk)"
```

**Problems:**
- Veto threshold raised from 0.8 → 0.98 to reduce false positives
- Now impossible to reach (requires near-perfect sensor consensus)
- System cannot flag obvious deepfakes

**Impact:**
- Clear synthetic audio passes through
- Prosecution sensors rendered ineffective
- False negative rate increased to 38%

---

### Issue #3: Configuration Fragmentation ⚠️ HIGH

**Three Sources of Truth:**

**File 1:** `/backend/config/settings.yaml`
```yaml
fusion:
  profiles:
    default:
      weights:
        GlottalInertiaSensor: 0.35
        PitchVelocitySensor: 0.15
        FormantTrajectorySensor: 0.20
```

**File 2:** `/backend/sensors/fusion.py`
```python
DEFAULT_WEIGHTS = {
    "GlottalInertiaSensor": 0.20,  # Different!
    "FormantTrajectorySensor": 0.20,
    "PhaseCoherenceSensor": 0.10,
}
```

**File 3:** `/backend/detection/stages/physics_analysis.py`
```python
# Ignores both and uses flat 0.2!
total_score += 0.2
```

**Impact:**
- Unclear which weights are actually used
- Calibration efforts wasted
- Impossible to debug performance issues

---

### Issue #4: String-Based Categorization 🐛 MEDIUM

**Location:** `/backend/detection/stages/fusion_engine.py:99-101`

**Current Code:**
```python
category = "defense"
lower_name = name.lower()
if "glottal" in lower_name or "pitch velocity" in lower_name:
    category = "prosecution"
```

**Problems:**
- Fragile string matching
- Sensors miscategorized if renamed
- No compile-time safety

**Impact:**
- Sensors may be incorrectly categorized
- Prosecution/Defense logic unreliable

---

### Issue #5: Disabled High-Value Sensors 🔴 HIGH

**Location:** `/backend/config/settings.yaml`

```yaml
sensors:
  hf_deepfake:
    confidence_threshold: 0.70
  # BUT in fusion weights:
  HFDeepfakeSensor: 0.00  # DISABLED
  TwoMouthSensor: 0.00    # DISABLED
```

**Problems:**
- HFEnsembleSensor (ML model) disabled to reduce FPR
- TwoMouthSensor (anatomical conflict) disabled
- Removing powerful detectors instead of tuning them

**Impact:**
- Missing deepfakes that ML models would catch
- Not leveraging full sensor suite

---

### Issue #6: No Adaptive Thresholding 🎯 MEDIUM

**Current Implementation:**
```python
THRESHOLD_SYNTHETIC = 0.7  # Fixed
THRESHOLD_REAL = 0.3       # Fixed
```

**Problems:**
- Same thresholds for all audio qualities
- No codec-specific tuning (narrowband vs wideband profiles exist but not fully integrated)
- No confidence-based adjustment

**Impact:**
- Poor performance on degraded audio (phone calls)
- Can't differentiate high-confidence from uncertain decisions

---

### Issue #7: Missing Sensor Metadata 📝 LOW

**Current Flow:**
```
Sensor.analyze() → SensorResult(passed, value, threshold)
                                    ↓
                          (NO category metadata)
                                    ↓
                    FusionEngine (guesses category via strings)
```

**Impact:**
- Requires workarounds in fusion engine
- Error-prone categorization

---

## 🚀 Improvement Roadmap

### Phase 1: Critical Fixes (Week 1) - Target: 70% Accuracy

#### **1.1 Implement Weighted Physics Fusion** ⚡ IMMEDIATE

**File:** `/backend/detection/stages/physics_analysis.py`

**Changes Required:**
```python
# BEFORE (Line 68-96):
total_score = 0.0
for name, res in results_dict.items():
    if res.passed is False:
        total_score += 0.2  # Naive!
physics_score = min(total_score, 1.0)

# AFTER:
from backend.utils.config import get_fusion_config

def process(self, audio: np.ndarray) -> Dict[str, Any]:
    # ... existing code ...

    # Load weights from config
    fusion_config = get_fusion_config()
    profile = fusion_config.get("profiles", {}).get("default", {})
    sensor_weights = profile.get("weights", {})

    # Weighted fusion
    weighted_sum = 0.0
    total_weight = 0.0

    for name, res in results_dict.items():
        # Get configured weight (default to 0.05 for unknown sensors)
        weight = sensor_weights.get(name, 0.05)

        # Skip disabled sensors (weight = 0)
        if weight == 0:
            continue

        # Convert passed status to risk score
        # passed=True → risk=0.0, passed=False → risk=1.0
        risk_score = 0.0 if res.passed else 1.0

        weighted_sum += risk_score * weight
        total_weight += weight

    # Normalize
    physics_score = weighted_sum / total_weight if total_weight > 0 else 0.5
```

**Expected Impact:**
- Accuracy: 52% → 65%
- Proper use of calibrated weights
- GlottalInertiaSensor failures weighted at 35% (as designed)

---

#### **1.2 Restore Prosecution Veto Logic** ⚡ IMMEDIATE

**File:** `/backend/detection/stages/fusion_engine.py`

**Changes Required:**
```python
# BEFORE (Line 130):
if risk_score > 0.98:  # Too high!
    final_score = max(final_score, risk_score)

# AFTER:
# Adaptive veto threshold based on sensor confidence
veto_threshold = 0.75  # Balanced threshold
high_confidence_threshold = 0.85  # Very confident sensors

if risk_score > high_confidence_threshold:
    # Strong veto: Guaranteed fake
    final_score = risk_score
    decision_logic = "High-Confidence Prosecution Veto"
elif risk_score > veto_threshold:
    # Moderate veto: Boost score but allow defense
    final_score = max(final_score, (final_score + risk_score) / 2)
    decision_logic = "Prosecution Influence"
```

**Expected Impact:**
- Accuracy: 65% → 72%
- Catch obvious fakes
- Reduce false negative rate: 38% → 20%

---

#### **1.3 Consolidate Configuration** ⚡ IMMEDIATE

**Action:** Make `settings.yaml` the single source of truth

**Files to Update:**
1. `/backend/sensors/fusion.py`: Remove `DEFAULT_WEIGHTS`, load from config
2. `/backend/detection/stages/physics_analysis.py`: Load weights from config
3. `/backend/detection/stages/fusion_engine.py`: Load profiles from config

**Implementation:**
```python
# Create utility function
# /backend/utils/config.py

import yaml
from pathlib import Path

_CONFIG_CACHE = None

def load_config():
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(config_path) as f:
            _CONFIG_CACHE = yaml.safe_load(f)
    return _CONFIG_CACHE

def get_fusion_config():
    config = load_config()
    return config.get("fusion", {})

def get_sensor_weights(profile="default"):
    fusion = get_fusion_config()
    profiles = fusion.get("profiles", {})
    profile_config = profiles.get(profile, {})
    return profile_config.get("weights", {})
```

**Expected Impact:**
- Single source of truth
- Easier calibration workflow
- Consistent behavior

---

### Phase 2: Optimization (Week 2) - Target: 80% Accuracy

#### **2.1 Re-Enable High-Value Sensors with Tuned Thresholds**

**Sensors to Re-Enable:**
1. **HFEnsembleSensor** (ML model)
   - Current: Disabled (weight=0.00)
   - Proposal: Enable at 0.10 weight with higher confidence threshold (0.85)

2. **TwoMouthSensor** (Anatomical conflict)
   - Current: Disabled (weight=0.00)
   - Proposal: Enable at 0.05 weight with stricter thresholds

**Configuration Changes:**
```yaml
# /backend/config/settings.yaml
fusion:
  profiles:
    default:
      weights:
        # Existing sensors...
        HFEnsembleSensor: 0.10      # Re-enabled
        TwoMouthSensor: 0.05        # Re-enabled
        # Reduce others slightly to keep total ~1.0

sensors:
  hf_deepfake:
    confidence_threshold: 0.85  # Raised from 0.70
  two_mouth:
    combined_threshold: 0.50    # Raised from 0.40
```

**Expected Impact:**
- Accuracy: 72% → 78%
- Catch ML-detectable patterns
- Reduce false negatives further

---

#### **2.2 Implement Sensor Metadata Passing**

**File:** `/backend/sensors/base.py`

**Changes:**
```python
class SensorResult:
    def __init__(
        self,
        sensor_name: str,
        passed: Optional[bool],
        value: float,
        threshold: float,
        reason: str = "",
        detail: str = "",
        metadata: Optional[Dict[str, Any]] = None,  # EXISTING
    ):
        self.metadata = metadata or {}
        # ADD category to metadata
        self.metadata.setdefault("category", "defense")  # Default
```

**Update All Sensors:**
```python
# Example: GlottalInertiaSensor
def __init__(self):
    super().__init__(name="GlottalInertiaSensor", category="prosecution")

def analyze(self, audio_data, sample_rate):
    result = SensorResult(
        sensor_name=self.name,
        passed=passed,
        value=value,
        threshold=threshold,
        metadata={"category": self.category}  # Pass category
    )
    return result
```

**Update Fusion Engine:**
```python
# /backend/detection/stages/fusion_engine.py
# Replace string matching (lines 98-106) with:
category = res.get("metadata", {}).get("category", "defense")
```

**Expected Impact:**
- Robust categorization
- No string matching hacks
- Easier to add new sensors

---

#### **2.3 Implement Codec-Aware Fusion**

**Current:** Narrowband profile exists but not fully integrated

**Enhancement:**
```python
# /backend/detection/stages/physics_analysis.py

def process(self, audio: np.ndarray) -> Dict[str, Any]:
    # ... existing code ...

    # Detect codec/bandwidth
    bandwidth_result = results_dict.get("BandwidthSensor")
    is_narrowband = False
    if bandwidth_result and bandwidth_result.value < 4000:  # <4kHz rolloff
        is_narrowband = True

    # Select appropriate profile
    profile_name = "narrowband" if is_narrowband else "default"
    sensor_weights = get_sensor_weights(profile=profile_name)

    # ... rest of fusion with selected weights ...
```

**Expected Impact:**
- Better performance on phone audio
- Adaptive to audio quality
- Accuracy: 78% → 82%

---

### Phase 3: Advanced Improvements (Week 3) - Target: 85%+ Accuracy

#### **3.1 Implement Confidence-Based Adaptive Thresholds**

**Current:** Fixed thresholds (0.7 synthetic, 0.3 real)

**Proposal:**
```python
def adaptive_threshold(base_threshold, confidence, sensor_consensus):
    """
    Adjust threshold based on confidence and consensus.

    High confidence + high consensus → Stricter threshold
    Low confidence + low consensus → More lenient threshold
    """
    adjustment = (confidence - 0.5) * 0.2  # ±0.1 max adjustment
    consensus_factor = (sensor_consensus - 0.5) * 0.1  # ±0.05

    adjusted = base_threshold + adjustment + consensus_factor
    return max(0.5, min(0.9, adjusted))  # Clamp to [0.5, 0.9]
```

**Expected Impact:**
- Better handling of uncertain cases
- Reduced false positives on degraded audio

---

#### **3.2 Implement Ensemble Voting**

**Add voting mechanism for edge cases:**
```python
def ensemble_decision(physics_score, neural_score, artifact_score):
    """
    Voting mechanism when scores disagree.
    """
    votes = {
        "physics": "REAL" if physics_score < 0.3 else "FAKE" if physics_score > 0.7 else "UNCERTAIN",
        "neural": "REAL" if neural_score < 0.3 else "FAKE" if neural_score > 0.7 else "UNCERTAIN",
        "artifact": "REAL" if artifact_score < 0.3 else "FAKE" if artifact_score > 0.7 else "UNCERTAIN",
    }

    fake_votes = sum(1 for v in votes.values() if v == "FAKE")
    real_votes = sum(1 for v in votes.values() if v == "REAL")

    if fake_votes >= 2:
        return "FAKE", 0.8
    elif real_votes >= 2:
        return "REAL", 0.8
    else:
        # Fall back to weighted average
        return "UNCERTAIN", 0.5
```

---

#### **3.3 Add Per-Sensor Performance Tracking**

**Track sensor accuracy over time:**
```python
# /backend/sensors/metrics.py

class SensorMetrics:
    def __init__(self):
        self.sensor_stats = defaultdict(lambda: {
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
        })

    def record_result(self, sensor_name, predicted, actual):
        stats = self.sensor_stats[sensor_name]
        if actual == "FAKE" and predicted == "FAKE":
            stats["true_positives"] += 1
        elif actual == "REAL" and predicted == "FAKE":
            stats["false_positives"] += 1
        # ... etc

    def get_sensor_accuracy(self, sensor_name):
        stats = self.sensor_stats[sensor_name]
        total = sum(stats.values())
        correct = stats["true_positives"] + stats["true_negatives"]
        return correct / total if total > 0 else 0.0
```

**Use for adaptive weighting:**
- Low-performing sensors get reduced weight
- High-performing sensors get boosted weight

---

## 🧪 Testing & Validation Plan

### Benchmark Suite Requirements

**Test Data:**
- ✅ 100+ organic voice samples (LibriSpeech, in-house recordings)
- ✅ 100+ synthetic samples (ElevenLabs, Tortoise TTS, Coqui)
- ✅ Various codecs (wideband HD, narrowband phone, compressed VoIP)
- ✅ Edge cases (noisy, short clips, accents)

**Metrics to Track:**
```python
{
    "accuracy": target >= 0.85,
    "precision": target >= 0.90,
    "recall": target >= 0.85,
    "f1_score": target >= 0.87,
    "auc": target >= 0.90,
    "fpr": target <= 0.05,
    "fnr": target <= 0.15,
    "processing_time_ms": target <= 3000,
}
```

**Per-Sensor Metrics:**
- Individual sensor accuracy
- Sensor contribution to final decision
- False positive rate per sensor
- Processing time per sensor

---

### Validation Workflow

**Step 1: Implement Phase 1 fixes**
```bash
# Make changes to physics_analysis.py, fusion_engine.py
python backend/scripts/run_benchmark.py --config scripts/benchmark_config.yaml
python backend/scripts/generate_accuracy_report.py
```

**Step 2: Compare metrics**
```bash
# Expect: 52% → 70% accuracy
# Verify FPR reduction
```

**Step 3: Iterate**
- Adjust weights based on results
- Re-calibrate thresholds
- Re-run benchmarks

**Step 4: A/B Testing**
- Run old fusion vs new fusion side-by-side
- Compare on production-like data

---

## 📋 Implementation Checklist

### Phase 1 (Critical - Week 1)
- [ ] **1.1** Implement weighted physics fusion in `physics_analysis.py`
- [ ] **1.2** Restore prosecution veto logic in `fusion_engine.py`
- [ ] **1.3** Create config utility functions in `utils/config.py`
- [ ] **1.3** Update fusion.py to use config
- [ ] **1.3** Update physics_analysis.py to use config
- [ ] Run benchmark suite
- [ ] Verify accuracy improvement (target: 70%)
- [ ] Document weight configuration process

### Phase 2 (Optimization - Week 2)
- [ ] **2.1** Re-enable HFEnsembleSensor with tuned threshold
- [ ] **2.1** Re-enable TwoMouthSensor with tuned threshold
- [ ] **2.2** Add category metadata to BaseSensor
- [ ] **2.2** Update all 13 sensors to pass category
- [ ] **2.2** Update fusion_engine to use metadata
- [ ] **2.3** Implement codec-aware profile selection
- [ ] Run benchmark suite
- [ ] Verify accuracy improvement (target: 80%)

### Phase 3 (Advanced - Week 3)
- [ ] **3.1** Implement confidence-based adaptive thresholds
- [ ] **3.2** Implement ensemble voting mechanism
- [ ] **3.3** Add sensor performance tracking
- [ ] **3.3** Implement adaptive weight adjustment
- [ ] Run comprehensive benchmark suite
- [ ] Verify production readiness (target: 85%+)
- [ ] Conduct A/B testing
- [ ] Document final configuration

---

## 🎯 Success Criteria

**Production Readiness Checklist:**
- ✅ Accuracy ≥ 85%
- ✅ Precision ≥ 90% (low false positive rate)
- ✅ Recall ≥ 85% (catch most deepfakes)
- ✅ AUC ≥ 0.90
- ✅ FPR ≤ 5% (acceptable for production)
- ✅ Processing time ≤ 3 seconds per sample
- ✅ Consistent performance across codecs (wideband, narrowband)
- ✅ Single source of truth for configuration
- ✅ Documented sensor weights and thresholds
- ✅ Automated benchmark pipeline

---

## 📊 Expected Performance Trajectory

| Phase | Changes | Estimated Accuracy | FPR | Notes |
|-------|---------|-------------------|-----|-------|
| **Baseline** | Current system | 52% | 58% | Random performance |
| **Phase 1.1** | Weighted fusion | 65% | 40% | Proper sensor weighting |
| **Phase 1.2** | Restore veto | 72% | 35% | Catch obvious fakes |
| **Phase 1.3** | Config consolidation | 72% | 35% | No accuracy change, easier tuning |
| **Phase 2.1** | Re-enable sensors | 78% | 20% | ML model + anatomical checks |
| **Phase 2.2** | Metadata passing | 78% | 20% | Robustness improvement |
| **Phase 2.3** | Codec-aware fusion | 82% | 15% | Better phone audio handling |
| **Phase 3.1** | Adaptive thresholds | 84% | 10% | Confidence-based decisions |
| **Phase 3.2** | Ensemble voting | 85% | 8% | Multi-stage consensus |
| **Phase 3.3** | Performance tracking | 87% | 5% | Self-tuning weights |

---

## 🚧 Risks & Mitigations

### Risk 1: Performance Regression
**Mitigation:**
- Keep old fusion code as fallback
- A/B test before full rollout
- Gradual rollout with monitoring

### Risk 2: Increased False Positives
**Mitigation:**
- Conservative threshold tuning
- Start with Phase 1 (proven weights)
- Monitor FPR closely during rollout

### Risk 3: Computational Overhead
**Mitigation:**
- Profile sensor execution times
- Disable slow sensors if needed
- Implement caching for repeated analysis

---

## 📝 Next Steps

**Immediate Actions (Today):**
1. Review this plan with team
2. Prioritize Phase 1 tasks
3. Set up benchmark baseline
4. Begin implementation of weighted fusion

**Short-Term (This Week):**
1. Complete Phase 1 implementation
2. Run benchmarks and validate improvements
3. Document configuration process
4. Prepare Phase 2 implementation plan

**Medium-Term (Next 2 Weeks):**
1. Complete Phase 2 & 3 implementations
2. Comprehensive testing and validation
3. Production deployment planning
4. User acceptance testing

---

**Document Owner:** AI Assistant (Claude)
**Last Updated:** 2025-12-10
**Next Review:** After Phase 1 completion
