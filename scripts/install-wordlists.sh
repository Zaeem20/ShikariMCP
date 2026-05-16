#!/usr/bin/env bash
set -euo pipefail

DEST="${DEST:-/opt/shikari/wordlists}"
SECLISTS_DIR="$DEST/SecLists"

if [[ -d "$SECLISTS_DIR/.git" ]]; then
  echo "+ git -C $SECLISTS_DIR pull --ff-only"
  sudo git -C "$SECLISTS_DIR" pull --ff-only
else
  echo "+ sudo mkdir -p $DEST"
  sudo mkdir -p "$DEST"
  echo "+ sudo git clone --depth 1 https://github.com/danielmiessler/SecLists $SECLISTS_DIR"
  sudo git clone --depth 1 https://github.com/danielmiessler/SecLists "$SECLISTS_DIR"
fi
