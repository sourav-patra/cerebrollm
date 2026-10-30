#!/bin/bash
# usage: run.sh LOGNAME ACTION [MODEL]
log=~/cerebrollm-scratch/m/$1.log
shift
echo "=== $(date -u +%FT%TZ) r2_wsl.py $*" >> "$log"
~/.cerebrollm/venv/bin/python -B <repo>/research/model-study/r2_wsl.py "$@" >> "$log" 2>&1
echo "=== exit $? $(date -u +%FT%TZ)" >> "$log"
