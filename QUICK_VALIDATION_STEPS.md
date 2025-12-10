# Quick Validation Steps - Phase 1 & Phase 2.1

**Status:** All improvements implemented ✅ - Ready for benchmark validation

---

## What Was Implemented

### ✅ Phase 1 (Commit e126000)
1. **Weighted Physics Fusion** - Sensors now contribute based on calibrated weights (30% GlottalInertia, 20% FormantTrajectory, etc.)
2. **Adaptive Prosecution Veto** - Two-tier veto system (0.85/0.75 thresholds) replaces disabled SAFE MODE
3. **Configuration Utilities** - Single source of truth in `settings.yaml`

### ✅ Phase 2.1 (Commit 92e7a05)
1. **HFDeepfakeSensor Re-enabled** - ML model now contributing at 10% weight
2. **Raised Confidence Threshold** - 0.70 → 0.85 to reduce false positives
3. **Weight Rebalancing** - Adjusted other sensors to accommodate ML model

### ✅ Phase 2.3 (Pre-existing)
1. **Codec-Aware Fusion** - Automatic narrowband profile for phone audio

---

## Run Benchmarks Now (3 Options)

### Option 1: Quick Test (30 seconds)
```bash
cd /home/user/sonotheia-enhanced/backend
python scripts/run_micro_test.py --count 10
```

### Option 2: Library Test (2 minutes)
```bash
cd /home/user/sonotheia-enhanced/backend
python scripts/generate_accuracy_report.py
```

### Option 3: Full Benchmark (5 minutes)
```bash
cd /home/user/sonotheia-enhanced/backend
python scripts/run_benchmark.py --config scripts/benchmark_config.yaml --full-eval
```

---

## Expected Results

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| **Accuracy** | 52% | 70-78% | 🎯 |
| **Precision** | 51.7% | 72-82% | 🎯 |
| **Recall** | 62% | 75-80% | 🎯 |
| **FPR** | 58% | 20-35% | 🎯 |
| **AUC** | 0.5392 | 0.75-0.85 | 🎯 |

**Improvement Target:** +18-26% accuracy, -23-38% FPR

---

## What to Check

### 1. Metrics Improved ✅
- Accuracy above 70%
- FPR below 35%
- AUC above 0.75

### 2. Logs Show New Logic ✅
```bash
# Check for weighted fusion
grep -i "weighted" backend/logs/*.log

# Check for veto logic
grep -i "veto" backend/logs/*.log

# Check for HF model contribution
grep -i "hfdeepfake" backend/logs/*.log
```

### 3. No Regressions ✅
- True Positive rate maintained or improved
- No new errors in logs

---

## If You Need Test Data

### Generate synthetic test data:
```bash
cd /home/user/sonotheia-enhanced/backend
python scripts/generate_test_data.py --output data/test_dataset --num-genuine 50 --num-spoof 50
```

### Or use existing library:
- Place real audio files in: `backend/data/library/organic/`
- Place fake audio files in: `backend/data/library/synthetic/`

---

## Troubleshooting

### "No module named 'numpy'"
```bash
cd /home/user/sonotheia-enhanced/backend
pip install -r requirements.txt
```

### "Directory does not exist"
```bash
mkdir -p backend/data/library/organic
mkdir -p backend/data/library/synthetic
```

### Accuracy still at 52%
```bash
# Verify changes are active
grep -n "weighted_sum" backend/detection/stages/physics_analysis.py
grep -n "high_confidence_veto = 0.85" backend/detection/stages/fusion_engine.py

# Check config loading
python -c "from backend.utils.config import get_sensor_weights; print(get_sensor_weights('default'))"
```

---

## Next Steps After Validation

### If Results Are Good (70-78% accuracy):
1. Document results in PERFORMANCE_HISTORY.md
2. Proceed to Phase 2.2 (sensor metadata)
3. Plan Phase 3 (advanced optimizations)

### If Results Need Tuning (60-70%):
1. Run detailed sensor analysis
2. Recalibrate thresholds: `python scripts/recalibrate_thresholds.py`
3. Adjust fusion weights based on performance

### If Results Are Low (<60%):
1. Check implementation with: `git diff e126000^ e126000`
2. Verify test data quality
3. Run with verbose logging: `LOG_LEVEL=DEBUG python scripts/generate_accuracy_report.py`

---

**Summary:** Everything is ready. Just run one of the benchmark commands above to validate the improvements!

For detailed information, see: `BENCHMARK_VALIDATION_GUIDE.md`
