# Benchmark Validation Guide - Phase 1 & Phase 2.1

**Date:** 2025-12-10
**Purpose:** Validate detection improvements after Phase 1 (weighted fusion + adaptive veto) and Phase 2.1 (HFDeepfakeSensor re-enabled)
**Expected Impact:** 52% → 78% accuracy, 58% → 20% FPR

---

## Quick Status Check

### ✅ What's Already Implemented

**Phase 1.1 - Weighted Physics Fusion (Commit e126000)**
- File: `/backend/detection/stages/physics_analysis.py` (lines 83-143)
- Changes: Replaced flat 0.2 risk weights with calibrated sensor weights from `settings.yaml`
- Key sensors: GlottalInertia (30%), FormantTrajectory (20%), PitchVelocity (15%)

**Phase 1.2 - Adaptive Prosecution Veto (Commit e126000)**
- File: `/backend/detection/stages/fusion_engine.py` (lines 128-157)
- Changes: Two-tier veto system (high confidence >0.85, moderate >0.75)
- Replaced disabled SAFE MODE veto (0.98 threshold)

**Phase 1.3 - Configuration Utilities (Commit e126000)**
- File: `/backend/utils/config.py` (lines 191-270)
- Changes: Added `get_fusion_config()`, `get_sensor_weights()`, `get_fusion_thresholds()`

**Phase 2.1 - HFDeepfakeSensor Re-enabled (Commit 92e7a05)**
- File: `/backend/config/settings.yaml` (lines 98-109, 73)
- Changes:
  - HFDeepfakeSensor weight: 0.00 → 0.10 (re-enabled)
  - Confidence threshold: 0.70 → 0.85 (reduced false positives)
  - Adjusted other sensor weights to maintain balance

**Phase 2.3 - Codec-Aware Fusion (Pre-existing)**
- File: `/backend/detection/stages/physics_analysis.py` (lines 68-81)
- Already implemented: Bandwidth detection and narrowband profile switching

---

## Baseline Performance (Before Improvements)

**Source:** `benchmark_results/metrics_20251210_120140.json`

| Metric | Baseline | Status |
|--------|----------|--------|
| **Accuracy** | 52% | ⚠️ Random baseline |
| **Precision** | 51.7% | ⚠️ Near random |
| **Recall** | 62% | ⚠️ Needs work |
| **F1 Score** | 56.4% | ⚠️ Low |
| **AUC** | 0.5392 | ⚠️ Random classifier |
| **FPR** | 58% | 🔴 Unacceptable |
| **FNR** | 38% | ⚠️ High |

**Test Dataset:**
- 100 files total (50 genuine, 50 spoof)
- True Negatives: 21
- False Positives: 29
- False Negatives: 19
- True Positives: 31

---

## Expected Performance (After Phase 1 + 2.1)

### Phase 1 Expected Impact

| Improvement | Expected Change | Rationale |
|-------------|----------------|-----------|
| **Weighted Fusion** | +13% accuracy | Physics sensors now properly weighted (35% GlottalInertia vs 20% flat) |
| **Adaptive Veto** | +7% accuracy | Two-tier veto catches obvious fakes without over-vetoing |
| **Combined** | 52% → 70% | Synergistic improvements |

### Phase 2.1 Expected Impact

| Improvement | Expected Change | Rationale |
|-------------|----------------|-----------|
| **HFDeepfake Re-enabled** | +8% accuracy | ML model adds complementary detection (10% weight) |
| **Raised Threshold** | -18% FPR | Confidence threshold 0.85 reduces false alarms |
| **Combined with Phase 1** | 70% → 78% | ML + Physics synergy |

### Target Metrics

| Metric | Baseline | After Phase 1 | After Phase 2.1 | Production Target |
|--------|----------|---------------|-----------------|-------------------|
| **Accuracy** | 52% | 70% | 78% | 85%+ |
| **Precision** | 51.7% | 72% | 82% | 90%+ |
| **Recall** | 62% | 75% | 80% | 85%+ |
| **F1 Score** | 56.4% | 73.5% | 81% | 87%+ |
| **AUC** | 0.5392 | 0.75 | 0.85 | 0.90+ |
| **FPR** | 58% | 35% | 20% | <5% |
| **FNR** | 38% | 25% | 20% | <15% |

---

## How to Run Benchmarks

### Option 1: Quick Library-Based Test (Recommended)

If you have audio files in `backend/data/library/`:

```bash
cd /home/user/sonotheia-enhanced

# Ensure you have test data
ls backend/data/library/organic/*.{wav,flac,mp3} | head -5
ls backend/data/library/synthetic/*.{wav,flac,mp3} | head -5

# Run quick accuracy report
cd backend
python scripts/generate_accuracy_report.py
```

