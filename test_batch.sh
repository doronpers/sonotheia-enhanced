#!/bin/bash
# Shortcut for running the full synthetic batch test
# Usage: ./test_batch.sh

# Ensure we are in the project root
cd "$(dirname "$0")"

# Run the synthetic batch test
# Use tee to show output AND save to file for printing
.venv/bin/python -u backend/scripts/test_synthetic_batch.py "$@" | tee logs/batch_last_run.txt

# Print the report
echo "Printing report..."
python3 backend/scripts/print_report.py logs/batch_last_run.txt
