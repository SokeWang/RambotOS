#!/bin/bash

# RambotOS Unified Startup Script
# This script starts the FastAPI core and the main GUI sequentially.

# 0. Environment Check
PYTHON_EXE=$(which python3)
echo "Using Python: $PYTHON_EXE"
$PYTHON_EXE --version

# 1. Kill any existing instances
echo "Shutting down existing Rambot processes..."
pkill -f rambot_core.py
pkill -f standalone_monitor.py
pkill -f standalone_telegram.py
rm -f /tmp/rambot_email_monitor.pid
rm -f /tmp/rambot_telegram_monitor.pid

# 2. Start Rambot Core (FastAPI) in the background
echo "Starting Rambot Core Service..."
$PYTHON_EXE rambot_core.py > core.log 2>&1 &
CORE_PID=$!

# Wait for Core to be ready
echo "Waiting for Core to initialize..."
MAX_RETRIES=15
COUNT=0
while ! curl -s http://127.0.0.1:8000/ > /dev/null; do
    sleep 1
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Rambot Core failed to start."
        echo "Last 10 lines of core.log:"
        tail -n 10 core.log
        kill $CORE_PID 2>/dev/null
        exit 1
    fi
done
echo "Rambot Core is UP."

# 2.5 Start Standalone Monitors
echo "Starting Email Monitor..."
$PYTHON_EXE standalone_monitor.py > email.log 2>&1 &
EMAIL_PID=$!

echo "Starting Telegram Monitor..."
$PYTHON_EXE standalone_telegram.py > telegram.log 2>&1 &
TG_PID=$!

# 3. Start the main GUI
echo "Launching Rambot OS GUI..."
$PYTHON_EXE gui.py

# 4. Cleanup on GUI exit
echo "OS exited. Cleaning up services..."
kill $CORE_PID $EMAIL_PID $TG_PID 2>/dev/null
echo "Done."
