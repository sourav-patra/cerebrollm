#!/bin/bash
R=~/cerebrollm-scratch/m/run.sh
for m in qwen3-coder:30b qwen3:30b; do
  $R r4-c-${m//:/-} correctness $m
  $R r4-s-${m//:/-} speed $m
done
echo R4DONE >> ~/cerebrollm-scratch/m/r4.log
