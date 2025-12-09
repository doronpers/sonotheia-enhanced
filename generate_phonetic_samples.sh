#!/bin/bash
# Helper script to generate phonetic voice samples
# Automatically activates virtual environment and runs the script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/backend/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it first: cd backend && python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Change to project root
cd "$SCRIPT_DIR"

# Run the script with all arguments passed through
python backend/scripts/generate_phonetic_samples.py "$@"

