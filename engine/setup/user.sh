#!/bin/bash
# User step (no root) for Ubuntu 24.04: virtual environment, packages, and a socket-only
# PostgreSQL 16 cluster with pgvector. Idempotent. Run after root-ubuntu.sh:
#   bash engine/setup/user.sh
# Ollama is a prerequisite. On Windows with WSL2 mirrored networking it runs on Windows and is
# reachable here on 127.0.0.1:11434.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PG=/usr/lib/postgresql/16/bin
STATE="$HOME/.cerebrollm"

curl -fsS -m 5 http://127.0.0.1:11434/api/version || { echo "Ollama not reachable on 127.0.0.1:11434"; exit 1; }
echo

mkdir -p "$STATE/pip-cache" "$STATE/tmp"   # pip and venv write only under $STATE
export TMPDIR="$STATE/tmp" PIP_CACHE_DIR="$STATE/pip-cache"
[ -x "$STATE/venv/bin/python" ] || python3.12 -m venv "$STATE/venv"
"$STATE/venv/bin/pip" install -q --timeout 120 --retries 10 -r "$REPO/engine/requirements.txt"

if [ ! -f "$STATE/pg16/PG_VERSION" ]; then
  mkdir -p "$STATE/pg16"
  $PG/initdb -D "$STATE/pg16" -U cerebrollm --auth=trust
  mkdir -p "$STATE/pg16/sock"
  printf "listen_addresses = ''\nunix_socket_directories = '%s'\nport = 54329\n" "$STATE/pg16/sock" >> "$STATE/pg16/postgresql.conf"
fi
$PG/pg_ctl -D "$STATE/pg16" status >/dev/null || $PG/pg_ctl -D "$STATE/pg16" -l "$STATE/pg16/server.log" -w start
$PG/psql -h "$STATE/pg16/sock" -p 54329 -U cerebrollm -d postgres -lqt | cut -d'|' -f1 | grep -qw rag_local \
  || $PG/createdb -h "$STATE/pg16/sock" -p 54329 -U cerebrollm rag_local
$PG/psql -h "$STATE/pg16/sock" -p 54329 -U cerebrollm rag_local -c 'CREATE EXTENSION IF NOT EXISTS vector;'

echo "USER SETUP DONE"
