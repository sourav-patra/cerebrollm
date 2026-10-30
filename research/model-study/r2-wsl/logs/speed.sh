#!/bin/bash
R=~/cerebrollm-scratch/m/run.sh
while ! grep -q CHAINDONE ~/cerebrollm-scratch/m/chain.log; do sleep 10; done
for m in phi4 devstral:24b gpt-oss:20b qwen3:14b qwen3:8b; do
  $R s-${m//:/-} speed $m
done
echo SPEEDDONE >> ~/cerebrollm-scratch/m/speed.log
