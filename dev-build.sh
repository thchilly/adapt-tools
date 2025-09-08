#!/usr/bin/env bash
set -euo pipefail

APP_VERSION="$(cat VERSION)"
GIT_SHA="$(git rev-parse --short HEAD)"

# make the vars available to BOTH build and up (needed for build args)
export APP_VERSION GIT_SHA

echo "Building version $APP_VERSION ($GIT_SHA)…"

# optional clean rebuild if you pass --clean
NOCACHE=""
if [[ "${1:-}" == "--clean" ]]; then
  echo "Doing a clean rebuild (down -v + build --no-cache)…"
  docker compose down -v || true
  NOCACHE="--no-cache"
fi

# build (add --no-cache if you ran with --clean)
docker compose build $NOCACHE

# bring the stack up
docker compose up -d