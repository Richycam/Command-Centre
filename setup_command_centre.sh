#!/usr/bin/env bash
#
# setup_command_centre.sh (v3 - permission-safe, paste-safe)
# --------------------------------------------------------------
# Bootstraps everything needed to run "Command Centre" on Ubuntu.
# No sudo is used for venv creation or pip installs, avoiding the
# earlier root-owned-venv permission problem.
#
# Usage:
#   chmod +x setup_command_centre.sh
#   ./setup_command_centre.sh
#
# Run this WITHOUT sudo. It calls sudo internally only for apt.

set -euo pipefail

if [ "$EUID" -eq 0 ]; then
    echo "Do not run this script with sudo or as root."
    echo "Run it as your normal user: ./setup_command_centre.sh"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"

echo "=============================================="
echo " Command Centre - Ubuntu Environment Setup"
echo "=============================================="
echo "Project directory: ${PROJECT_DIR}"
echo "Virtual env target: ${VENV_DIR}"
echo ""

OLD_ROOT_VENV="/root/command_centre"
if [ -d "${OLD_ROOT_VENV}" ]; then
    echo "Found a leftover root-owned venv at ${OLD_ROOT_VENV}"
    echo "This is likely the source of earlier Permission denied errors."
    read -r -p "Remove it now with sudo? [y/N] " REPLY
    if [[ "${REPLY}" =~ ^[Yy]$ ]]; then
        sudo rm -rf "${OLD_ROOT_VENV}"
        echo "Removed."
    else
        echo "Skipping removal, leaving it in place."
    fi
    echo ""
fi

echo "[1/5] Updating apt package index (sudo required here only)"
sudo apt update -y

echo "[2/5] Installing system prerequisites"
sudo apt install -y python3 python3-venv python3-pip python3-dev build-essential

echo "[3/5] Creating user-owned virtual environment at ${VENV_DIR}"
if [ -d "${VENV_DIR}" ]; then
    echo "Virtual environment already exists, skipping creation."
else
    python3 -m venv "${VENV_DIR}"
    echo "Created, owned by $(whoami), no sudo used."
fi

echo "[4/5] Activating virtual environment and upgrading pip"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip setuptools wheel

echo "[5/5] Installing Python packages: dash, plotly, feedparser"
pip install dash plotly feedparser

deactivate

echo ""
echo "=============================================="
echo " Setup complete"
echo "=============================================="
echo ""
echo "To run Command Centre:"
echo "  source venv/bin/activate"
echo "  python command_centre.py"
echo ""
echo "Then open http://127.0.0.1:8050 in your browser."
echo ""
echo "To leave the environment when finished:"
echo "  deactivate"
echo ""
echo "Reminder: never prefix python3 -m venv or pip install with sudo."
echo ""
