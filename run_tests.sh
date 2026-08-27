#!/usr/bin/env bash
# Script to execute Python Network Test Automation Framework test suite

set -e

echo "======================================================="
echo "   Python Network Test Automation Framework - Phase 1   "
echo "======================================================="

# Ensure virtual environment is activated if present
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
fi

echo "Running Pytest suite..."
python3 -m pytest "$@"
