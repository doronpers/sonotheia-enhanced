#!/bin/bash
# Shortcut for running a 25-sample verification test WITHOUT auto-printing
# Usage: ./verify_25.sh

# Ensure we are in the project root
cd "$(dirname "$0")"

echo "Starting 25-sample verification run (No Print)..."

# Run the micro test script with count=25
# Use tee to show output AND save to file (just in case)
.venv/bin/python -u backend/scripts/run_micro_test.py --count 25 | tee logs/verify_last_run.txt

echo "Run complete. Log saved to logs/verify_last_run.txt"
