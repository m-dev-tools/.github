#!/usr/bin/env bash
# m-dev-tools — interactive bootstrap installer.
#
# Recommended invocation (review first, then run):
#   curl -O https://raw.githubusercontent.com/m-dev-tools/.github/main/setup.sh
#   less ./setup.sh
#   bash ./setup.sh
#
# Or, for the convinced:
#   bash <(curl -fsSL https://raw.githubusercontent.com/m-dev-tools/.github/main/setup.sh)
#
# Flags:
#   -y, --yes        non-interactive; accept defaults
#   -d, --dir PATH   install root (default: ~/m-dev-tools)
#   -h, --help       this message
#
# What it does:
#   1. Detect OS (Linux distro / macOS) and check for required tools
#      (git, docker, python3.12+, uv, make). Prints install commands
#      for anything missing and exits — never sudo's.
#   2. Verifies the Docker daemon is reachable.
#   3. Clones m-cli into the chosen install root.
#   4. Delegates the rest (sibling clones, venv install, engine
#      install + start, m doctor verification) to `make bootstrap`
#      inside m-cli.
#   5. Prints PATH-setup advice and a "next steps" pointer to the
#      TDD lifecycle walkthrough.
#
# Idempotent — re-running on an already-installed host skips the
# clones and re-verifies via `m doctor`.

set -euo pipefail

# ── flag parsing ─────────────────────────────────────────────────────
NONINTERACTIVE=0
M_DEV_HOME_ARG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)  NONINTERACTIVE=1; shift ;;
    -d|--dir)  M_DEV_HOME_ARG="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,/^set -/p' "$0" | sed 's/^# \{0,1\}//' | head -n -1
      exit 0 ;;
    *) printf 'unknown flag: %s\n' "$1" >&2; exit 2 ;;
  esac
done

# ── pretty-print helpers (degrade gracefully on no-tty) ──────────────
if [[ -t 1 ]]; then
  RED=$'\033[1;31m'; YEL=$'\033[1;33m'; GRN=$'\033[1;32m'
  CYA=$'\033[1;36m'; RST=$'\033[0m'
else
  RED=""; YEL=""; GRN=""; CYA=""; RST=""
fi
info() { printf '%s==>%s %s\n' "$CYA" "$RST" "$*"; }
warn() { printf '%sWARN%s %s\n' "$YEL" "$RST" "$*" >&2; }
fail() { printf '%sFAIL%s %s\n' "$RED" "$RST" "$*" >&2; exit 1; }
ok()   { printf '  %s✓%s %s\n'  "$GRN" "$RST" "$*"; }

ask() {
  # ask "prompt" "default" — read interactively, return default in -y mode.
  local prompt="$1" default="$2" reply
  if (( NONINTERACTIVE )); then
    printf '%s\n' "$default"
    return 0
  fi
  read -r -p "$prompt [$default]: " reply
  printf '%s\n' "${reply:-$default}"
}

# ── OS detection ─────────────────────────────────────────────────────
detect_os() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    printf 'macos\n'
    return 0
  fi
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    case "${ID:-unknown}" in
      ubuntu|debian|linuxmint|pop) printf 'debian\n' ;;
      fedora|rhel|centos|rocky|almalinux) printf 'fedora\n' ;;
      arch|manjaro|endeavouros) printf 'arch\n' ;;
      *) printf 'linux-other\n' ;;
    esac
    return 0
  fi
  printf 'unsupported\n'
}

OS=$(detect_os)
case "$OS" in
  macos|debian|fedora|arch|linux-other)
    info "Detected OS: $OS" ;;
  unsupported)
    fail "Unsupported OS. m-dev-tools targets Linux (apt/dnf/pacman) and macOS." ;;
esac

# ── arch detection ───────────────────────────────────────────────────
ARCH_RAW=$(uname -m)
case "$ARCH_RAW" in
  arm64|aarch64) ARCH=arm64 ;;
  x86_64|amd64)  ARCH=amd64 ;;
  *) ARCH="$ARCH_RAW"
     warn "Unknown arch: $ARCH_RAW — proceeding without arch compatibility check" ;;
esac
info "Detected arch: $ARCH"

install_hint() {
  # Print a one-line install hint for the given package on the detected OS.
  local pkg="$1"
  case "$OS" in
    macos)  printf '  brew install %s\n' "$pkg" ;;
    debian) printf '  sudo apt install %s\n' "$pkg" ;;
    fedora) printf '  sudo dnf install %s\n' "$pkg" ;;
    arch)   printf '  sudo pacman -S %s\n' "$pkg" ;;
    *)      printf '  install %s via your package manager\n' "$pkg" ;;
  esac
}

# ── pre-flight ───────────────────────────────────────────────────────
info "Pre-flight checks..."
missing=0

# git
if command -v git >/dev/null; then
  ok "git present ($(git --version | awk '{print $3}'))"
else
  warn "git not found."
  install_hint git
  missing=1
fi

# docker
if command -v docker >/dev/null; then
  ok "docker present ($(docker --version | awk '{print $3}' | tr -d ,))"
