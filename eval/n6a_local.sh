#!/bin/bash
# N6a local phases (Ubuntu). Each phase holds the GPU lock only while it runs, so lanes N7 and M3 can take turns between phases.
# usage: n6a_local.sh prepare | gen MODEL[,MODEL...] ARMS | grade JUDGE MODELS
set -u
R=$(cd "$(dirname "$0")/.." && pwd)
PY=~/.cerebrollm/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
cd $R
case "$1" in
  probe) flock ~/.cerebrollm/gpu.lock $PY eval/n6a_probe.py ;;
  prepare) flock ~/.cerebrollm/gpu.lock $PY eval/run_v2.py prepare --arms A0,A3 ;;
  gen) for m in ${2//,/ }; do echo "== $(date -u +%FT%TZ) waiting for lock: gen $m $3"; flock ~/.cerebrollm/gpu.lock bash -c "echo \"== \$(date -u +%FT%TZ) lock held: gen $m ollama \$(curl -s localhost:11434/api/version)\"; $PY eval/run_v2.py gen $m --arms $3 ${4:+--runs $4}; echo \"== \$(date -u +%FT%TZ) lock released\""; done ;;
  grade) echo "== $(date -u +%FT%TZ) waiting for lock: grade $2"; flock ~/.cerebrollm/gpu.lock bash -c "echo \"== \$(date -u +%FT%TZ) lock held: grade $2 ollama \$(curl -s localhost:11434/api/version)\"; $PY eval/run_v2.py grade --judge $2 --models $3; echo \"== \$(date -u +%FT%TZ) lock released\"" ;;
esac