**Expected Output:**
```
----------------------------------------
ACCURACY REPORT (100 files)
----------------------------------------
Accuracy:  78.00%    (up from 52%)
Precision: 82.00%    (up from 51.7%)
Recall:    80.00%    (up from 62%)
----------------------------------------
True Positives (Caught Fakes): 40  (was 31)
True Negatives (Cleared Real): 38  (was 21)
False Positives (Real->Fake):  12  (was 29)
False Negatives (Fake->Real):  10  (was 19)
----------------------------------------
```

### Option 2: Micro Test (Quick Validation)

Run on a small subset (10-50 samples) for rapid feedback:

```bash
cd backend

# Quick test with 20 samples (10 organic + 10 synthetic)
python scripts/run_micro_test.py --count 10

# Expected output:
# Accuracy: 75-80%
# Processing time: 20-40 seconds
```

### Option 3: Full Benchmark Suite

If you have a complete test dataset with metadata:

```bash
cd backend

# Generate benchmark metadata (if needed)
python scripts/generate_benchmark_metadata.py

# Run full benchmark
python scripts/run_benchmark.py --config scripts/benchmark_config.yaml --full-eval

# Expected duration: 2-5 minutes for 100 files
```

### Option 4: Using Docker

```bash
# Ensure backend container is running
docker compose up -d backend

# Run benchmark inside container
docker compose exec backend python scripts/generate_accuracy_report.py

# Or use micro test
docker compose exec backend python scripts/run_micro_test.py --count 10
```

---

## What to Look For in Results

### 1. Overall Metrics (Priority 1)

**Accuracy Improvement:**
- ✅ **Target:** 70-78% (from 52%)
- 🎯 **Stretch:** 80%+
- ❌ **Fail:** <60%

**False Positive Rate:**
- ✅ **Target:** 20-35% (from 58%)
- 🎯 **Stretch:** <20%
- ❌ **Fail:** >45%

**AUC Score:**
- ✅ **Target:** 0.75-0.85 (from 0.5392)
- 🎯 **Stretch:** >0.85
- ❌ **Fail:** <0.65

### 2. Log Analysis (Priority 2)

**Check for Weighted Fusion in Logs:**

```bash
# Search for weighted fusion evidence
grep -i "weighted" backend/logs/*.log
# Expected: "weighted_sum" mentions, "total_weight" calculations

# Search for veto logic
grep -i "veto" backend/logs/*.log
# Expected: "High-confidence veto applied" or "Prosecution Influence"

# Check profile selection
grep -i "narrowband" backend/logs/*.log
# Expected: "Narrowband audio detected" for phone audio
```

**Expected Log Entries:**

```
[INFO] Narrowband audio detected, using narrowband fusion profile
[INFO] Weighted fusion: GlottalInertiaSensor (0.30), FormantTrajectory (0.20)...
[INFO] High-confidence veto applied: risk_score=0.892
[DEBUG] HFDeepfakeSensor contributing: score=0.88, weight=0.10
```

### 3. Confusion Matrix Analysis (Priority 3)

Compare baseline vs new results:

| Metric | Baseline | Expected | Improvement |
|--------|----------|----------|-------------|
| **True Positives** | 31/50 (62%) | 40/50 (80%) | +9 catches |
| **True Negatives** | 21/50 (42%) | 38/50 (76%) | +17 clears |
| **False Positives** | 29/50 (58%) | 12/50 (24%) | -17 errors |
| **False Negatives** | 19/50 (38%) | 10/50 (20%) | -9 misses |

### 4. Sensor Contribution Analysis

Check which sensors are most effective:

```bash
# Run with verbose logging
PYTHONPATH=. LOG_LEVEL=DEBUG python scripts/generate_accuracy_report.py 2>&1 | tee benchmark_detailed.log

# Analyze sensor contributions
grep -i "sensor_results" benchmark_detailed.log | python -m json.tool
```

**Expected Top Contributors:**
1. **GlottalInertiaSensor** - 30% weight, high accuracy on physical violations
2. **FormantTrajectorySensor** - 20% weight, catches unnatural transitions
3. **PitchVelocitySensor** - 15% weight, detects impossible pitch changes
4. **HFDeepfakeSensor** - 10% weight, ML-based detection
5. **DigitalSilenceSensor** - 10% weight, non-biological silence

---

## Validation Checklist

### Before Running Benchmarks

- [ ] Git is on correct branch (`claude/claude-md-mj0aha1ng1r0rpo2-01FDDtk9NqsJpALMoy5X46nn`)
- [ ] Latest commits pulled (`e126000`, `92e7a05`)
- [ ] Configuration verified (`backend/config/settings.yaml`)
- [ ] HFDeepfakeSensor weight = 0.10 (line 106)
- [ ] HFDeepfakeSensor threshold = 0.85 (line 73)
- [ ] Test data available (`backend/data/library/organic/` and `synthetic/`)

### After Running Benchmarks

- [ ] Accuracy improved by at least 15% (52% → 67%+)
- [ ] FPR reduced by at least 20% (58% → 38% or better)
- [ ] Logs show weighted fusion calculations
- [ ] Logs show veto logic triggered for high-risk samples
- [ ] HFDeepfakeSensor contributing to decisions (if enabled)
- [ ] No regressions in True Positive rate (should improve from 62%)

