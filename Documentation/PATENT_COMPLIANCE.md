# Patent Compliance: Pindrop Design-Around Strategy

**Document Version**: 1.0  
**Last Updated**: 2025-12-03  
**Status**: Implemented

---

## Executive Summary

This document explains Sonotheia's **design-around strategy** to operate freely without infringing Pindrop's patents on deepfake detection using Linear Predictive Coding (LPC) and Source-Filter Models.

**Key Distinction**: 
- **Pindrop (RESTRICTED)**: Static spectral values + LPC residuals
- **Sonotheia (SAFE)**: Dynamic trajectories + Phase-Physics Model

---

## Pindrop Patent Coverage (What We CANNOT Use)

### Restricted Technologies

Pindrop owns intellectual property covering:

1. **Linear Predictive Coding (LPC)**
   - Modeling vocal tract using LPC coefficients
   - Analyzing LPC residual error signals
   - Detecting glottal closure/opening in residuals

2. **Static Spectral Values**
   - Using formant frequencies (F1-F4) as absolute values
   - Pitch (F0) measurements as static features
   - Flagging based on "F1 is 400Hz" (snapshot)

3. **Source-Filter Model**
   - "Intentional modification introduces errors to source-filter model"
   - Glottal Closure Instances (GCIs)
   - Glottal Opening Instances (GOIs)

### Legal Risk

Using any of these approaches would constitute **direct patent infringement**:
- ❌ `librosa.lpc()` or `scipy.signal.lpc()`
- ❌ LPC residual analysis
- ❌ Static formant value flagging
- ❌ Glottal closure/opening detection

---

## Sonotheia Design-Around (What We CAN Use)

### Patent-Safe Technologies

Our implementation uses fundamentally different approaches:

### 1. **Formant Trajectory Sensor** (Replaces LPC-based Vocal Tract)

**Pindrop Approach (RESTRICTED)**:
- Use LPC to model vocal tract
- Analyze LPC residuals for errors
- Flag based on static formant values

**Sonotheia Approach (SAFE)**:
```python
# File: backend/sensors/formant_trajectory.py

# Extract formant frequencies using spectral peak tracking (NOT LPC)
formants_over_time = extract_formant_tracks(audio)  # F1-F4 per frame

# Calculate VELOCITY (rate of change), not static values
velocity_f1 = (f1[t+1] - f1[t]) / delta_t  # Hz per 10ms

# Flag if velocity exceeds physiological limits
if velocity_f1 > 300:  # Hz per 10ms
    verdict = "SYNTHETIC - impossible formant movement"
```

**Why It's Safe**:
- Uses **dynamic trajectories** (derivatives), not static snapshots
- No LPC usage whatsoever
- Focuses on physiological speed limits, not spectral errors
- Detects same phenomenon (synthetic artifacts) via different physics

---

### 2. **Phase Coherence Sensor** (Enhanced)

**Pindrop Approach (RESTRICTED)**:
- Analyze LPC residuals for phase anomalies
- Detection glottal pulse timing

**Sonotheia Approach (SAFE)**:
```python
# File: backend/sensors/phase_coherence.py

# Use Hilbert transform for analytic signal
analytic_signal = hilbert(audio)
instantaneous_phase = unwrap(angle(analytic_signal))

# Calculate instantaneous frequency (phase DERIVATIVE)
inst_freq = diff(instantaneous_phase) * sr / (2*pi)

# Measure Shannon entropy of phase derivative distribution
phase_entropy = calculate_entropy(inst_freq)

# Detect "digital silence" artifacts
discontinuities = detect_phase_discontinuities(instantaneous_phase)

# Flag if entropy too low or discontinuities present
if phase_entropy < threshold or discontinuities > 0:
    verdict = "SYNTHETIC - vocoder artifacts detected"
```

**Why It's Safe**:
- Uses **phase mathematics**, not source-filter modeling
- Analyzes phase derivative entropy, not LPC residuals
- Detects vocoder artifacts, not glottal closure
- "Phase-Physics Model" distinct from "Source-Filter Model"

