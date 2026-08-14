#!/bin/bash
# =====================================================================
# CAR-bench Disambiguation Task Benchmark Runner
# Evaluates Agent against local vLLM server (port 8300)
# =====================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="/mnt/hungpv/car_bench_notebook/output/bench_disambig"
mkdir -p /mnt/hungpv/car_bench_notebook/output

# Auto-detect next available numbered log file
LOG_NUM=1
while [ -f "${LOG_PREFIX}_${LOG_NUM}.log" ]; do
    LOG_NUM=$((LOG_NUM + 1))
done
LOG_FILE="${LOG_PREFIX}_${LOG_NUM}.log"

echo "=============================================="
echo "Starting CAR-bench Disambiguation Evaluation..."
echo "Logging to: $LOG_FILE"
echo "=============================================="

# Ensure OpenAI API base is unset for user evaluator but pointed for agent
unset OPENAI_API_BASE

# Validate OPENAI_API_KEY for GPT-4o-mini user evaluator
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY is not set in your environment!"
    echo "Please set it before running this script:"
    echo "  export OPENAI_API_KEY=\"your-openai-key\""
    exit 1
fi

export AGENT_LLM="openai/disambiguation"
export AGENT_API_BASE="http://localhost:8300/v1"
export AGENT_API_KEY="local-dummy-key"
export PATH="/mnt/hungpv/.local/bin:$HOME/.local/bin:$PATH"

cd /mnt/hungpv/car_bench_notebook

# Run official CAR-bench runner tool for local_disambiguation_test.toml scenario
uv run car-bench-run scenarios/track_1_agent_under_test/local_disambiguation_test.toml \
    --output "/mnt/hungpv/car_bench_notebook/output/disambig_sft_${LOG_NUM}.json" \
    --show-logs 2>&1 | tee "$LOG_FILE"