else
  warn "docker not found."
  case "$OS" in
    debian) install_hint docker.io ;;
    macos)  printf '  brew install --cask docker-desktop  # then launch Docker Desktop\n' ;;
    *)      install_hint docker ;;
  esac
  missing=1
fi

# make
if command -v make >/dev/null; then
  ok "make present"
else
  warn "make not found."
  install_hint make
  missing=1
fi

# python 3.12+
PYTHON=""
for py in python3.12 python3.13 python3 python; do
  if command -v "$py" >/dev/null && \
     "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
    PYTHON="$py"
    break
  fi
done
if [[ -n "$PYTHON" ]]; then
  ok "python ≥ 3.12 present ($("$PYTHON" --version 2>&1))"
else
  warn "python 3.12+ not found."
  case "$OS" in
    macos)  printf '  brew install python@3.12\n' ;;
    debian) printf '  sudo apt install python3.12 python3.12-venv\n' ;;
    fedora) printf '  sudo dnf install python3.12\n' ;;
    arch)   printf '  sudo pacman -S python\n' ;;
    *)      install_hint python3.12 ;;
  esac
  missing=1
fi

# uv
if command -v uv >/dev/null; then
  ok "uv present ($(uv --version | awk '{print $2}'))"
else
  warn "uv not found."
  printf '  curl -LsSf https://astral.sh/uv/install.sh | sh\n'
  missing=1
fi

# docker daemon reachable
if docker info >/dev/null 2>&1; then
  ok "docker daemon reachable"
else
  warn "docker daemon not running."
  case "$OS" in
    macos)
      printf '  Open Docker Desktop and wait for the daemon to start.\n' ;;
    debian|fedora|arch)
      printf '  sudo systemctl start docker\n'
      printf '  sudo usermod -aG docker $USER  # then log out / back in for group to take effect\n' ;;
    *)
      printf '  Start the Docker daemon for your platform.\n' ;;
  esac
  missing=1
fi

if (( missing )); then
  fail "fix the prerequisites above, then re-run setup.sh."
fi

# ── engine-image arch compatibility ──────────────────────────────────
# The bootstrap will pull ghcr.io/m-dev-tools/m-test-engine. If that image
# has no manifest entry for the host arch, surface it now and pin the
# platform so Docker runs the amd64 image under emulation rather than
# failing mid-bootstrap with a cryptic "no matching manifest" error.
ENGINE_IMAGE="ghcr.io/m-dev-tools/m-test-engine:0.1.0"
if [[ "$ARCH" == "arm64" || "$ARCH" == "amd64" ]]; then
  info "Checking engine image manifest for $ARCH..."
  if manifest=$(docker manifest inspect "$ENGINE_IMAGE" 2>/dev/null); then
    if printf '%s' "$manifest" | grep -q "\"architecture\": \"$ARCH\""; then
      ok "engine image $ENGINE_IMAGE has $ARCH manifest"
    else
      warn "Engine image $ENGINE_IMAGE has no $ARCH manifest."
      warn "Setting DOCKER_DEFAULT_PLATFORM=linux/amd64 — engine will run under emulation."
      export DOCKER_DEFAULT_PLATFORM=linux/amd64
      if (( ! NONINTERACTIVE )); then
        read -r -p "Continue with linux/amd64 emulation? [Y/n]: " reply
        case "${reply:-Y}" in
          [Nn]*) fail "aborted by user. Re-run once a native $ARCH image is published." ;;
        esac
      fi
    fi
  else
    warn "Could not inspect $ENGINE_IMAGE manifest — skipping arch compatibility check."
    warn "If the bootstrap fails with 'no matching manifest', re-run with: DOCKER_DEFAULT_PLATFORM=linux/amd64 bash setup.sh"
  fi
fi

# ── confirm install location ─────────────────────────────────────────
M_DEV_HOME=$(ask "Install m-dev-tools under" "${M_DEV_HOME_ARG:-$HOME/m-dev-tools}")
info "Installing to: $M_DEV_HOME"
mkdir -p "$M_DEV_HOME"
cd "$M_DEV_HOME"

# ── clone m-cli ──────────────────────────────────────────────────────
if [[ -d m-cli/.git ]]; then
  info "m-cli already cloned — skipping"
else
  info "Cloning m-cli..."
  git clone https://github.com/m-dev-tools/m-cli
fi

# ── delegate to make bootstrap ───────────────────────────────────────
info "Delegating to 'make bootstrap' inside m-cli..."
cd m-cli
make bootstrap

# ── next steps ───────────────────────────────────────────────────────
printf '\n'
ok "Setup complete."
cat <<NEXT

Next steps:

  1. Add m-cli to your PATH (paste into ~/.bashrc or ~/.zshrc):
       export PATH="$M_DEV_HOME/m-cli/.venv/bin:\$PATH"

  2. Verify on a new shell:
       m --version
       m doctor

  3. Read the TDD lifecycle walkthrough — exercises every m subcommand
     end-to-end against a small data-analysis app:
       $M_DEV_HOME/m-cli/docs/m-tdd-lifecycle-walkthrough.md

  4. Start a project of your own:
       mkdir -p ~/m-work && cd ~/m-work
       m new myapp && cd myapp
       m ci init --write
       m test tests

NEXT
