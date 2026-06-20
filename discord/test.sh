#!/bin/bash

set -o errexit

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

(
  # shellcheck disable=SC1091
  source "$BASE_DIR/ensure-venv.sh"

  cd "$BASE_DIR"
  
  echo "Running tests"
  python -m coverage run

  echo "Producting coverage reports"
  python -m coverage html
)