---

### 3. **Coarticulation Sensor** (Patent "White Space")

**Pindrop Coverage**: None - coarticulation not mentioned in their patents

**Sonotheia Approach (SAFE)**:
```python
# File: backend/sensors/coarticulation.py

# Use Mel spectrogram (NOT LPC)
mel_spec = melspectrogram(audio)

# Calculate spectral delta (rate of change)
delta_mel = delta_features(mel_spec)

# Measure articulation velocity
mean_transition_speed = mean(abs(delta_mel))

# Flag if transitions too fast for human articulators
if mean_transition_speed > threshold:
    verdict = "SYNTHETIC - impossible articulation speed"
```

**Why It's Safe**:
- Analyzes **motor planning** (future sound anticipation)
- Focuses on temporal dependencies, not current-sound modeling
- Uses Mel spectrograms, not LPC
- In "white space" - Pindrop doesn't cover coarticulation

---

## Technical Comparison Table

| Aspect | Pindrop (RESTRICTED) | Sonotheia (SAFE) |
|--------|---------------------|------------------|
| **Vocal Tract** | LPC residuals, static formants | Formant velocities, physiological limits |
| **Method** | Source-Filter Model | Motor-Planning & Phase-Physics Model |
| **Feature Type** | Static spectral snapshots | Dynamic trajectories (derivatives) |
| **Analysis** | "F1 is 400Hz" (position) | "F1 moved 300 Hz in 10ms" (velocity) |
| **Phase Analysis** | LPC residual glottal pulses | Phase derivative entropy |
| **Coarticulation** | Not covered | Spectral transition speed |
| **Core Physics** | Current sound modeling | Movement constraints modeling |

---

## Sensor Implementation Details

### Formant Trajectory Sensor

**File**: `backend/sensors/formant_trajectory.py` (343 lines)

**Key Features**:
- ✅ Spectral peak tracking (no LPC)
- ✅ Frame-by-frame formant extraction (F1-F4)
- ✅ Velocity calculation (Hz per 10ms)
- ✅ Physiological speed limits:
  - F1: max 300 Hz / 10ms
  - F2/F3: max 500 Hz / 10ms
  - F4: max 600 Hz / 10ms
- ✅ Normalized risk score based on max velocity

**Patent Compliance**: Zero LPC usage, pure kinematic analysis

---

### Phase Coherence Sensor

**File**: `backend/sensors/phase_coherence.py` (192 lines)

**Key Features**:
- ✅ Hilbert transform for analytic signal
- ✅ Instantaneous frequency calculation
- ✅ Shannon entropy of phase derivative
- ✅ Discontinuity detection (digital silence artifacts)
- ✅ Combined score: entropy - discontinuity_penalty

**Patent Compliance**: No LPC residuals, pure phase mathematics

---

### Coarticulation Sensor

**File**: `backend/sensors/coarticulation.py` (69 lines)

**Key Features**:
- ✅ Mel spectrogram delta features
- ✅ Mean spectral transition speed
- ✅ Physiological articulation limits
- ✅ Temporal dependency analysis

**Patent Compliance**: In "white space" - not covered by Pindrop patents

---

## Fusion Engine Configuration

**File**: `backend/sensors/fusion.py`

**Patent-Safe Sensor Weights**:
```python
DEFAULT_WEIGHTS = {
    "FormantTrajectory": 0.35,    # High weight - physics-based
    "PhaseCoherence": 0.25,        # Enhanced entropy analysis
    "Coarticulation": 0.20,        # Motor planning (white space)
    "BandwidthSensor": 0.10,       # Reduced
    "HuggingFaceDetector": 0.10,   # ML-based (supplemental)
}
```

**Deprecated (REMOVED)**:
- ❌ `BreathSensor` - used LPC residuals
- ❌ `VocalTractSensor` - used LPC (replaced by FormantTrajectory)

