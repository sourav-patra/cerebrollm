#!/bin/bash
PY=~/.cerebrollm/venv/bin/python
G=<repo>/research/model-study/model_guard.py
for m in devstral:24b gpt-oss:20b qwen3:14b qwen3:8b; do
  echo "=== pull $m $(date -u +%FT%TZ)"
  $PY -B $G pull $m; echo "exit $? $(date -u +%FT%TZ)"
done
echo ALLDONE
