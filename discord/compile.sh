#!/bin/bash

set -o errexit

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

(
  # shellcheck disable=SC1091
  source "$BASE_DIR/ensure-venv.sh"

  cd "$BASE_DIR"
  
  echo "Running compile"
  find . \
    \( -name "submodules" -o -name ".venv" \) -prune \
    -o -type f -name "*.py" \
    -exec python -m py_compile {} \;
)
