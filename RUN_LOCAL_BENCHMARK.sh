#!/bin/bash
# Run Benchmark on Local Machine with Real Audio Data
# Location: /Volumes/Treehorn/Gits/sonotheia-enhanced

echo "============================================================"
echo "  SONOTHEIA BENCHMARK - Phase 1 + Phase 2.1 Validation"
echo "============================================================"
echo ""
echo "This script will benchmark the detection improvements using"
echo "your real audio library."
echo ""
echo "Expected Results:"
echo "  - Accuracy: 70-78% (from 52% baseline)"
echo "  - FPR: 20-35% (from 58% baseline)"
echo ""
echo "============================================================"
echo ""

# Check if we're in the right directory
if [ ! -d "backend/data/library/organic" ]; then
    echo "❌ Error: backend/data/library/organic not found"
    echo "   Current directory: $(pwd)"
    echo "   Please run from: /Volumes/Treehorn/Gits/sonotheia-enhanced"
    exit 1
fi

# Count available files
ORGANIC_COUNT=$(find backend/data/library/organic -type f \( -name "*.wav" -o -name "*.flac" -o -name "*.mp3" \) 2>/dev/null | wc -l | tr -d ' ')
SYNTHETIC_COUNT=$(find backend/data/library/synthetic -type f \( -name "*.wav" -o -name "*.flac" -o -name "*.mp3" \) 2>/dev/null | wc -l | tr -d ' ')

echo "📊 Audio Library Status:"
echo "   Organic (real):    $ORGANIC_COUNT files"
echo "   Synthetic (fake):  $SYNTHETIC_COUNT files"
echo "   Total:             $((ORGANIC_COUNT + SYNTHETIC_COUNT)) files"
echo ""

if [ "$ORGANIC_COUNT" -eq 0 ] || [ "$SYNTHETIC_COUNT" -eq 0 ]; then
    echo "❌ Error: Not enough audio files found"
    echo "   Need at least 1 organic and 1 synthetic file"
    exit 1
fi

echo "✅ Audio library found!"
echo ""
echo "============================================================"
echo "  Running Benchmark..."
echo "============================================================"
echo ""

# Change to project root
cd "$(dirname "$0")"

# Run the accuracy report
python3 backend/scripts/generate_accuracy_report.py

# Check if it succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "  ✅ BENCHMARK COMPLETE!"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "1. Review the results above"
    echo "2. Check if accuracy improved from 52% baseline"
    echo "3. Verify FPR decreased from 58% baseline"
    echo "4. Share results for analysis"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "  ❌ BENCHMARK FAILED"
    echo "============================================================"
    echo ""
    echo "Troubleshooting:"
    echo "1. Install dependencies: pip3 install -r backend/requirements.txt"
    echo "2. Check Python version: python3 --version (need 3.11+)"
    echo "3. Verify library structure:"
    echo "   ls backend/data/library/organic/"
    echo "   ls backend/data/library/synthetic/"
    echo ""
fi
