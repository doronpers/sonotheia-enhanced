# Enhancements to Apply - Fusion Engine & Sensors

## Enhancement 1: Normalize Stage Weights

**File:** `backend/detection/stages/fusion_engine.py`
**Lines:** 44-50

**Current:**
```python
self.stage_weights = stage_weights or {
    "feature_extraction": 0.15,
    "temporal_analysis": 0.15,
    "artifact_detection": 0.15,
    "rawnet3": 0.40,
    "explainability": 0.15,
}
```

**Replace with:**
```python
self.stage_weights = stage_weights or {
    "feature_extraction": 0.10,      # Reduced: redundant with RawNet3
    "temporal_analysis": 0.10,       # Reduced: redundant with RawNet3
    "artifact_detection": 0.10,      # Reduced: redundant with RawNet3
    "rawnet3": 0.45,                 # Increased: primary ML detector
    "physics_analysis": 0.25,        # Added: critical physics sensors
}
# Total: 100%
```

---

## Enhancement 2: Add Score Validation in Physics Analysis

**File:** `backend/detection/stages/physics_analysis.py`
**Location:** After line 115 (risk_score calculation)

**Add this code block:**

```python
                # Convert boolean passed status to risk score
                # passed=True (real) → risk=0.0
                # passed=False (spoof) → risk=1.0
                risk_score = 0.0 if res.passed else 1.0

                # ENHANCEMENT: Validate risk_score is in [0,1] range
                if risk_score < 0.0 or risk_score > 1.0:
                    logger.warning(
                        f"Sensor {name} returned out-of-range risk_score: {risk_score:.3f}, "
                        f"clamping to [0,1]. Original value: {res.value}"
                    )
                    risk_score = max(0.0, min(1.0, float(risk_score)))

                # Apply weight
                weighted_sum += risk_score * weight
                total_weight += weight
```

---

## Enhancement 3: Add Score Clamping in Fusion Engine

**File:** `backend/detection/stages/fusion_engine.py`
**Location:** Lines 85-111 (sensor value extraction loop)

**Current:**
```python
for name, res in sensor_results.items():
    if res is None:
        continue
    # Extract score (preferred) or value (fallback)
    val = res.get("score")
    if val is None:
         val = res.get("value", 0.0)
```

**Replace with:**
```python
for name, res in sensor_results.items():
    if res is None:
        continue

    # Extract score (preferred) or value (fallback)
    val = res.get("score")
    if val is None:
        val = res.get("value", 0.0)

    # ENHANCEMENT: Clamp to [0,1] range and log violations
    original_val = val
    val = max(0.0, min(1.0, float(val)))

    if abs(original_val - val) > 1e-6:  # Clamping occurred
        logger.warning(
            f"Sensor {name} returned out-of-range value: {original_val:.3f}, "
            f"clamped to {val:.3f}"
        )
```

**Then after line 115-119 (risk/trust calculation), add:**

```python
    # 1. Calculate Risk (Max of Prosecution)
    # If any prosecutor finds a violation, Risk is high.
    risk_score = max(risk_scores) if risk_scores else 0.0

    # ENHANCEMENT: Clamp risk_score to [0,1]
    risk_score = max(0.0, min(1.0, risk_score))

    # 2. Calculate Trust (Avg of Defense)
    # consistently good defense signs build trust.
    trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0.5

    # ENHANCEMENT: Clamp trust_score to [0,1]
    trust_score = max(0.0, min(1.0, trust_score))
```

---

## Enhancement 4: Add Debug Logging

**File:** `backend/detection/stages/fusion_engine.py`
**Location:** After line 119 (trust_score calculation)

**Add:**

```python
    # ENHANCEMENT: Debug logging for score tracking
    logger.debug(f"Prosecution sensors: {len(risk_scores)} active, max risk: {risk_score:.3f}")
    logger.debug(f"Defense sensors: {len(trust_scores)} active, avg trust: {trust_score:.3f}")

    if risk_scores and logger.isEnabledFor(logging.DEBUG):
        top_risk = sorted(risk_scores, reverse=True)[:5]
        logger.debug(f"Top risk scores: {[f'{s:.3f}' for s in top_risk]}")

    if trust_scores and logger.isEnabledFor(logging.DEBUG):
        top_trust = sorted(trust_scores, reverse=True)[:5]
        logger.debug(f"Top trust scores: {[f'{s:.3f}' for s in top_trust]}")
```

**And after line 156 (final_score calculation), add:**

```python
    # (existing decision logic code)

    # ENHANCEMENT: Log final fusion decision
    logger.info(
        f"Fusion: base={base_score:.3f}, final={final_score:.3f}, "
        f"logic='{decision_logic}', risk={risk_score:.3f}, trust={trust_score:.3f}"
    )
```

---

## Enhancement 5: Improve BandwidthSensor Categorization

**File:** `backend/detection/stages/fusion_engine.py`
**Location:** Lines 98-106 (category determination)

**Current:**
```python
category = "defense"
lower_name = name.lower()
if "glottal" in lower_name or "pitch velocity" in lower_name or "silence" in lower_name or "two-mouth" in lower_name:
    category = "prosecution"

# Check optional metadata override
meta = res.get("metadata") or {}
if meta.get("category"):
     category = meta.get("category")
```

