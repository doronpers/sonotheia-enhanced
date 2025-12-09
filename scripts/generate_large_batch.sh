#!/bin/bash
set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/backend/venv"
PYTHON="$VENV_PATH/bin/python"

echo "Starting large batch generation of 1000 synthetic samples..."
echo "Target: 2 hours runtime approx."
echo "Services: ElevenLabs and OpenAI"

# 500 count per service * 2 services = 1000 samples
# This will take approx 1.5 - 2 hours depending on API latency
LOG_FILE="$PROJECT_ROOT/generation_$(date +%s).log"
echo "Logging to $LOG_FILE"
"$PYTHON" "$PROJECT_ROOT/backend/scripts/generate_red_team.py" --count 500 --service all > "$LOG_FILE" 2>&1

echo "Batch generation complete. Log saved to $LOG_FILE"
