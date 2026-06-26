#!/usr/bin/env bash
set -euo pipefail

PROFILE="core"
DRY_RUN=false
SKIP_GO=false
SKIP_TRIVY=false
SKIP_WORDLISTS=false
GO_VERSION="${GO_VERSION:-1.25.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="${LOCK_FILE:-$ROOT_DIR/tools.lock.json}"
OS_NAME="$(uname -s)"
IS_MACOS=false
SUDO=()
if [[ "$OS_NAME" == "Darwin" ]]; then
  IS_MACOS=true
fi

usage() {
  cat <<'USAGE'
Usage: scripts/install-tools.sh [--profile core] [--dry-run] [--skip-go] [--skip-trivy] [--skip-wordlists]

Installs Shikari's local-first verified security tool profile on Debian/Ubuntu,
Kali, and best-effort macOS Homebrew systems. The script is intentionally
profile-based; it does not install every experimental wrapper in the repository.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:?--profile requires a value}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --skip-go)
      SKIP_GO=true
      shift
      ;;
    --skip-trivy)
      SKIP_TRIVY=true
      shift
      ;;
    --skip-wordlists)
      SKIP_WORDLISTS=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$PROFILE" in
  core|recon|web|cloud|forensics|offensive|osint|full) ;;
  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 2
    ;;
esac

run() {
  echo "+ $*"
  if [[ "$DRY_RUN" != "true" ]]; then
    "$@"
  fi
}

run_shell() {
  echo "+ $*"
  if [[ "$DRY_RUN" != "true" ]]; then
    bash -c "$*"
  fi
}

if [[ "$IS_MACOS" == "true" ]]; then
  if ! command -v brew >/dev/null 2>&1; then
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "Dry-run: Homebrew is not installed; package install commands will still be shown."
    else
      echo "Homebrew is required for macOS installs: https://brew.sh/" >&2
      exit 1
    fi
  fi
