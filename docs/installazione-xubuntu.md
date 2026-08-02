# Quick installation of TruMetraPla on Xubuntu

This guide summarizes the steps to download, build, and install TruMetraPla on Xubuntu (or other Ubuntu 22.04+ based distributions).

## Quick procedure

### Prerequisites

```bash
sudo apt update
sudo apt install -y python3-venv python3-full desktop-file-utils
```

### Build the Linux package in an isolated environment

```bash
cd ~/Downloads/TruMetraPla
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .[build]
trumetrapla build-linux
```

At the end, the archive `dist/TruMetraPla-linux.tar.gz` is generated.

### Install the package

```bash
cd dist
tar -xf TruMetraPla-linux.tar.gz
cd TruMetraPla-linux
# optional: install to a custom path
# PREFIX="$HOME/.local" BIN_DEST="$HOME/.local/bin" sudo -E ./install.sh
sudo ./install.sh
```

## Useful notes

- To change the path without modifying the script:

  ```bash
  PREFIX="$HOME/.local" BIN_DEST="$HOME/.local/bin" ./install.sh
  ```

- Use `sudo -E` only if administrative permissions are needed for the chosen destinations.
- If you encounter the `externally-managed-environment` error during dependency installation, make sure you have activated the virtual environment before running `pip install .[build]`.

## Windows automation

For completeness, you can use the included batch script to quickly generate the Windows package:

```bat
installer\Build-TruMetraPla.bat --dist C:\Output\Path
```

This command leverages the build infrastructure already present in the repository to create artifacts destined for Windows.