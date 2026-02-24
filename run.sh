#!/bin/bash

# TalkBubble One-Click Start Script
# This script sets up the environment and launches the application.

# Define colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting TalkBubble...${NC}"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install -r requirements.txt
# Ensure qwen-asr is installed (sometimes missed if not in requirements)
pip install qwen-asr modelscope

# Run the application
echo -e "${GREEN}Launching TalkBubble UI...${NC}"
# Use python from venv directly to be sure
./.venv/bin/python src/main.py
