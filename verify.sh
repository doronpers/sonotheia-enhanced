#!/bin/bash
# Shortcut for running the Sonotheia verification test
# Usage: ./verify.sh [options]
# Example: ./verify.sh --count 500

# Ensure we are in the project root
cd "$(dirname "$0")"

# Run the test using the configured virtual environment
.venv/bin/python backend/scripts/run_micro_test.py "$@"
