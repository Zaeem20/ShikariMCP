#!/usr/bin/env bash
set -euo pipefail

DEST="${DEST:-/opt/wordlists}"
SECLISTS_REF="${SECLISTS_REF:-2024.4}"
SECLISTS_DIR="$DEST/SecLists"

SUDO=()
if [[ "${EUID}" -ne 0 ]]; then
  if [[ -n "${SUDO_COMMAND:-}" ]]; then
    read -r -a SUDO <<<"$SUDO_COMMAND"
  elif command -v sudo >/dev/null 2>&1; then
    SUDO=(sudo)
  else
    echo "sudo is required to install wordlists under $DEST" >&2
    exit 1
  fi
fi

if [[ -f "$SECLISTS_DIR/Discovery/Web-Content/common.txt" ]]; then
  echo "SecLists common wordlist already exists: $SECLISTS_DIR"
  exit 0
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

echo "+ git clone --depth 1 --branch $SECLISTS_REF https://github.com/danielmiessler/SecLists"
git clone --depth 1 --branch "$SECLISTS_REF" \
  https://github.com/danielmiessler/SecLists "$tmp_dir/SecLists"
"${SUDO[@]}" mkdir -p "$DEST"
"${SUDO[@]}" mv "$tmp_dir/SecLists" "$SECLISTS_DIR"
