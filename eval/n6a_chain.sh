#!/bin/bash
# restarted at 18:05Z with A4 limited to 3 runs: ask runs at temperature 0 and one call takes about 25 s (model swaps)
# N6a: after the phi4 phase, run arm A4 (cerebrollm ask, lane N7) for the three local models, then grade everything
# with gpt-oss:20b, then regrade the gpt-oss-20b answers with gemma4:12b. Each step takes the GPU lock on its own.
D=$(cd "$(dirname "$0")" && pwd)
$D/n6a_local.sh probe >> $D/runs/logs/n6a-gpu-probe.log 2>&1 || { echo "GPU probe failed: CPU or no model loaded, stopping"; exit 1; }
$D/n6a_local.sh gen gemma4-12b,gpt-oss-20b,phi4 A4 3 >> $D/runs/logs/n6a-gen-a4.log 2>&1
$D/n6a_local.sh grade gpt-oss:20b gpt-oss-20b,gemma4-12b,phi4,sonnet-5-5
$D/n6a_local.sh grade gemma4:12b gpt-oss-20b
