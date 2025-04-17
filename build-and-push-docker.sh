#!/bin/bash

set -o errexit

version="$1"

function build-and-push-docker() (
  local container="$1"
  local version="$2"
  cd "$container"
  docker build --platform linux/amd64,linux/arm64 -t "ghcr.io/yellow-corps/ibis-$container:$version" -f Containerfile .
  docker push "ghcr.io/yellow-corps/ibis-$container:$version"
)

build-and-push-docker discord "v$version"
build-and-push-docker discord latest

build-and-push-docker exporter "v$version"
build-and-push-docker exporter latest

build-and-push-docker shopify "v$version"
build-and-push-docker shopify latest