---

## Freedom to Operate Statement

### Legal Position

Sonotheia's deepfake detection system operates under a **Motor-Planning & Phase-Physics Model**, fundamentally distinct from Pindrop's **Source-Filter Model**.

**Key Distinctions**:

1. **No LPC Usage**: Sonotheia does not use Linear Predictive Coding in any form
2. **Dynamic vs. Static**: Analyzes rate of change (velocities), not absolute values
3. **Different Physics**: Focuses on biomechanical constraints, not acoustic modeling
4. **White Space**: Coarticulation analysis is uncovered territory

### Independent Claims

Our detection methods are based on:
- Formant kinematics (movement physics)
- Phase derivative entropy (information theory)
- Motor planning temporal dependencies (neuroscience)

These are **independent inventions** that happen to detect the same phenomenon (synthetic speech) through orthogonal technical means.

---

## Compliance Verification

### Automated Scanning

**Test File**: `backend/tests/test_patent_compliance.py`

```python
def test_no_lpc_in_sensors():
    """Scan all sensor files for prohibited LPC usage."""
    prohibited_patterns = [
        r'librosa\.lpc',
        r'scipy\.signal\.lpc',
        r'LPC.*residual',
        r'glottal.*closure',
        r'glottal.*opening'
    ]
    # Scan all .py files in backend/sensors/
    # Assert no matches found
```

**Run Command**:
```bash
cd /Volumes/Treehorn/Gits/sonotheia-enhanced/backend
pytest tests/test_patent_compliance.py -v
```

**Expected Result**: ✅ All tests pass (zero LPC usage detected)

---

### Manual Code Review Checklist

- [ ] No `librosa.lpc()` calls in any sensor file
- [ ] No `scipy.signal.lpc()` calls in any sensor file
- [ ] No references to "residual" in vocal tract analysis
- [ ] No glottal closure/opening detection
- [ ] All sensors use dynamic features (derivatives, velocities)
- [ ] Documentation clearly states design-around strategy

---

## Maintenance Guidelines

### When Adding New Sensors

1. **Review patent landscape** before implementing
2. **Avoid LPC** and source-filter modeling entirely
3. **Use dynamic features** (velocities, accelerations, entropies)
4. **Document patent compliance** in sensor docstring
5. **Add to automated compliance tests**

### Red Flags

Stop immediately if you see:
- ❌ `librosa.lpc` or `scipy.signal.lpc`
- ❌ "LPC residual" or "error signal"
- ❌ "Glottal closure/opening"
- ❌ Static formant value thresholding
- ❌ Source-filter model terminology

### Safe Approaches

Always prefer:
- ✅ Spectral peak tracking
- ✅ Kinematic analysis (velocities, accelerations)
- ✅ Entropy measurements
- ✅ Temporal dependency modeling
- ✅ Phase mathematics

---

## References

### Internal Documentation
- `backend/sensors/formant_trajectory.py` - Formant velocity implementation
- `backend/sensors/phase_coherence.py` - Phase entropy implementation
- `backend/sensors/coarticulation.py` - Motor planning implementation
- `backend/sensors/fusion.py` - Sensor weight configuration

### Patent Strategy Resources
- User-provided design-around guidance (2025-12-03)
- Physiological speech constraints literature
- Phase coherence theory for vocoder detection

---

## Updates Log

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-12-03 | Replaced `vocal_tract.py` with `formant_trajectory.py` | Remove LPC patent infringement |
| 2025-12-03 | Enhanced `phase_coherence.py` with entropy | Strengthen phase-physics approach |
| 2025-12-03 | Added patent compliance docstrings | Document design-around strategy |
| 2025-12-03 | Updated fusion weights | Reflect new sensor set |

---

## Contact

For questions about patent compliance:
- Review this document  
- Check sensor implementation comments
- Run automated compliance tests
- Consult legal counsel if uncertain

**Remember**: When in doubt, avoid LPC and use dynamic trajectory analysis instead.
