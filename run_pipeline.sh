#!/usr/bin/env bash
# =====================================================================
# CAR-Bench Master Pipeline Script
# Executes environment setup, dataset generation, and SFT training
# =====================================================================

set -e

echo "=== CAR-Bench End-to-End Pipeline Execution ==="

# 1. Load or Initialize Environment Variables (.env)
if [ ! -f .env ]; then
    echo "[1/4] Creating .env from .env.example..."
    cp .env.example .env
fi

echo "[1/4] Loading environment variables from .env..."
set -a
source .env 2>/dev/null || true
set +a

# 2. Synchronize Python Environment using uv
echo "[2/4] Synchronizing Python environment dependencies using uv..."
if command -v uv >/dev/null 2>&1; then
    uv sync
else
    echo "[WARN] 'uv' command not found. Using system python..."
fi

# 3. Generate In-Domain SFT Data
echo "[3/4] Running CAR-Bench SFT Data Generator..."
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your_openai_or_vllm_key_here" ]; then
    echo "       Running in API mode (Base: ${OPENAI_API_BASE:-http://localhost:8000/v1}, Model: ${CAR_BENCH_MODEL:-Qwen/Qwen2.5-7B-Instruct})..."
    uv run data/generate_car_bench_sft_data.py --mode api --api-base "${OPENAI_API_BASE:-http://localhost:8000/v1}" --api-key "$OPENAI_API_KEY" --model "${CAR_BENCH_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
else
    echo "       Running in Simulated mode (0% API cost, 100% offline)..."
    uv run data/generate_car_bench_sft_data.py --mode simulated
fi

# 4. Execute SFT Fine-Tuning across all task categories
echo "[4/4] Executing SFT Fine-Tuning across Base, Disambiguation, and Hallucination tasks..."

echo "---------------------------------------------------------------------"
echo "Starting Base Tasks SFT Fine-Tuning..."
bash llm-training/train_base.sh

echo "---------------------------------------------------------------------"
echo "Starting Disambiguation Tasks SFT Fine-Tuning..."
bash llm-training/train_disambiguation.sh

echo "---------------------------------------------------------------------"
echo "Starting Hallucination Tasks SFT Fine-Tuning..."
bash llm-training/train_hallucination.sh

echo "====================================================================="
echo "[SUCCESS] CAR-Bench End-to-End Pipeline completed successfully!"
echo "====================================================================="