else
  if [[ "$EUID" -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
    SUDO=(sudo)
  elif [[ "$EUID" -ne 0 ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "Dry-run: sudo is not installed; package install commands will still be shown."
    else
      echo "sudo is required for package installation." >&2
      exit 1
    fi
  fi

  if ! command -v apt-get >/dev/null 2>&1; then
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "Dry-run: apt-get is not installed; Debian package install commands will still be shown."
    else
      echo "This installer supports Debian/Ubuntu/Kali apt-based systems and macOS Homebrew." >&2
      exit 1
    fi
  fi
fi

BASE_APT_PACKAGES=(
  ca-certificates
  curl
  wget
  git
  jq
  unzip
  tar
  build-essential
  python3-pip
  pipx
)

CORE_APT_PACKAGES=(
  nmap
  whois
  dnsutils
  netcat-openbsd
  libpcap0.8
  libpcap-dev
  perl
  libnet-ssleay-perl
  libjson-perl
  libio-socket-ssl-perl
  libxml-writer-perl
  libxml-libxml-perl
)

RECON_APT_PACKAGES=(masscan)
WEB_APT_PACKAGES=(openssl ruby sslscan)
CLOUD_APT_PACKAGES=()
FORENSICS_APT_PACKAGES=(yara radare2)
OFFENSIVE_APT_PACKAGES=(john hashcat hydra)

OSINT_APT_PACKAGES=(libimage-exiftool-perl)

BASE_BREW_PACKAGES=(
  ca-certificates
  curl
  wget
  git
  jq
  go
  pipx
)

CORE_BREW_PACKAGES=(
  nmap
  whois
  bind
  netcat
  nikto
  sqlmap
)

RECON_BREW_PACKAGES=(masscan)
WEB_BREW_PACKAGES=(whatweb wafw00f testssl sslscan)
CLOUD_BREW_PACKAGES=()
FORENSICS_BREW_PACKAGES=(yara radare2)
OFFENSIVE_BREW_PACKAGES=(john hashcat hydra)

OSINT_BREW_PACKAGES=(exiftool)

APT_PACKAGES=("${BASE_APT_PACKAGES[@]}")
BREW_PACKAGES=("${BASE_BREW_PACKAGES[@]}")
case "$PROFILE" in
  core)
    APT_PACKAGES+=("${CORE_APT_PACKAGES[@]}")
    BREW_PACKAGES+=("${CORE_BREW_PACKAGES[@]}")
    ;;
  recon)
    APT_PACKAGES+=("${RECON_APT_PACKAGES[@]}")
    BREW_PACKAGES+=("${RECON_BREW_PACKAGES[@]}")
    ;;
  web)
    APT_PACKAGES+=("${WEB_APT_PACKAGES[@]}")
    BREW_PACKAGES+=("${WEB_BREW_PACKAGES[@]}")
    ;;
  cloud)
    APT_PACKAGES+=("${CLOUD_APT_PACKAGES[@]}")
    BREW_PACKAGES+=("${CLOUD_BREW_PACKAGES[@]}")
    ;;
  forensics)
    APT_PACKAGES+=("${FORENSICS_APT_PACKAGES[@]}")
    BREW_PACKAGES+=("${FORENSICS_BREW_PACKAGES[@]}")
    ;;
  offensive)
    APT_PACKAGES+=("${OFFENSIVE_APT_PACKAGES[@]}")
    BREW_PACKAGES+=("${OFFENSIVE_BREW_PACKAGES[@]}")
    ;;
  osint)
    APT_PACKAGES+=("${OSINT_APT_PACKAGES[@]}")
    BREW_PACKAGES+=("${OSINT_BREW_PACKAGES[@]}")
    ;;
  full)
    APT_PACKAGES+=(
      "${CORE_APT_PACKAGES[@]}"
      "${RECON_APT_PACKAGES[@]}"
      "${WEB_APT_PACKAGES[@]}"
      "${CLOUD_APT_PACKAGES[@]}"
      "${FORENSICS_APT_PACKAGES[@]}"
      "${OFFENSIVE_APT_PACKAGES[@]}"
      "${OSINT_APT_PACKAGES[@]}"
    )
    BREW_PACKAGES+=(
      "${CORE_BREW_PACKAGES[@]}"
      "${RECON_BREW_PACKAGES[@]}"
      "${WEB_BREW_PACKAGES[@]}"
      "${CLOUD_BREW_PACKAGES[@]}"
      "${FORENSICS_BREW_PACKAGES[@]}"
      "${OFFENSIVE_BREW_PACKAGES[@]}"
      "${OSINT_BREW_PACKAGES[@]}"
    )
    ;;
esac

if [[ "$IS_MACOS" == "true" ]]; then
  run brew update
  for package in "${BREW_PACKAGES[@]}"; do
    echo "+ brew install $package"
    if [[ "$DRY_RUN" != "true" ]]; then
      if ! brew install "$package"; then
        echo "Warning: Homebrew package '$package' was not installed; continuing best-effort." >&2
      fi
    fi
  done
else
  run "${SUDO[@]}" apt-get update
  run "${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${APT_PACKAGES[@]}"
fi

install_git_tool() {
  local name="$1"
  local repository="$2"
  local ref="$3"
  local executable="$4"
  local destination="/opt/shikari/tools/$name"
  echo "+ install $name@$ref from $repository"
  if [[ "$DRY_RUN" == "true" ]]; then
    return
  fi
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  git clone --depth 1 --branch "$ref" "$repository" "$tmp_dir/source"
  "${SUDO[@]}" mkdir -p /opt/shikari/tools
  "${SUDO[@]}" rm -rf "$destination"
  "${SUDO[@]}" mv "$tmp_dir/source" "$destination"
  "${SUDO[@]}" ln -sfn "$destination/$executable" "/usr/local/bin/$name"
  rm -rf "$tmp_dir"
}

