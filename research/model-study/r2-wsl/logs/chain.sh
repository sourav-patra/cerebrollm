#!/bin/bash
# correctness for the remaining models, one at a time; waits for the pull script before the models it still pulls
R=~/cerebrollm-scratch/m/run.sh
$R c-devstral correctness devstral:24b
while ! grep -q ALLDONE ~/cerebrollm-scratch/m/pulls.log; do sleep 10; done
$R c-gptoss correctness gpt-oss:20b
$R c-qwen14 correctness qwen3:14b
$R c-qwen8 correctness qwen3:8b
echo CHAINDONE >> ~/cerebrollm-scratch/m/chain.log
