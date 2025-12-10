#!/usr/bin/env python3
"""
 Sonotheia Data Factory
 ======================
 Master CLI for managing test data and running verification loops.
 
 Features:
 1. Generate Synthetic Data (ElevenLabs/OpenAI) + Telephony Variants.
 2. Augment Organic Data (Add Telephony effects to real audio).
 3. Run Micro-Tests (Rapid verification of calibration).
 
 Usage:
    ./data_factory.py generate --count 10 --service openai
    ./data_factory.py augment --count 20
    ./data_factory.py test --count 50
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_ROOT / "backend/venv/bin/python"

# Helper to run commands
def run_script(script_path: Path, args: list):
    """Run a python script using the venv python."""
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)
        
    cmd = [str(VENV_PYTHON)] + [str(script_path)] + args
    print(f"[EXEC] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def generate(args):
    """Handle generation command."""
    script = PROJECT_ROOT / "backend/scripts/generate_red_team.py"
    cmd_args = ["--count", str(args.count)]
    
    if args.service:
        cmd_args.extend(["--service", args.service])
    
    if args.augment:
        cmd_args.append("--augment")
        
    if args.dry_run:
        cmd_args.append("--dry-run")
        
    run_script(script, cmd_args)

def augment(args):
    """Handle augmentation command."""
    script = PROJECT_ROOT / "backend/scripts/augment_organic.py"
    cmd_args = ["--count", str(args.count)]
    
    if args.all:
        cmd_args.append("--all")
        
    run_script(script, cmd_args)

def test(args):
    """Handle test command."""
    script = PROJECT_ROOT / "backend/scripts/run_micro_test.py"
    cmd_args = ["--count", str(args.count)]
    
    if args.update:
        cmd_args.append("--update")
        
    run_script(script, cmd_args)

def main():
    parser = argparse.ArgumentParser(description="Sonotheia Data Factory CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # --- Generate Command ---
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic deepfake samples")
    gen_parser.add_argument("--count", type=int, default=5, help="Number of files to generate")
    gen_parser.add_argument("--service", choices=["elevenlabs", "openai", "all"], default="all", help="TTS Service to use")
    gen_parser.add_argument("--augment", action="store_true", help="Auto-generate telephony variants")
    gen_parser.add_argument("--dry-run", action="store_true", help="Simulate without API costs")
    
    # --- Augment Command ---
    aug_parser = subparsers.add_parser("augment", help="Apply telephony effects to existing organic data")
    aug_parser.add_argument("--count", type=int, default=10, help="Number of organic files to augment")
    aug_parser.add_argument("--all", action="store_true", help="Process ALL organic files")
    
    # --- Test Command ---
    test_parser = subparsers.add_parser("test", help="Run verification test")
    test_parser.add_argument("--count", type=int, default=50, help="Number of samples (split organic/synthetic) to test")
    test_parser.add_argument("--update", action="store_true", help="Update file metadata/JSON logs")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        generate(args)
    elif args.command == "augment":
        augment(args)
    elif args.command == "test":
        test(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
