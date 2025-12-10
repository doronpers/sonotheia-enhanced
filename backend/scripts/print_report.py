#!/usr/bin/env python3
"""
Print Report Utility

Sends a text file to the default printer or a specified printer.
Intended to be called at the end of shell scripts to print job summaries.

Usage:
    python3 print_report.py <filename> [printer_name]
"""

import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

def print_file(filepath: str, printer_name: str = None):
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File '{filepath}' not found.")
        return

    # Auto-detect printer if not specified
    if not printer_name:
        try:
            # Try to get default printer
            result = subprocess.run(['lpstat', '-d'], capture_output=True, text=True)
            if result.returncode == 0 and "system default destination" in result.stdout:
                printer_name = result.stdout.split(": ")[1].strip()
            else:
                # Fallback to HP DeskJet if known
                printer_name = "HP_DeskJet_4100_series"
        except FileNotFoundError:
             print("Error: 'lpstat' command not found. Is CUPS installed?")
             return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"Sonotheia Report - {timestamp}\n{'-'*40}\n"
    
    # Create a temporary file with header
    temp_print_file = path.with_suffix('.to_print.txt')
    try:
        content = path.read_text()
        with open(temp_print_file, 'w') as f:
            f.write(header)
            f.write(content)
            
        print(f"Printing '{filepath}' to '{printer_name}'...")
        cmd = ['lp', '-d', printer_name, str(temp_print_file)]
        subprocess.run(cmd, check=True)
        print("Print job submitted.")
        
    except subprocess.CalledProcessError as e:
        print(f"Printing failed: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if temp_print_file.exists():
            temp_print_file.unlink()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 print_report.py <filename> [printer_name]")
        sys.exit(1)
        
    filename = sys.argv[1]
    printer = sys.argv[2] if len(sys.argv) > 2 else "HP_DeskJet_4100_series" 
    
    print_file(filename, printer)
