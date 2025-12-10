#!/bin/bash
# Example script showing how to calibrate ProsodicContinuitySensor
# with organic speech samples

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "ProsodicContinuitySensor Calibration"
echo "=========================================="
echo ""

# Check if organic samples directory is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <organic_samples_directory>"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/organic/speech/samples"
    echo ""
    echo "The directory should contain WAV, FLAC, MP3, or OGG files"
    echo "with authentic human speech recordings."
    exit 1
fi

ORGANIC_DIR="$1"

if [ ! -d "$ORGANIC_DIR" ]; then
    echo "Error: Directory not found: $ORGANIC_DIR"
    exit 1
fi

# Count audio files
NUM_FILES=$(find "$ORGANIC_DIR" -type f \( -name "*.wav" -o -name "*.flac" -o -name "*.mp3" -o -name "*.ogg" \) | wc -l)
echo "Found $NUM_FILES audio files in $ORGANIC_DIR"
echo ""

if [ "$NUM_FILES" -eq 0 ]; then
    echo "Warning: No audio files found!"
    echo "Please ensure the directory contains .wav, .flac, .mp3, or .ogg files"
    exit 1
fi

if [ "$NUM_FILES" -lt 10 ]; then
    echo "Warning: Only $NUM_FILES files found. Recommend at least 20-30 samples for reliable calibration."
    echo ""
fi

# Output files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="$BACKEND_DIR/config/calibration_results"
mkdir -p "$OUTPUT_DIR"

CONFIG_FILE="$OUTPUT_DIR/prosodic_continuity_${TIMESTAMP}.yaml"
STATS_FILE="$OUTPUT_DIR/prosodic_continuity_stats_${TIMESTAMP}.json"

echo "Running calibration..."
echo ""

# Run calibration
cd "$SCRIPT_DIR"
python3 calibrate_prosodic.py \
    --organic-dir "$ORGANIC_DIR" \
    --output "$CONFIG_FILE" \
    --json > "$STATS_FILE"

echo ""
echo "=========================================="
echo "Calibration Complete!"
echo "=========================================="
echo ""
echo "Results saved to:"
echo "  Config: $CONFIG_FILE"
echo "  Stats:  $STATS_FILE"
echo ""
echo "Next steps:"
echo "1. Review the statistics in $STATS_FILE"
echo "2. Copy recommended thresholds from $CONFIG_FILE"
echo "3. Update backend/config/settings.yaml with new values"
echo "4. Test with synthetic samples to validate"
echo ""
echo "To apply these settings, add to settings.yaml:"
echo ""
cat "$CONFIG_FILE"
echo ""
