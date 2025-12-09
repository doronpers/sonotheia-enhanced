#!/bin/bash
# Human Calibration Tool Launcher
# Run listening annotation sessions to improve deepfake detection

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/backend/venv"
PYTHON="$VENV_PATH/bin/python"

# Check venv exists
if [ ! -f "$PYTHON" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/pip" install --upgrade pip
    "$VENV_PATH/bin/pip" install numpy scipy soundfile pyyaml
fi

# Display usage if no args
if [ $# -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║           HUMAN CALIBRATION TOOL FOR DEEPFAKE DETECTION          ║"
    echo "╠══════════════════════════════════════════════════════════════════╣"
    echo "║ Use your ears to improve detection accuracy!                     ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "QUICK START:"
    echo "  $0 annotate <audio-file>     # Annotate single file"
    echo "  $0 batch <audio-dir>         # Batch annotate directory"
    echo "  $0 artifacts                 # List artifact types"
    echo "  $0 optimize                  # Run threshold optimizer"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 annotate sample.wav"
    echo "  $0 batch backend/data/samples"
    echo ""
    exit 0
fi

cd "$SCRIPT_DIR"

case "$1" in
    annotate)
        if [ -z "$2" ]; then
            echo "Usage: $0 annotate <audio-file>"
            exit 1
        fi
        "$PYTHON" backend/scripts/human_annotate.py --audio-file "$2" --interactive
        ;;
    batch)
        if [ -z "$2" ]; then
            echo "Usage: $0 batch <audio-dir>"
            exit 1
        fi
        "$PYTHON" backend/scripts/human_annotate.py --audio-dir "$2" --interactive
        ;;
    artifacts)
        "$PYTHON" backend/scripts/human_annotate.py --list-artifacts
        ;;
    optimize)
        echo "Running threshold optimizer on calibration dataset..."
        "$PYTHON" backend/calibration/optimizer.py --dataset backend/data/calibration
        ;;
    help|--help|-h)
        "$PYTHON" backend/scripts/human_annotate.py --help
        ;;
    *)
        # Pass all args directly to the script
        "$PYTHON" backend/scripts/human_annotate.py "$@"
        ;;
esac
