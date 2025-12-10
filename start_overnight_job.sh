#!/bin/bash
# start_overnight_job.sh
# Automates data ingestion, generation, analysis, and calibration for overnight processing.

set -e

# Configuration
LIBRISPEECH_COUNT=${LIBRISPEECH_COUNT:-5000}  # Increased for overnight load (was 2000)
COMMONVOICE_COUNT=${COMMONVOICE_COUNT:-2000}  # Increased for overnight load (was 500)
SYNTHETIC_COUNT=${SYNTHETIC_COUNT:-500}       # Increased for overnight load (was 50)
export PYTHONPATH=$PYTHONPATH:.

echo "============================================================"
echo "   SONOTHEIA ENHANCED - OVERNIGHT PROCESSING JOB"
echo "============================================================"
echo "This script will:"
echo "1. Ingest $LIBRISPEECH_COUNT files from LibriSpeech (Free)"
echo "2. Attempt to ingest $COMMONVOICE_COUNT files from CommonVoice"
echo "3. Generate $SYNTHETIC_COUNT synthetic samples per service (ElevenLabs/OpenAI)"
echo "4. Analyze all audio files in the library"
echo "5. Calibrate sensor thresholds based on new data"
echo "6. Run comprehensive benchmarks"
echo "============================================================"

# Python interpreter
PYTHON="python3"
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
    echo "Using virtual environment: .venv"
fi

# 1. Ingest LibriSpeech
echo ""
echo "[1/6] Ingesting LibriSpeech ($LIBRISPEECH_COUNT samples)..."
$PYTHON backend/scripts/ingest_librispeech.py --count $LIBRISPEECH_COUNT || echo "LibriSpeech ingestion warning (check logs)"

# 2. Ingest Common Voice
echo ""
echo "[2/6] Ingesting Common Voice ($COMMONVOICE_COUNT samples)..."
# Ensure token is loaded
if [ -f .env ]; then
    export HUGGINGFACE_TOKEN=$(grep HUGGINGFACE_TOKEN .env | cut -d '=' -f2)
fi
$PYTHON backend/scripts/ingest_commonvoice.py --count $COMMONVOICE_COUNT || echo "CommonVoice ingestion skipped or failed (check token)"

# 3. Generate Synthetics
echo ""
echo "[3/6] Generating Synthetic Samples ($SYNTHETIC_COUNT per service)..."
# Check for API keys before running to avoid errors
if grep -q "ELEVENLABS_API_KEY" .env || grep -q "OPENAI_API_KEY" .env; then
    # Generate new synthetic samples (with Telephony Augmentation)
    echo "Generating $SYNTHETIC_COUNT synthetic samples per service..."
    $PYTHON backend/scripts/generate_red_team.py --count $SYNTHETIC_COUNT --service all --augment || echo "Generation warning (check logs/credits)"
else
    echo "Skipping generation: No API keys found in .env"
fi

# 4. Analyze Library
echo ""
echo "[4/6] Analyzing Audio Library (Force Update)..."
$PYTHON backend/scripts/analyze_library.py --force --label all || echo "Analysis failed"

# 5. Calibrate
echo ""
echo "[5/6] Calibrating Sensors..."
$PYTHON backend/scripts/calibrate_library.py --update-config || echo "Calibration failed"

# 6. Benchmark
echo ""
echo "[6/6] Running Benchmarks..."
$PYTHON backend/scripts/run_benchmark.py || echo "Benchmarking warning"

echo ""
echo "============================================================"
echo "   OVERNIGHT JOB COMPLETE"
echo "============================================================"