if [[ "$IS_MACOS" != "true" && ( "$PROFILE" == "core" || "$PROFILE" == "full" ) ]]; then
  install_git_tool nikto https://github.com/sullo/nikto.git 2.6.0 program/nikto.pl
  install_git_tool sqlmap https://github.com/sqlmapproject/sqlmap.git 1.9 sqlmap.py
fi

if [[ "$IS_MACOS" != "true" && ( "$PROFILE" == "web" || "$PROFILE" == "full" ) ]]; then
  install_git_tool whatweb https://github.com/urbanadventurer/WhatWeb.git v0.6.4 whatweb
  install_git_tool testssl.sh https://github.com/testssl/testssl.sh.git v3.2.3 testssl.sh
fi

if [[ "$IS_MACOS" != "true" && ( "$PROFILE" == "osint" || "$PROFILE" == "full" ) ]]; then
  install_git_tool theHarvester https://github.com/laramies/theHarvester.git 4.6.0 theHarvester.py
fi

go_version_ok() {
  if ! command -v go >/dev/null 2>&1; then
    return 1
  fi
  local version
  version="$(go version | awk '{print $3}' | sed 's/^go//')"
  local major minor
  major="${version%%.*}"
  minor="${version#*.}"
  minor="${minor%%.*}"
  [[ "$major" -gt 1 || ( "$major" -eq 1 && "$minor" -ge 24 ) ]]
}

install_go() {
  if [[ "$IS_MACOS" == "true" ]]; then
    run brew install go
    return
  fi

  local arch
  case "$(uname -m)" in
    x86_64|amd64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *)
      echo "Unsupported CPU architecture for Go auto-install: $(uname -m)" >&2
      exit 1
      ;;
  esac

  local tmp_dir
  tmp_dir="$(mktemp -d)"
  local archive="$tmp_dir/go.tgz"
  local url="https://go.dev/dl/go${GO_VERSION}.linux-${arch}.tar.gz"

  run curl -fsSL "$url" -o "$archive"
  run tar -C "$tmp_dir" -xzf "$archive"
  run "${SUDO[@]}" mkdir -p /opt/shikari
  run "${SUDO[@]}" rm -rf "/opt/shikari/go-${GO_VERSION}"
  run "${SUDO[@]}" mv "$tmp_dir/go" "/opt/shikari/go-${GO_VERSION}"
  run "${SUDO[@]}" ln -sfn "/opt/shikari/go-${GO_VERSION}" /opt/shikari/go
  run rm -rf "$tmp_dir"
}

if [[ "$SKIP_GO" != "true" ]]; then
  if go_version_ok; then
    echo "Go toolchain is already new enough: $(go version)"
  else
    install_go
    export PATH="/opt/shikari/go/bin:$PATH"
  fi

  export PATH="/opt/shikari/go/bin:${HOME}/go/bin:$PATH"
  if [[ ! -f "$LOCK_FILE" ]]; then
    echo "Missing tools lock file: $LOCK_FILE" >&2
    exit 1
  fi

  GO_KEYS=(subfinder httpx nuclei naabu katana ffuf gobuster)
  case "$PROFILE" in
    recon) GO_KEYS=(dnsx mapcidr uncover) ;;
    web) GO_KEYS=(tlsx dalfox ffuf gobuster) ;;
    cloud) GO_KEYS=(gitleaks) ;;
    forensics|offensive) GO_KEYS=() ;;
    full) GO_KEYS=(subfinder httpx nuclei naabu katana ffuf gobuster dnsx tlsx mapcidr uncover dalfox gitleaks) ;;
  esac
  if [[ "$DRY_RUN" == "true" ]] && ! command -v jq >/dev/null 2>&1; then
    for key in "${GO_KEYS[@]}"; do
      echo "+ go install -v <locked:$key from $LOCK_FILE>"
    done
  else
    GO_FILTER="$(printf '%s\n' "${GO_KEYS[@]}" | jq -R . | jq -s .)"
    mapfile -t GO_TOOLS < <(
      jq -r --argjson keys "$GO_FILTER" '.go_tools | to_entries[] | select(.key as $k | $keys | index($k)) | .value.module + "@" + .value.ref' "$LOCK_FILE"
    )
    for tool in "${GO_TOOLS[@]}"; do
      run go install -v "$tool"
    done
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    GOPATH_VALUE="${GOPATH:-$HOME/go}"
  else
    GOPATH_VALUE="$(go env GOPATH)"
  fi
  LINK_BIN_DIR="/usr/local/bin"
  if [[ "$IS_MACOS" == "true" && ! -w "$LINK_BIN_DIR" ]]; then
    LINK_BIN_DIR="$HOME/.local/bin"
    run mkdir -p "$LINK_BIN_DIR"
  fi
  for binary in subfinder httpx nuclei naabu katana ffuf gobuster dnsx tlsx mapcidr uncover dalfox gitleaks; do
    if [[ -x "$GOPATH_VALUE/bin/$binary" || "$DRY_RUN" == "true" ]]; then
      if [[ "$IS_MACOS" == "true" ]]; then
        run ln -sf "$GOPATH_VALUE/bin/$binary" "$LINK_BIN_DIR/$binary"
      else
        run "${SUDO[@]}" ln -sf "$GOPATH_VALUE/bin/$binary" "/usr/local/bin/$binary"
      fi
    fi
  done
