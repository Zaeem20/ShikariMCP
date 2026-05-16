#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="core"
JSON=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:?--profile requires a value}"
      shift 2
      ;;
    --json)
      JSON=true
      shift
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/verify-tools.sh [--profile core] [--json]

Verifies the binaries declared in Shikari's packaged tool manifest.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python not found: $PYTHON_BIN" >&2
  exit 127
fi

ARGS=(tools verify --profile "$PROFILE")
if [[ "$JSON" == "true" ]]; then
  ARGS+=(--json)
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m shikari.server "${ARGS[@]}"
