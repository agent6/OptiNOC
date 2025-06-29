#!/usr/bin/env bash
set -euo pipefail

# Install system dependencies for pygraphviz and other packages
sudo apt-get update
sudo apt-get install -y graphviz graphviz-dev libgraphviz-dev pkg-config python3-venv python3-dev build-essential

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Upgrade pip and install Python requirements
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. Activate the environment with 'source venv/bin/activate'"
