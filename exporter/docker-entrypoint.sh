#!/bin/sh

do-node() {
  if [[ -n "$WITH_OTEL" ]]; then
    echo "Starting with otel instrumentation"
    node --require @opentelemetry/auto-instrumentations-node/register "$@"
  else
    node "$@"
  fi
}

entrypoint() {
  export METADATA_SERVER_DETECTION=none
  do-node --trace-uncaught --trace-warnings index.mjs
}

entrypoint
