#!/bin/bash
# verify_quick.sh - Fast verification run (10 samples)

# Ensure we are in the project root
cd "$(dirname "$0")"

echo "Starting Quick Verification (10 samples)..."

# Run micro test with count=5 (5 Real + 5 Fake = 10 Total)
# Using the virtual environment python explicitly
.venv/bin/python -u backend/scripts/run_micro_test.py --count 5

echo "Quick run complete."
