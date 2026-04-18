#!/bin/sh

do-python() {
  if [[ -n "$WITH_OTEL" ]]; then
    echo "Starting with otel instrumentation"
    .local/bin/opentelemetry-instrument "$@"
  else
    echo "Starting"
    python "$@"
  fi
}

entrypoint() {
  do-python \
    .local/bin/redbot ibis \
    --rpc \
    --team-developers-are-owners \
    --mentionable \
    --prefix "[@]" \
    "$@"
}

entrypoint "$@"
