#!/bin/bash
cd <repo>/research/model-study
S=$(date +%s)
date -u +%FT%TZ
~/.cerebrollm/venv/bin/python r1_live_index.py
echo EXIT $?
echo WALL_SECONDS $(( $(date +%s) - S ))
cd ../../engine
bin/cerebrollm status