fi

if [[ "$SKIP_TRIVY" != "true" ]]; then
  if [[ "$PROFILE" == "core" || "$PROFILE" == "cloud" || "$PROFILE" == "full" ]]; then
    if [[ "$IS_MACOS" == "true" ]]; then
      run brew install trivy
    else
      tmp_dir="$(mktemp -d)"
      run curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/9b49920/contrib/install.sh -o "$tmp_dir/install-trivy.sh"
      run "${SUDO[@]}" sh "$tmp_dir/install-trivy.sh" -b /usr/local/bin v0.71.0
      run rm -rf "$tmp_dir"
    fi
  fi
fi

if [[ "$PROFILE" == "cloud" || "$PROFILE" == "full" ]]; then
  run pipx install --force semgrep
  run pipx install --force checkov
fi

if [[ "$PROFILE" == "web" || "$PROFILE" == "full" ]]; then
  run pipx install --force arjun
  run pipx install --force wafw00f
fi

if [[ "$PROFILE" == "forensics" || "$PROFILE" == "full" ]]; then
  run pipx install --force volatility3
fi

if [[ "$PROFILE" == "osint" || "$PROFILE" == "full" ]]; then
  run pipx install --force sherlock-project
  run pipx install --force maigret
  run pipx install --force holehe
  run pipx install --force socialscan
  run pipx install --force shodan
  run pipx install --force censys
  run pipx install --force greynoise
  run pipx install --force h8mail
fi

# Note: vt (VirusTotal CLI) is a Go binary from GitHub releases, not pipx/apt.
# Install manually: https://github.com/VirusTotal/vt-cli/releases

if [[ "$SKIP_WORDLISTS" != "true" && ( "$PROFILE" == "core" || "$PROFILE" == "web" || "$PROFILE" == "full" ) ]]; then
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "+ scripts/install-wordlists.sh"
  else
    SUDO_COMMAND="${SUDO[*]:-}" bash "$(dirname "${BASH_SOURCE[0]}")/install-wordlists.sh"
  fi
fi

if command -v nuclei >/dev/null 2>&1; then
  echo "+ nuclei -update-templates -duc"
  if [[ "$DRY_RUN" != "true" ]] && ! nuclei -update-templates -duc; then
    echo "Warning: nuclei templates could not be updated; the binary remains installed." >&2
  fi
fi

echo
if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry-run complete; verification was skipped."
  exit 0
fi

echo
echo "Verification:"
bash "$(dirname "${BASH_SOURCE[0]}")/verify-tools.sh" --profile "$PROFILE"
