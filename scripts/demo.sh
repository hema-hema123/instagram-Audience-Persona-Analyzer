#!/usr/bin/env bash
set -e
# shellcheck disable=SC1091
source .venv/bin/activate
python -m scripts.demo_classify
if command -v jq >/dev/null 2>&1; then
  jq . data/report.json
else
  cat data/report.json
fi
