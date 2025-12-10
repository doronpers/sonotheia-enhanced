#!/bin/bash
# process_backlog_only.sh
# Processes existing audio files in the library without new ingestion or generation.
# Useful if ingestion steps fail but files are present.

set -e

export PYTHONPATH=$PYTHONPATH:.

echo "============================================================"
echo "   SONOTHEIA ENHANCED - BACKLOG PROCESSING ONLY"
echo "============================================================"
echo "This script will:"
echo "1. SKIP Ingestion (LibriSpeech/CommonVoice)"
echo "2. SKIP Generation (Synthetic)"
echo "3. Analyze ALL files currently in backend/data/library"
echo "4. Calibrate sensors based on this library"
echo "5. Run benchmarks"
echo "============================================================"

# Python interpreter
PYTHON="python3"
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
    echo "Using virtual environment: .venv"
fi

# 1. Analyze Library
echo ""
echo "[1/3] Analyzing EXISTING Audio Library (Force Update)..."
$PYTHON backend/scripts/analyze_library.py --force --label all || echo "Analysis failed"

# 2. Calibrate
echo ""
echo "[2/3] Calibrating Sensors..."
$PYTHON backend/scripts/calibrate_library.py --update-config || echo "Calibration failed"

# 3. Benchmark
echo ""
echo "[3/3] Running Benchmarks..."
$PYTHON backend/scripts/run_benchmark.py || echo "Benchmarking warning"

echo ""
echo "============================================================"
echo "   BACKLOG PROCESSING COMPLETE"
echo "============================================================"
