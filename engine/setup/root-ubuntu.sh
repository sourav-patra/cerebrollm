#!/bin/bash
# Root step for Ubuntu 24.04 (WSL2 or native). Run once, by a person with sudo:
#   sudo bash engine/setup/root-ubuntu.sh
# Installs the packages the engine needs and disables the packaged PostgreSQL service, because
# cerebrollm runs its own socket-only cluster under $HOME/.cerebrollm (see user.sh).
# Ollama is a prerequisite and is not installed here.
set -euo pipefail
apt-get update
apt-get install -y python3.12-venv postgresql-16 postgresql-16-pgvector zstd
systemctl disable --now postgresql 2>/dev/null || true   # no systemd: nothing to disable
