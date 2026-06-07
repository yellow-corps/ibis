#!/bin/bash

set -o errexit

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

(
  # shellcheck disable=SC1091
  source "$BASE_DIR/ensure-venv.sh"

  cd "$BASE_DIR"
  
  echo "Running tests in cogs"
  python -m unittest discover -s cogs

  # Uncomment once tests exist in ibis
  # echo "Running tests in ibis"
  # python -m unittest discover -s ibis
)
