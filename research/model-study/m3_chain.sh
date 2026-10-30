#!/bin/bash
# Lane M3 GPU phases. Each phase takes ~/.cerebrollm/gpu.lock on its own and releases it when it ends, so the other lanes get turns.
# A phase waits for the lock until DEADLINE (06:30 IST on 2026-10-30 by default); if the lock is still busy then, the chain stops
# and the remaining phases stay "not measured". Usage: bash m3_chain.sh PHASE...   (phases: smoke qwen-correct qwen-speed qwen-ctx-4 qwen-ctx-0 glm-correct glm-speed glm-ctx)
cd "$(dirname "$0")" || exit 1
PY=~/.cerebrollm/venv/bin/python
QWEN=qwen3.6:35b-a3b-coding-mtp-q4_K_M
GLM=glm-4.7-flash:q4_K_M
LOCK=~/.cerebrollm/gpu.lock
DEADLINE=${DEADLINE:-$(TZ=Asia/Kolkata date -d '2026-10-30 06:30' +%s)}
LOGS=r2-wsl/logs
mkdir -p "$LOGS"

phase() {  # name, command...
  local name=$1; shift
  local wait=$(( DEADLINE - $(date +%s) ))
  if [ "$wait" -le 0 ]; then echo "$(date -Is) $name: deadline passed before the phase started; not measured" | tee -a $LOGS/m3-chain.log; return 1; fi
  echo "$(date -Is) $name: waiting for the GPU lock (at most ${wait} s)" | tee -a $LOGS/m3-chain.log
  flock -w "$wait" "$LOCK" bash -c 'echo "$(date -Is) '"$name"': lock taken"; "$@"; rc=$?; echo "$(date -Is) '"$name"': command exit $rc, releasing lock"; exit $rc' _ "$@" >> "$LOGS/m3-$name.log" 2>&1
  local rc=$?
  echo "$(date -Is) $name: exit $rc" | tee -a $LOGS/m3-chain.log
  return $rc
}

for p in "$@"; do
  case $p in
    smoke)        phase smoke $PY -B m3_smoke.py $QWEN ;;
    qwen-correct) phase qwen-correct $PY -B r2_wsl.py correctness $QWEN ;;
    qwen-speed)   phase qwen-speed $PY -B r2_wsl.py speed $QWEN ;;
    qwen-ctx-4)   phase qwen-ctx-4 $PY -B m3_speed.py $QWEN mtp4-think-off ;;
    qwen-ctx-0)   phase qwen-ctx-0 $PY -B m3_speed.py $QWEN mtp0-think-off ;;
    glm-correct)  phase glm-correct $PY -B r2_wsl.py correctness $GLM ;;
    glm-speed)    phase glm-speed $PY -B r2_wsl.py speed $GLM ;;
    glm-ctx)      phase glm-ctx $PY -B m3_speed.py $GLM think-off ;;
    *) echo "unknown phase $p"; exit 2 ;;
  esac || { echo "chain stopped at $p"; exit 1; }
done