---

## Troubleshooting

### Issue: "No results found" or "Directory does not exist"

**Solution:**
```bash
# Check if library directory exists
ls -la backend/data/library/

# If missing, create structure
mkdir -p backend/data/library/organic
mkdir -p backend/data/library/synthetic

# Add audio files or generate test data
# (Refer to data generation scripts or use demo audio)
```

### Issue: Accuracy still at ~52%

**Possible causes:**
1. **Changes not applied:** Verify git status shows latest commits
2. **Config not loaded:** Check `backend/utils/config.py` is being imported
3. **Cache issue:** Restart backend/workers
4. **Wrong branch:** Ensure on feature branch, not old main

**Debug steps:**
```bash
# Verify code changes
grep -n "weighted_sum" backend/detection/stages/physics_analysis.py
# Should show usage around line 118

grep -n "high_confidence_veto = 0.85" backend/detection/stages/fusion_engine.py
# Should show exact match at line 133

# Check config loading
python -c "
from backend.utils.config import get_sensor_weights
print(get_sensor_weights('default'))
"
# Should show GlottalInertiaSensor: 0.30, HFDeepfakeSensor: 0.10
```

### Issue: High FPR (still >40%)

**Possible causes:**
1. HFDeepfakeSensor threshold too low
2. Veto thresholds need adjustment
3. Sensor weights need recalibration

**Solution:**
```bash
# Raise HFDeepfakeSensor threshold
# Edit backend/config/settings.yaml line 73:
# confidence_threshold: 0.90  # (from 0.85)

# Or raise veto thresholds
# Edit backend/detection/stages/fusion_engine.py:
# high_confidence_veto = 0.90  # (from 0.85)
# moderate_veto = 0.80  # (from 0.75)
```

### Issue: Low Recall (many false negatives)

**Possible causes:**
1. Veto thresholds too high
2. Defense sensors overriding prosecution

**Solution:**
```bash
# Lower veto thresholds slightly
# Edit fusion_engine.py:
# high_confidence_veto = 0.80  # (from 0.85)

# Or increase prosecution sensor weights
# Edit settings.yaml:
# GlottalInertiaSensor: 0.35  # (from 0.30)
```

---

## Next Steps After Validation

### If Accuracy 70-80% ✅

**Status:** Phase 1 + 2.1 validated successfully

**Next Actions:**
1. **Phase 2.2:** Implement sensor metadata passing (replace string-based categorization)
   - File: `backend/sensors/base.py` - add category to BaseSensor
   - File: `backend/detection/stages/fusion_engine.py` - use metadata instead of strings

2. **Phase 3:** Advanced optimizations
   - Confidence-based adaptive thresholds
   - Ensemble voting mechanism
   - Per-sensor performance tracking

### If Accuracy 60-70% ⚠️

**Status:** Partial success, needs tuning

**Next Actions:**
1. Run detailed sensor analysis to find weak links
2. Recalibrate sensor thresholds using `recalibrate_thresholds.py`
3. Adjust fusion weights based on individual sensor performance
4. Consider raising HFDeepfakeSensor weight to 0.15

### If Accuracy <60% ❌

**Status:** Implementation issue or data quality problem

**Next Actions:**
1. Verify all code changes are active (check git diff)
2. Check test data quality (corrupted files, wrong labels)
3. Run micro test with verbose logging to debug
4. Review sensor outputs individually
5. Consider rolling back to baseline and re-implementing incrementally

---

## Performance Tracking

Create a tracking file after each benchmark:

```bash
# Save results to tracking file
cat >> PERFORMANCE_HISTORY.md <<EOF

## Benchmark Run - $(date +%Y-%m-%d)

**Commit:** $(git rev-parse --short HEAD)
**Branch:** $(git branch --show-current)

**Results:**
- Accuracy: X.XX%
- Precision: X.XX%
- Recall: X.XX%
- F1: X.XX%
- FPR: X.XX%
- AUC: X.XXXX

**Notes:**
[Add observations here]

---
EOF
```

---

## Summary

**Phase 1 + Phase 2.1 changes are fully implemented and ready for validation.**

**To validate:**
1. Run: `python backend/scripts/generate_accuracy_report.py`
2. Verify: Accuracy 70-78% (from 52%)
3. Check: FPR 20-35% (from 58%)
4. Confirm: Weighted fusion and veto logic in logs

**Expected outcome:** Significant improvement demonstrating that weighted fusion and adaptive veto are working correctly.

**If validation succeeds:** Proceed to Phase 2.2 (sensor metadata) and Phase 3 (advanced optimizations) to reach 85%+ accuracy target.

**If validation fails:** Use troubleshooting guide above to diagnose and fix issues.

---

**Last Updated:** 2025-12-10
**Created By:** AI Assistant (Claude)
**For:** Phase 1 & Phase 2.1 Validation
