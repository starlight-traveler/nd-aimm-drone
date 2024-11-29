#!/bin/bash

# ======================================================================
# Script Name: run.sh
# Description: Navigates to the parent directory and runs main.py as a
#              background process, logging output to start/drone.log.
#              The process continues running after SSH logout, and
#              outputs are visible on the terminal while connected.
# ======================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# Function to display usage information
usage() {
    echo "Usage: $0"
    echo "Runs main.py as a background process from the parent directory."
    echo "Outputs are logged to start/drone.log and displayed on the terminal."
    exit 1
}

# Check if help is requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
fi

# Get the absolute path of the directory where this script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the parent directory
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Navigate to the parent directory
cd "$PARENT_DIR" || { echo "Error: Failed to navigate to parent directory."; exit 1; }

# Define the path to the log directory and log file
LOG_DIR="$SCRIPT_DIR"
LOG_FILE="$LOG_DIR/drone.out"
PID_FILE="$LOG_DIR/main.pid"

# Ensure the log directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory at $LOG_DIR..."
    mkdir -p "$LOG_DIR" || { echo "Error: Failed to create log directory."; exit 1; }
fi

# Check if main.py exists in the parent directory
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found in $PARENT_DIR."
    exit 1
fi

# Inform the user about starting the process
echo "Starting main.py as a background process..."
echo "Logs will be written to $LOG_FILE."
echo "Process ID will be saved to $PID_FILE."

# Run main.py using nohup and tee
# - nohup allows the process to continue running after logout
# - tee displays output on the terminal and appends it to the log file
# - The process runs in the background
nohup python3 main.py 2>&1 | tee -a "$LOG_FILE" &

# Capture the PID of the last background process
PID=$!

# Save the PID to a file for future reference
echo "$PID" > "$PID_FILE"

# Confirm to the user that the process has started
echo "main.py is now running with PID $PID."
echo "To stop the process, run: kill $(cat $PID_FILE)"
