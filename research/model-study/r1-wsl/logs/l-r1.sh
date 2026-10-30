cd <repo>/research/model-study
PY=~/.cerebrollm/venv/bin/python
$PY retrieval.py self-check; echo selfcheck EXIT $?
for M in bge-m3 qwen3-embedding:0.6b qwen3-embedding:4b; do
  echo "=== $M $(date -u +%FT%TZ)"
  S=$(date +%s)
  $PY retrieval.py index --model $M 2>&1 | grep -v "indexed" ; echo index EXIT ${PIPESTATUS[0]} SECONDS $(( $(date +%s) - S ))
  S=$(date +%s)
  $PY retrieval.py evaluate --model $M 2>&1 | tail -6; echo evaluate EXIT ${PIPESTATUS[0]} SECONDS $(( $(date +%s) - S ))
  $PY model_guard.py unload $M; echo unload EXIT $?
  $PY model_guard.py check-empty; echo check EXIT $?
done
echo ALLDONE
