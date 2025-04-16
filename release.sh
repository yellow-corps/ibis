#!/bin/bash

set -o errexit

version="$1"

npm version --no-git-tag-version --allow-same-version "$version"

version="$(node -p "require('./package.json').version")"

npm run format-changelog
npm run bump-changelog "$version"
npm run format-changelog
git add CHANGELOG.md package.json package-lock.json
git commit -m "v$version"
git tag "v$version"
git push origin --atomic main "v$version"

function build-and-push-docker() (
  local container="$1"
  local $version="$2"
  cd "$container"
  docker build -t "ghcr.io/yellow-corps/ibis-$container:$version" -f Containerfile .
  docker push "ghcr.io/yellow-corps/ibis-$container:$version"
)

build-and-push-docker discord "v$version"
build-and-push-docker discord latest

build-and-push-docker exporter "v$version"
build-and-push-docker exporter latest

build-and-push-docker shopify "v$version"
build-and-push-docker shopify latest
