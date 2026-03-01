#!/usr/bin/env bash
set -e
python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo "✅ Environment ready. Run: source .venv/bin/activate && make demo"
