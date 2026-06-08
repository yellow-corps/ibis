#!/bin/bash

set -o errexit

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

(
  # shellcheck disable=SC1091
  source "$BASE_DIR/ensure-venv.sh"

  cd "$BASE_DIR"

  "$BASE_DIR/compile.sh"
  "$BASE_DIR/lint.sh"
  "$BASE_DIR/format.sh"
  "$BASE_DIR/tests.sh"
)
