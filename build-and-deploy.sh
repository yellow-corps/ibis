#!/bin/bash

VERSION="$1"

(
  cd discord &&
  docker build -t "ghcr.io/yellow-corps/ibis-discord:$VERSION" -f Containerfile . &&
  docker push "ghcr.io/yellow-corps/ibis-discord:$VERSION"
)

(
  cd exporter &&
  docker build -t "ghcr.io/yellow-corps/ibis-exporter:$VERSION" -f Containerfile . &&
  docker push "ghcr.io/yellow-corps/ibis-exporter:$VERSION"
)

(
  cd shopify &&
  docker build -t "ghcr.io/yellow-corps/ibis-shopify:$VERSION" -f Containerfile . &&
  docker push "ghcr.io/yellow-corps/ibis-shopify:$VERSION"
)
