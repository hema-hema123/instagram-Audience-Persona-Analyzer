#!/usr/bin/env bash
set -e
# shellcheck disable=SC1091
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
