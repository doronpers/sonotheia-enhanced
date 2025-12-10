# Testing & Tuning Workflow

This document outlines the standard procedures for testing, verifying, and tuning the **Sonotheia Enhanced** detection engine.

## 1. Testing Modes

We use two distinct testing scripts for different stages of the development cycle.

### A. The "Crash Test" (Recall Testing)
**Script:** `./test_batch.sh` (Runs `test_synthetic_batch.py`)

*   **Purpose:** Aggressively test the system's ability to catch fakes.
*   **Target:** Runs *only* against the `unanalyzed_batch.txt` list (typically 1000+ synthetic files).
*   **Goal:** Maximize **Recall** (Sensitivity).
    *   Ignores False Positives (as it tests no real data).
    *   Focuses purely on identifying "Missed Fakes".
*   **When to Use:**
    *   Immediately after generating a new batch of synthetic samples.
    *   When tuning "Prosecution" sensors to ensure they aren't too weak.
    *   To answer the question: *"Can we catch this specific new attack vector?"*

### B. The "Health Check" (Regression Testing)
**Script:** `./verify.sh` (Runs `run_micro_test.py`)

*   **Purpose:** Verify system stability and balance.
*   **Target:** Runs a **balanced 50/50 mix** of Real and Fake files.
*   **Goal:** Maintain **Accuracy** and protect **Specificity**.
    *   Ensures valid organic files are not flagged as fake (False Positives).
    *   Ensures code changes haven't crashed the pipeline.
*   **When to Use:**
    *   Daily regression testing.
    *   After every code change or bug fix.
    *   Immediately *after* tuning thresholds to confirm safety.
    *   Recommended daily run: `./verify.sh --count 250` (500 total files).

---

## 2. The Accuracy "Hill Climbing" Loop

To systematically improve detection accuracy without breaking the system, use this feedback loop:

### Step 1: The "Missed Fake" Hunt
Run the crash test to find weaknesses.
```bash
./test_batch.sh > failures.txt
```
*   **Analyze:** Look for **"[VALID FAILURE]"** entries in the logs.
*   **Identify:** Check which sensors had scores *just below* their thresholds (e.g., `Pitch Velocity: 34.2` vs Threshold `35.0`).
*   **Action:** Tighten that specific sensor's threshold slightly in `settings.yaml` (e.g., lower `max_velocity_threshold` to `34.0`).

### Step 2: The "Safety Check"
Immediately verify that your new threshold is safe for real humans.
```bash
./verify.sh --count 250
```
*   **Pass:** System achieves 100% accuracy (or high TPR/TNR). The tuning was successful.
*   **Fail:** System starts flagging Real files as Fake (False Positives).
    *   **Remedy:** You tightened the threshold too much. Revert the change or tune a different sensor.

### Step 3: Automated Calibration
For large-scale tuning, use the dedicated calibration suite:
```bash
python backend/scripts/run_calibration.py
```
This script mathematically optimizes thousands of iterations to find the ideal "Goldilocks" zone for all sensors simultaneously.
