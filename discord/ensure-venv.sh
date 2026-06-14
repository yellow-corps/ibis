#!/bin/bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_DIR="$BASE_DIR/.venv"
ACTIVATE_SCRIPT="$VENV_DIR/Scripts/activate"

function __ensure_python() {
  unset __ensure_python
  if [ ! -f "$ACTIVATE_SCRIPT" ] || [ "$1" == "--force" ] || [ "$1" == "-f" ]; then
    rm -rf "$VENV_DIR"
    python -m venv "$VENV_DIR" --prompt ibis/.venv || return 1
    # shellcheck disable=SC1090
    source "$ACTIVATE_SCRIPT"
    pip install -r "$BASE_DIR/requirements.dev.txt" --ignore-requires-python || return 1
  elif [ -z "$VIRTUAL_ENV" ]; then
    # shellcheck disable=SC1090
    source "$ACTIVATE_SCRIPT"
  fi
}
__ensure_python "$@"
