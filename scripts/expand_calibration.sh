#!/bin/bash
set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/backend/venv"
PYTHON="$VENV_PATH/bin/python"
CALIBRATION_DIR="$PROJECT_ROOT/backend/data/calibration"
SYNTHETIC_DIR="$CALIBRATION_DIR/synthetic"
REAL_DIR="$CALIBRATION_DIR/real"

echo "Expanding calibration dataset..."

# Ensure directories exist
mkdir -p "$SYNTHETIC_DIR"
mkdir -p "$REAL_DIR"

# 1. Generate samples (uses default output: backend/data/library/synthetic)
echo "Generating fresh synthetic samples..."
# Using --dry-run for safety unless you want to spend API credits. 
# REMOVE --dry-run to actually generate audio.
"$PYTHON" "$PROJECT_ROOT/backend/scripts/generate_red_team.py" --count 2 --dry-run

# 2. Import to calibration (Simulated move for dry-run)
SOURCE_DIR="$PROJECT_ROOT/backend/data/library/synthetic"

echo "Importing from $SOURCE_DIR to $SYNTHETIC_DIR..."
# Ensure source exists
mkdir -p "$SOURCE_DIR"

# Copy/Mock import
# For dry run, we'll just touch some files if they don't exist
if [ ! "$(ls -A "$SOURCE_DIR")" ]; then
    echo "Creating dummy files for dry-run testing..."
    touch "$SOURCE_DIR/elevenlabs_dummy_1.mp3"
    touch "$SOURCE_DIR/openai_dummy_1.mp3"
fi

cp "$SOURCE_DIR"/*.mp3 "$SYNTHETIC_DIR/" 2>/dev/null || true

# 3. Update metadata.csv
echo "Updating metadata.csv..."
METADATA_FILE="$CALIBRATION_DIR/metadata.csv"

# Start fresh or append? Let's rebuild to be safe
echo "file,label" > "$METADATA_FILE"

# Add real files
count_real=0
if [ -d "$REAL_DIR" ]; then
    for f in "$REAL_DIR"/*.wav; do
        if [ -f "$f" ]; then
            echo "$(basename "$f"),bonafide" >> "$METADATA_FILE"
            ((count_real++))
        fi
    done
fi

# Add synthetic files
count_fake=0
if [ -d "$SYNTHETIC_DIR" ]; then
    # Look for both mp3 and wav
    for f in "$SYNTHETIC_DIR"/*.{wav,mp3}; do
        if [ -f "$f" ]; then
            echo "$(basename "$f"),spoof" >> "$METADATA_FILE"
            ((count_fake++))
        fi
    done
fi

echo "Calibration expansion complete."
echo "  Real samples: $count_real"
echo "  Synthetic samples: $count_fake"
