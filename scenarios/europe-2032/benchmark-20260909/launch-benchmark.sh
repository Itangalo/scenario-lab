#!/bin/bash
# Model benchmark: meta/muse-spark-1.3-contributor against the standard qwen.
#
# Three matched pairs. Each pair shares a dice seed, so both models see exactly
# the same events and the only difference is the model. That deliberately
# departs from the never-reuse-seeds rule in story/README.md: the rule exists so
# story branches explore different worlds, and this is a controlled comparison
# rather than story material. The runs carry their own batch tag and are never
# mixed with story or statistics runs.
#
# Both sides run with llm.max_tokens=16000. qwen never approaches that ceiling,
# so it changes nothing for the incumbent, but muse's reasoning is mandatory and
# at the scenario's own 3000 the events step exhausted the budget on reasoning
# and returned nothing parseable. Raising it for both keeps the configs
# identical apart from the model.
#
# muse additionally runs at reasoning_effort=minimal. Measured on one
# events-shaped prompt: default effort spends 1 599 output tokens and 18.2s,
# minimal spends 304 and 3.3s, for the same answer. Benchmarking at the default
# would measure a setting nobody would choose.
#
# Usage:
#   nohup caffeinate -dimsu scripts/run-notify.sh /tmp/benchmark.log -- \
#       scenarios/europe-2032/benchmark-20260909/launch-benchmark.sh &
#   grep -q RUN_DONE /tmp/benchmark.log   # completion check; never sleep+pgrep

set -uo pipefail
cd "$(dirname "$0")/../../.." || exit 1

VARIANT="scenarios/europe-2032/variants/verification-bounded.yaml"
STATES="scenarios/europe-2032/benchmark-20260909/initial-states"
MUSE="openrouter:meta/muse-spark-1.3-contributor"
SEEDS=(771001 771002 771003)

pids=()

for i in 0 1 2; do
    draw=$(printf "draw-%03d.json" $((i + 1)))
    seed=${SEEDS[$i]}

    python3 -m scenario_lab.cli run "$VARIANT" \
        --model "$MUSE" \
        --override llm.reasoning_effort=minimal \
        --override llm.max_tokens=16000 \
        --seed "$seed" \
        --initial-state "$STATES/$draw" \
        --quiet --skip-model-checks \
        > "/tmp/bench-muse-$seed.log" 2>&1 &
    pids+=($!)

    python3 -m scenario_lab.cli run "$VARIANT" \
        --override llm.max_tokens=16000 \
        --seed "$seed" \
        --initial-state "$STATES/$draw" \
        --quiet --skip-model-checks \
        > "/tmp/bench-qwen-$seed.log" 2>&1 &
    pids+=($!)
done

echo "launched ${#pids[@]} runs: 3 muse (minimal effort) + 3 qwen, seeds ${SEEDS[*]}"

fail=0
for pid in "${pids[@]}"; do
    wait "$pid" || fail=$((fail + 1))
done

echo "all runs finished; $fail failed"
exit 0
