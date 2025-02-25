#!/bin/bash

# Define paths
VENV_DIR="/home/glorified2247/Python_Programs/sonos_hat_v1/env"  # Replace with actual virtual environment path
SCRIPT_PATH="/home/glorified2247/Python_Programs/sonos_hat_v1/sonos_hat_v1/controller.py"  # Replace with your Python script path
LOG_FILE="/home/glorified2247/Python_Programs/sonos_hat_v1/output.log"  # Define log file path

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Activate virtual environment
#source "$VENV_DIR/bin/activate"

# Run Python script as sudo in the background, redirecting output to the log file
sudo nohup "$VENV_DIR/bin/python" "$SCRIPT_PATH" > "$LOG_FILE" 2>&1 &

# Get the PID of the background process
PID=$!

# Print message with PID of background process
echo "Python script started with sudo in background (PID: $PID). Check logs at: $LOG_FILE"

# Keep virtual environment active (NO deactivate)
