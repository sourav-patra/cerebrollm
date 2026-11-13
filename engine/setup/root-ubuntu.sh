#!/bin/bash
# Root step for Ubuntu 24.04 (WSL2 or native). Run once, by a person with sudo:
#   sudo bash engine/setup/root-ubuntu.sh
# Installs the packages the engine needs. cerebrollm runs its own socket-only cluster under
# $HOME/.cerebrollm on port 54329 (see user.sh), so it never uses the packaged PostgreSQL service.
# When this install is what creates the packaged service, it is stopped and disabled again; a
# PostgreSQL service unit that existed before this script, running or not, is left exactly as it was.
# Ollama is a prerequisite and is not installed here.
set -euo pipefail
had_unit=no
systemctl cat postgresql.service >/dev/null 2>&1 && had_unit=yes
apt-get update
apt-get install -y python3.12-venv postgresql-16 postgresql-16-pgvector zstd
if [ "$had_unit" = yes ]; then
  echo "A PostgreSQL service existed before this script; left as it was (cerebrollm uses its own cluster on port 54329)."
else
  systemctl disable --now postgresql 2>/dev/null || true   # no systemd: nothing to disable
fi
