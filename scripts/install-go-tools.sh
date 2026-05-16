#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="${LOCK_FILE:-$ROOT_DIR/tools.lock.json}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 1
fi

if ! command -v go >/dev/null 2>&1; then
  echo "go is required; run scripts/install-tools.sh first" >&2
  exit 1
fi

jq -r '.go_tools[] | .module + "@" + .ref' "$LOCK_FILE" | while read -r tool; do
  echo "+ go install -v $tool"
  go install -v "$tool"
done
