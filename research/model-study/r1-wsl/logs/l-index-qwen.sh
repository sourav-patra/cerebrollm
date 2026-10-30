cd <repo>/research/model-study
S=$(date +%s)
date -u +%FT%TZ
psql -h ~/.cerebrollm/pg16/sock -p 54329 -U cerebrollm rag_local -tc "select 'live rows before swap', count(*) from data_chunks"
~/.cerebrollm/venv/bin/python model_guard.py check-empty || ~/.cerebrollm/venv/bin/python model_guard.py unload qwen3-embedding:0.6b
~/.cerebrollm/venv/bin/python r1_live_index.py
echo EXIT $?
echo WALL_SECONDS $(( $(date +%s) - S ))
cd ../../engine
bin/cerebrollm status
psql -h ~/.cerebrollm/pg16/sock -p 54329 -U cerebrollm rag_local -c "\dt"
bin/cerebrollm search "how do I pull a model with the ollama CLI" --k 3 | head -12
