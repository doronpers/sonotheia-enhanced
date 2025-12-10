#!/bin/bash
# Shortcut for running the Sonotheia verification test
# Usage: ./verify.sh [options]
# Example: ./verify.sh --count 500

# Ensure we are in the project root
cd "$(dirname "$0")"

# Run the micro test script
# Use tee to show output AND save to file for printing
.venv/bin/python -u backend/scripts/run_micro_test.py "$@" | tee logs/verify_last_run.txt

# Print the report
echo "Printing report..."
python3 backend/scripts/print_report.py logs/verify_last_run.txt
