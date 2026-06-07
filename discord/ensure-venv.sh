#!/bin/bash

set -o errexit

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ACTIVATE_SCRIPT="$BASE_DIR/.venv/Scripts/activate"

if [ ! -f "$ACTIVATE_SCRIPT" ]; then
  python -m venv .venv --prompt ibis/.venv
  # shellcheck disable=SC1090
  source "$ACTIVATE_SCRIPT"
  pip install -r requirements.txt --ignore-requires-python
elif [ -z "$VIRTUAL_ENV" ]; then
  # shellcheck disable=SC1090
  source "$ACTIVATE_SCRIPT"
fi