**Replace with:**
```python
# ENHANCEMENT: Check metadata first, then fall back to name mapping
meta = res.get("metadata") or {}
category = meta.get("category")

if not category:
    # Fall back to name-based mapping
    lower_name = name.lower()

    # Informational sensors (don't contribute to risk/trust)
    if "bandwidth" in lower_name:
        logger.debug(f"Skipping informational sensor: {name}")
        continue  # Skip, don't add to risk_scores or trust_scores

    # Prosecution sensors (violations = high risk)
    elif ("glottal" in lower_name or "pitch velocity" in lower_name or
          "silence" in lower_name or "two-mouth" in lower_name):
        category = "prosecution"

    # Defense sensors (natural signs = trust)
    else:
        category = "defense"
```

---

## Enhancement 6: Update DigitalSilenceSensor Segment Check

**File:** `backend/sensors/digital_silence.py`
**Location:** Line 327 (in _detect_room_tone_changes)

**Current:**
```python
if len(region) < 512:
    continue
```

**Replace with:**
```python
# ENHANCEMENT: Use 2048 samples minimum to avoid n_fft warnings
# At 16kHz, 2048 samples = 128ms
if len(region) < 2048:
    logger.debug(f"Skipping short silence region: {len(region)} samples < 2048 (128ms)")
    continue
```

**Also update spectral flux analysis:**

**Location:** Line 252 (in _analyze_spectral_flux)

**Current:**
```python
nperseg = min(frame_length, 1024)

if len(audio) < nperseg * 2:
    return {
        "has_instant_change": False,
        "instant_change_count": 0,
    }
```

**Replace with:**
```python
# ENHANCEMENT: Use 2048 for consistency and avoid warnings
nperseg = min(frame_length, 2048)

# Require minimum 2048 samples for reliable spectral analysis
if len(audio) < 2048:
    logger.debug(f"Audio too short for spectral flux: {len(audio)} samples < 2048")
    return {
        "has_instant_change": False,
        "instant_change_count": 0,
    }
```

---

## Enhancement 7: Extract physics_score Properly

**File:** `backend/detection/stages/fusion_engine.py`
**Location:** Lines 197-219 (_extract_scores method)

**Current:**
```python
def _extract_scores(self, stage_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Extract scores from stage results."""
    scores = {}

    for stage_name, result in stage_results.items():
        if result is None or not result.get("success", False):
            continue

        # Extract score based on stage type
        score = None
        if "score" in result:
            score = result["score"]
        elif "anomaly_score" in result:
            score = result["anomaly_score"]
        elif "temporal_score" in result:
            score = result["temporal_score"]
        elif "artifact_score" in result:
            score = result["artifact_score"]

        if score is not None:
            scores[stage_name] = float(score)

    return scores
```

**Replace with:**
```python
def _extract_scores(self, stage_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Extract scores from stage results."""
    scores = {}

    for stage_name, result in stage_results.items():
        if result is None or not result.get("success", False):
            continue

        # Extract score based on stage type
        score = None
        if "score" in result:
            score = result["score"]
        elif "physics_score" in result:  # ENHANCEMENT: Added
            score = result["physics_score"]
        elif "anomaly_score" in result:
            score = result["anomaly_score"]
        elif "temporal_score" in result:
            score = result["temporal_score"]
        elif "artifact_score" in result:
            score = result["artifact_score"]

        if score is not None:
            # ENHANCEMENT: Clamp to [0,1] range
            score = max(0.0, min(1.0, float(score)))
            scores[stage_name] = score

    return scores
```

---

## Quick Apply Script

Save this as `apply_enhancements.sh`:

```bash
#!/bin/bash
# Quick script to apply all enhancements

echo "Applying Fusion Engine & Sensor Enhancements..."

# Backup files first
echo "Creating backups..."
cp backend/detection/stages/fusion_engine.py backend/detection/stages/fusion_engine.py.bak
cp backend/detection/stages/physics_analysis.py backend/detection/stages/physics_analysis.py.bak
cp backend/sensors/digital_silence.py backend/sensors/digital_silence.py.bak

echo "✓ Backups created (.bak files)"
echo ""
echo "Now manually apply enhancements from ENHANCEMENTS_TO_APPLY.md"
echo "Or use your IDE's search and replace with the provided code blocks"
echo ""
echo "After applying, test with:"
echo "  python3 backend/tests/test_fusion_fixes.py"
echo "  python3 backend/scripts/run_micro_test.py --count 10"
```

---

## Validation After Applying

```bash
# 1. Test score clamping
cd /Volumes/Treehorn/Gits/sonotheia-enhanced
python3 -m pytest backend/tests/test_fusion_fixes.py -v

# 2. Run micro test (should show improved accuracy)
python3 backend/scripts/run_micro_test.py --count 10

# 3. Check for n_fft warnings (should be zero)
python3 backend/scripts/run_micro_test.py --count 10 2>&1 | grep -i "n_fft"

# 4. Run full benchmark with real data
python3 backend/scripts/generate_accuracy_report.py
```

---

## Expected Results After Enhancements

### Score Validation:
```
✓ No out-of-range scores
✓ No BandwidthSensor contamination
✓ Physics scores properly contributing
```

### Warnings:
```
✓ Zero n_fft warnings
✓ Clear debug logging of score flows
```

### Accuracy (with real data):
```
Target: 75-80% (from 52% baseline)
FPR: 20-30% (from 58% baseline)
```

---

**Priority:** Apply Enhancements 1, 3, 5, 7 immediately (critical for accuracy)
**Next:** Apply Enhancements 2, 4, 6 for robustness and debugging
**Then:** Run full benchmark validation on local machine
