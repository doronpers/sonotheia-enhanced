#!/bin/bash
# Shortcut for starting the overnight job
# Usage: ./overnight.sh

# Ensure we are in the project root
cd "$(dirname "$0")"

# Execute the existing shell script which handles the job logic
# We assume start_overnight_job.sh is correct, but let's ensure it uses the venv python if called directly inside
# actually, let's just inspect it first. But user wants a shortcut.

./start_overnight_job.sh
