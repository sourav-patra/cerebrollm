#!/bin/bash
# N6a step 1 (Ubuntu): copy the 20 release notes into the corpus, rebuild the live index under the GPU lock.
# Attempt 1 used `engine/bin/cerebrollm index` and failed on Windows port exhaustion (see the log); this version runs the
# same indexer.run_index through the paced wrapper research/model-study/r1_live_index.py (step L, item 1).
set -u
R=$(cd "$(dirname "$0")/.." && pwd)   # repo root
LOG=$R/eval/runs/logs/n6a-index.log
exec >>"$LOG" 2>&1
echo "== $(date -u +%FT%TZ) status before"
$R/engine/bin/cerebrollm status
for d in ollama promptfoo llama_index; do
  mkdir -p ~/cerebrollm-corpus/$d
  for f in $R/eval/v2-sources/$d/*.md; do
    b=$(basename "$f")
    if [ -e ~/cerebrollm-corpus/$d/$b ]; then echo "exists, kept: $d/$b"; else cp "$f" ~/cerebrollm-corpus/$d/$b; fi
    cmp "$f" ~/cerebrollm-corpus/$d/$b && echo "same: $d/$b"
  done
done
echo "== $(date -u +%FT%TZ) waiting for gpu.lock"
flock ~/.cerebrollm/gpu.lock bash -c "echo \"== \$(date -u +%FT%TZ) lock held, index start\"; cd $R/research/model-study && PYTHONDONTWRITEBYTECODE=1 ~/.cerebrollm/venv/bin/python r1_live_index.py; echo \"index exit \$?\"; echo \"== \$(date -u +%FT%TZ) lock released\""
echo "== $(date -u +%FT%TZ) status after"
$R/engine/bin/cerebrollm status
