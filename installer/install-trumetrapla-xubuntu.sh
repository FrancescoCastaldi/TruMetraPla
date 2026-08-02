#!/usr/bin/env bash
set -euo pipefail
#
# Script to build and package TruMetraPla on Linux (Ubuntu/Debian)
# Installs dependencies, creates a virtual environment and generates the .tar.gz package
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
VENV_DIR="$ROOT_DIR/.venv"

usage() {
    cat <<'USAGE'
Usage: install-TruMetraPla-xubuntu.sh [--dist DIR] [--skip-apt]

  --dist DIR    Specify the output folder for the Linux package (default: dist/)
  --skip-apt    Do not run "sudo apt update && sudo apt install ..." (dependencies already present)
USAGE
}

RUN_APT=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dist)
            DIST_DIR="$2"
            shift 2
            ;;
        --skip-apt)
            RUN_APT=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unrecognized option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

log() {
    printf '\e[1;34m[TruMetraPla]\e[0m %s\n' "$1"
}

if [[ $RUN_APT -eq 1 ]]; then
    if command -v apt >/dev/null 2>&1; then
        log "Updating APT indexes"
        sudo apt update
        log "Installing system packages"
        sudo apt install -y python3-venv python3-full desktop-file-utils python3-tk
    else
        log "APT not available on this system: skipping package installation"
        log "Install python3-venv, python3-full and desktop-file-utils manually or use --skip-apt"
    fi
else
    log "Skipping system package installation"
fi

if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment in $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

log "Updating pip"
pip install --upgrade pip

log "Installing TruMetraPla in build mode"
pip install "$ROOT_DIR"[build]

mkdir -p "$DIST_DIR"

log "Generating the Linux package"
trumetrapla build-linux --dist "$DIST_DIR"

PACKAGE_PATH="$DIST_DIR/TruMetraPla-linux.tar.gz"

if [[ -f "$PACKAGE_PATH" ]]; then
    log "Package ready: $PACKAGE_PATH"
    log "Extract and run ./install.sh with sudo or with custom PREFIX/BIN_DEST variables"
else
    echo "Error: package not generated" >&2
    exit 1
fi