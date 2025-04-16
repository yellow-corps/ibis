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

changelog="$(npm run get-latest-changelog)"

gh release "v$version" --title "v$version" --notes "$changelog"

./build-and-push-docker.sh $version
