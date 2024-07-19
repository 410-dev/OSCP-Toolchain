#!/bin/bash

# Required apt packages
# python3.12, python3.12-venv python3.12-dev libkrb5-dev

# Check if required packages are installed
if ! dpkg -s python3.12 python3.12-venv python3.12-dev libkrb5-dev >/dev/null 2>&1; then
    echo "Installing required packages..."
    sudo apt-get update
    sudo apt-get install -y python3.12 python3.12-venv python3.12-dev libkrb5-dev
fi

# Set the name for your virtual environment
VENV_NAME=".venv"

# Create venv if not exists
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment..."
    python3.12 -m venv $VENV_NAME
fi

# Activate venv
echo "Activating virtual environment..."
source $VENV_NAME/bin/activate

# Specify pip and python from venv
VENV_PIP="$VENV_NAME/bin/pip"
VENV_PYTHON="$VENV_NAME/bin/python"

# Install requirements in venv
echo "Installing requirements..."
$VENV_PIP install -r requirements.txt

# Start main.py in sudo mode
echo "Starting main.py with sudo privileges..."
sudo $VENV_PYTHON main.py

# Deactivate the virtual environment
deactivate