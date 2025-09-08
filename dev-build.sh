#!/usr/bin/env bash
set -euo pipefail
APP_VERSION=$(cat VERSION)
GIT_SHA=$(git rev-parse --short HEAD)

echo "Building version $APP_VERSION ($GIT_SHA)..."
docker compose build \
  --build-arg APP_VERSION="$APP_VERSION" \
  --build-arg GIT_SHA="$GIT_SHA"