# Run Benchmarks on Your Local Machine

**Your audio library location:** `/Volumes/Treehorn/Gits/sonotheia-enhanced/backend/data/library`

Since the real audio files are on your local machine, you need to run the benchmarks there (not in this remote environment).

---

## Quick Start (2 commands)

```bash
# 1. Navigate to your local repo
cd /Volumes/Treehorn/Gits/sonotheia-enhanced

# 2. Run benchmark
python3 backend/scripts/generate_accuracy_report.py
```

That's it! Results will display in ~2-5 minutes.

---

## Alternative: Use the Script

```bash
cd /Volumes/Treehorn/Gits/sonotheia-enhanced
./RUN_LOCAL_BENCHMARK.sh
```

---

## What to Expect

### If Phase 1 + Phase 2.1 Are Working ✅

```
----------------------------------------
ACCURACY REPORT (100 files)
----------------------------------------
Accuracy:  75.00%    ← Should be 70-78% (was 52%)
Precision: 78.00%    ← Should be 72-82% (was 51.7%)
Recall:    77.00%    ← Should be 75-80% (was 62%)
----------------------------------------
True Positives (Caught Fakes): 38  ← Was 31
True Negatives (Cleared Real): 37  ← Was 21
False Positives (Real->Fake):  13  ← Was 29 (improvement!)
False Negatives (Fake->Real):  12  ← Was 19 (improvement!)
----------------------------------------
```

### Key Metrics to Check

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| **Accuracy** | 52% | 70-78% | ✅ Improved? |
| **FPR** | 58% | 20-35% | ✅ Reduced? |
| **AUC** | 0.5392 | 0.75-0.85 | ✅ Better? |

---

## If You Get Errors

### "No module named 'X'"
```bash
cd /Volumes/Treehorn/Gits/sonotheia-enhanced/backend
pip3 install -r requirements.txt
```

### "Directory does not exist"
```bash
# Verify library exists
ls -la backend/data/library/organic/ | head
ls -la backend/data/library/synthetic/ | head

# Should show .wav, .flac, or .mp3 files
```

### "No results found"
```bash
# Check if JSON results exist
ls backend/data/library/organic/*.json | wc -l
ls backend/data/library/synthetic/*.json | wc -l

# If 0, need to run detection first
python3 backend/scripts/analyze_library.py
```

---

## Detailed Analysis (Optional)

### Run with Verbose Logging

```bash
cd /Volumes/Treehorn/Gits/sonotheia-enhanced
LOG_LEVEL=DEBUG python3 backend/scripts/generate_accuracy_report.py 2>&1 | tee benchmark_detailed.log
```

### Check Weighted Fusion is Active

```bash
# Search logs for weighted fusion evidence
grep -i "weighted" benchmark_detailed.log
# Expected: "weighted_sum", "total_weight" mentions

# Check veto logic
grep -i "veto" benchmark_detailed.log
# Expected: "High-confidence veto" or "Prosecution Influence"

# Check HFDeepfakeSensor contribution
grep -i "hfdeepfake" benchmark_detailed.log
# Expected: "HFDeepfakeSensor contributing"
```

---

## Micro Test (Quick 30-Second Validation)

If you want a quick test before the full benchmark:

```bash
cd /Volumes/Treehorn/Gits/sonotheia-enhanced
python3 backend/scripts/run_micro_test.py --count 10

# Tests 10 organic + 10 synthetic samples
# Takes ~30 seconds
# Good for quick sanity check
```

---

## After Running Benchmarks

### If Results Are Good (70-78% accuracy) ✅

Share the output and we'll:
1. Document the validation success
2. Proceed to Phase 2.2 (sensor metadata)
3. Plan Phase 3 (advanced optimizations)

### If Results Are Similar to Baseline (52%) ⚠️

Share the output and we'll:
1. Debug why improvements aren't showing
2. Check if code changes are active
3. Verify sensor weights are loading correctly

### If Results Are Worse (<52%) ❌

Share the output and we'll:
1. Check for implementation issues
2. Verify configuration is correct
3. Debug sensor behavior

---

## Expected Processing Time

| Dataset Size | Time | RAM Usage |
|--------------|------|-----------|
| 20 files | 30 sec | ~500 MB |
| 50 files | 1.5 min | ~800 MB |
| 100 files | 3 min | ~1.2 GB |
| 500 files | 15 min | ~2 GB |

---

## Comparison with Baseline

The baseline benchmark (`metrics_20251210_120140.json`) showed:

```json
{
  "accuracy": 0.52,
  "precision": 0.5166666666666667,
  "recall": 0.62,
  "f1_score": 0.5636363636363636,
  "auc": 0.5392,
  "fpr": 0.58,
  "fnr": 0.38
}
```

**Your new results should show:**
- Accuracy: +18-26% improvement
- FPR: -23-38% reduction
- AUC: +0.21-0.31 improvement

---

## Quick Reference

```bash
# Just run the benchmark
cd /Volumes/Treehorn/Gits/sonotheia-enhanced
python3 backend/scripts/generate_accuracy_report.py
```

Copy and paste the results back here for analysis! 🎯
