#!/bin/bash
# Shortcut for running the full synthetic batch test
# Usage: ./test_batch.sh

# Ensure we are in the project root
cd "$(dirname "$0")"

# Run the batch test using the configured virtual environment
.venv/bin/python backend/scripts/test_synthetic_batch.py
