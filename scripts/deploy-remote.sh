#!/usr/bin/env bash
# ShikariMCP remote deployment script — run ON the Linux server.
# Automates: clone, install dependencies, install security binaries,
# verify, and start the HTTP server.
#
# Usage:
#   bash scripts/deploy-remote.sh --profile core --port 8080
#   bash scripts/deploy-remote.sh --profile osint --port 8080 --enable-active
#   bash scripts/deploy-remote.sh --profile full --port 8080 --enable-active --enable-offensive
#
# Prerequisites on the Linux server:
#   - Python 3.11+ (python3 --version)
#   - git, curl, jq
#   - sudo access (for apt installs and /usr/local/bin symlinks)
#   - For Go tools: the script installs Go automatically if missing
set -euo pipefail

# --- Defaults ---
PROFILE="core"
PORT="8080"
HOST="127.0.0.1"
API_KEY=""
ENABLE_ACTIVE=false
ENABLE_OFFENSIVE=false
ENABLE_CREDENTIAL=false
ENABLE_LEGACY=false
ENABLE_EXPERIMENTAL=false
TARGET_ALLOWLIST=""
REPO_URL="https://github.com/Zaeem20/ShikariMCP.git"
REPO_DIR="$HOME/ShikariMCP"
SKIP_INSTALL=false

usage() {
  cat <<'USAGE'
Usage: scripts/deploy-remote.sh [OPTIONS]

Options:
  --profile NAME        Tool profile: core, recon, web, cloud, forensics, offensive, osint, full
                        (default: core)
  --port PORT           HTTP port (default: 8080)
  --host HOST           Bind address (default: 127.0.0.1 — use 0.0.0.0 for remote access)
  --api-key KEY         API key for HTTP auth (REQUIRED for HTTP)
  --enable-active       Allow active scanning tools
  --enable-offensive    Allow offensive tools (exploitation, payloads, MITM)
  --enable-credential   Allow credential testing tools
  --enable-legacy       Expose legacy wrapper catalog
  --enable-experimental Expose experimental agents
  --target-allowlist X  Comma-separated authorized targets (domains, CIDRs, paths)
  --repo URL            Git repo URL (default: upstream ShikariMCP)
  --dir PATH            Clone directory (default: ~/ShikariMCP)
  --skip-install        Skip binary installation (use if already installed)
  -h, --help            Show this help

Examples:
  # Core profile, localhost only, SSH tunnel from Windows
  bash scripts/deploy-remote.sh --profile core --api-key "my-secret-key"

  # OSINT profile with active tools, accessible from network
  bash scripts/deploy-remote.sh --profile osint --api-key "my-secret-key" \
    --host 0.0.0.0 --enable-active --target-allowlist "example.com,10.0.0.0/8"

  # Full arsenal (use with caution)
  bash scripts/deploy-remote.sh --profile full --api-key "my-secret-key" \
    --enable-active --enable-offensive --enable-credential \
    --target-allowlist "lab.local,10.10.0.0/16"
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:?--profile requires a value}"; shift 2 ;;
    --port) PORT="${2:?--port requires a value}"; shift 2 ;;
    --host) HOST="${2:?--host requires a value}"; shift 2 ;;
    --api-key) API_KEY="${2:?--api-key requires a value}"; shift 2 ;;
    --enable-active) ENABLE_ACTIVE=true; shift ;;
    --enable-offensive) ENABLE_OFFENSIVE=true; shift ;;
    --enable-credential) ENABLE_CREDENTIAL=true; shift ;;
    --enable-legacy) ENABLE_LEGACY=true; shift ;;
    --enable-experimental) ENABLE_EXPERIMENTAL=true; shift ;;
    --target-allowlist) TARGET_ALLOWLIST="${2:?--target-allowlist requires a value}"; shift 2 ;;
    --repo) REPO_URL="${2:?--repo requires a value}"; shift 2 ;;
    --dir) REPO_DIR="${2:?--dir requires a value}"; shift 2 ;;
    --skip-install) SKIP_INSTALL=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$API_KEY" ]]; then
  echo "ERROR: --api-key is required for HTTP transport." >&2
  echo "Generate one with: openssl rand -hex 32" >&2
  exit 1
fi

echo "========================================"
echo " ShikariMCP Remote Deployment"
echo "========================================"
echo "  Profile:  $PROFILE"
echo "  Host:     $HOST"
echo "  Port:     $PORT"
echo "  Repo:     $REPO_URL"
echo "  Dir:      $REPO_DIR"
echo "  Active:   $ENABLE_ACTIVE"
echo "  Offensive: $ENABLE_OFFENSIVE"
echo "  Credential: $ENABLE_CREDENTIAL"
echo "========================================"
echo

# --- Step 1: Clone or update repo ---
echo "[1/5] Clone or update repository..."
if [[ -d "$REPO_DIR/.git" ]]; then
  echo "  Repository exists, pulling latest..."
  cd "$REPO_DIR"
  git pull --ff-only
else
  git clone "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
fi
echo

# --- Step 2: Install Python dependencies ---
echo "[2/5] Install Python dependencies..."
if ! command -v uv >/dev/null 2>&1; then
  echo "  Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv sync --group dev
echo

# --- Step 3: Install security binaries ---
if [[ "$SKIP_INSTALL" == "true" ]]; then
  echo "[3/5] Skipping binary installation (--skip-install)"
else
  echo "[3/5] Install security binaries (profile: $PROFILE)..."
  echo "  This may take 5-15 minutes depending on the profile."
  echo "  Go tools will be compiled from source."
  bash scripts/install-tools.sh --profile "$PROFILE"
fi
echo

# --- Step 4: Verify installation ---
echo "[4/5] Verify installation..."
uv run shikari-mcp tools verify --profile "$PROFILE" --json | jq '{profile, installed, total, missing}'
echo

# --- Step 5: Start server ---
echo "[5/5] Start ShikariMCP server..."
echo
echo "  Endpoint: http://$HOST:$PORT/mcp"
echo "  Auth:     Bearer $API_KEY"
echo
echo "  From Windows, create an SSH tunnel:"
echo "    ssh -L $PORT:localhost:$PORT user@this-server"
echo "  Then connect your AI client to:"
echo "    http://localhost:$PORT/mcp"
echo

CMD=(
  uv run shikari-mcp
  --transport http
  --host "$HOST"
  --port "$PORT"
  --api-key "$API_KEY"
  --tool-profile "$PROFILE"
)

if [[ "$HOST" == "127.0.0.1" || "$HOST" == "localhost" ]]; then
  CMD+=(--local)
fi
if [[ "$ENABLE_ACTIVE" == "true" ]]; then CMD+=(--enable-active-tools); fi
if [[ "$ENABLE_OFFENSIVE" == "true" ]]; then CMD+=(--enable-offensive-tools); fi
if [[ "$ENABLE_CREDENTIAL" == "true" ]]; then CMD+=(--enable-credential-tools); fi
if [[ "$ENABLE_LEGACY" == "true" ]]; then CMD+=(--enable-legacy-tools); fi
if [[ "$ENABLE_EXPERIMENTAL" == "true" ]]; then CMD+=(--enable-experimental-tools); fi
if [[ -n "$TARGET_ALLOWLIST" ]]; then CMD+=(--target-allowlist "$TARGET_ALLOWLIST"); fi

echo "  Full command:"
echo "    ${CMD[*]}"
echo
echo "  Press Ctrl+C to stop."
echo "========================================"

exec "${CMD[@]}"