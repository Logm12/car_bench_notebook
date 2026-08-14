#!/bin/bash
# =====================================================================
# CAR-bench Hallucination Task Benchmark Runner
# Evaluates Agent against local vLLM server (port 8300)
# =====================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="/mnt/hungpv/car_bench_notebook/output/bench_hallu"
mkdir -p /mnt/hungpv/car_bench_notebook/output

# Auto-detect next available numbered log file
LOG_NUM=1
while [ -f "${LOG_PREFIX}_${LOG_NUM}.log" ]; do
    LOG_NUM=$((LOG_NUM + 1))
done
LOG_FILE="${LOG_PREFIX}_${LOG_NUM}.log"

echo "=============================================="
echo "Starting CAR-bench Hallucination Evaluation..."
echo "Logging to: $LOG_FILE"
echo "=============================================="

# Ensure OpenAI API base is unset for user evaluator but pointed for agent
unset OPENAI_API_BASE

# Validate that the user provided an OpenAI API key in their environment
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY is not set in your environment!"
    echo "Please set it before running this script:"
    echo "  export OPENAI_API_KEY=\"your-openai-key\""
    exit 1
fi

# Route Agent LLM to our local vLLM server
export AGENT_LLM="openai/hallucination"
export AGENT_API_BASE="http://localhost:8300/v1"
export AGENT_API_KEY="local-dummy-key"

# Update PATH to include local user binaries where uv is installed
export PATH="/mnt/hungpv/.local/bin:$HOME/.local/bin:$PATH"

# Change directory to project root
cd /mnt/hungpv/car_bench_notebook

# Run the official CAR-bench runner tool
uv run car-bench-run scenarios/track_1_agent_under_test/local_hallucination_test.toml \
    --output "/mnt/hungpv/car_bench_notebook/output/hallu_sft_${LOG_NUM}.json" \
    --show-logs 2>&1 | tee "$LOG_FILE"
