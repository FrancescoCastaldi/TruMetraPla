#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
VENV_DIR="$ROOT_DIR/.venv"

usage() {
    cat <<'USAGE'
Uso: install-trumetrapla-xubuntu.sh [--dist DIR] [--skip-apt]

  --dist DIR    Specifica la cartella di output per il pacchetto Linux (default: dist/)
  --skip-apt    Non esegue "sudo apt update && sudo apt install ..." (dipendenze già presenti)
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
            echo "Opzione non riconosciuta: $1" >&2
            usage
            exit 1
            ;;
    esac
done

log() {
    printf '\e[1;34m[TruMetraPla]\e[0m %s\n' "$1"
}

if [[ $RUN_APT -eq 1 ]]; then
    log "Aggiornamento indici APT"
    sudo apt update
    log "Installazione pacchetti di sistema"
    sudo apt install -y python3-venv python3-full desktop-file-utils
else
    log "Skip installazione pacchetti di sistema"
fi

if [[ ! -d "$VENV_DIR" ]]; then
    log "Creazione ambiente virtuale in $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

log "Aggiornamento di pip"
pip install --upgrade pip

log "Installazione TruMetraPla in modalità build"
pip install "$ROOT_DIR"[build]

mkdir -p "$DIST_DIR"

log "Generazione pacchetto Linux"
trumetrapla build-linux --dist "$DIST_DIR"

PACKAGE_PATH="$DIST_DIR/TruMetraPla-linux.tar.gz"

if [[ -f "$PACKAGE_PATH" ]]; then
    log "Pacchetto pronto: $PACKAGE_PATH"
    log "Estrai e lancia ./install.sh con sudo o con variabili PREFIX/BIN_DEST personalizzate"
else
    echo "Errore: pacchetto non generato" >&2
    exit 1
fi
