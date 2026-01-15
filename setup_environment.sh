#!/bin/bash
# This script sets up the complete development environment from a clean state.
# It installs system dependencies, then uses mise to install Python.

set -e # Exit immediately if a command exits with a non-zero status.

echo "--- 1. Installing System Dependencies ---"
sudo apt-get update -y
sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git

echo "--- System Dependencies Installed ---"

echo "--- 2. Installing mise ---"
# Download and execute the official installer in a safe, sequential way
curl -o mise_installer.sh https://mise.run
chmod +x mise_installer.sh
./mise_installer.sh
rm mise_installer.sh # Clean up the installer script
echo "--- mise Installed ---"

echo "--- 3. Installing Python 3.11.0 with mise ---"
# Activate mise in the script's environment
export PATH="$HOME/.local/bin:$PATH"
eval "$(mise activate bash)"

# Install and set the global python version
mise install python@3.11.0
mise use --global python@3.11.0
echo "--- Python Installed ---"

echo "--- Environment Setup Complete ---"
