# CAR-Bench SFT Training & Benchmark Suite

This repository provides an end-to-end pipeline for generating in-domain SFT datasets in OpenAI Chat Completions specification, fine-tuning Qwen 3.5 4B using Unsloth (LoRA / BF16), and evaluating model execution across the official CAR-bench suite covering 58 automotive tools and 19 operational policies.

---

## 1. Environment Setup & Dependency Management (`uv`)

This project uses `uv` (Fast Python Package Installer & Resolver) for virtual environment and dependency management.

### Environment Synchronization
```bash
# Synchronize virtual environment and install all required packages
uv sync
```

The virtual environment is created automatically at `.venv`. Python scripts can be executed directly via:
```bash
uv run python <script_path>
```

---

## 2. Automatic Dataset Ingestion from Hugging Face

All SFT training datasets are packaged and published on the Hugging Face Hub:
- **Dataset Repository**: [upwitu/carbench_sft_benchmark_data](https://huggingface.co/datasets/upwitu/carbench_sft_benchmark_data)

### Dataset Catalog
- `data/car_base_sft.jsonl`: 3,500 SFT samples for Base Tasks & Safety Confirmation.
- `data/car_disambiguation_sft.jsonl`: 2,520 SFT samples for Disambiguation Tasks.
- `data/car_hallucination_sft.jsonl`: 2,548 SFT samples for Hallucination Tasks.
- `data/car_sft_dataset_openai.jsonl`: 8,568 combined master dataset samples across all categories.

*Note*: Training scripts (`train_base.py`, `train_disambiguation.py`, `train_hallucination.py`) include automatic fallback handlers: if local data files are absent, scripts automatically download the target dataset file from `upwitu/carbench_sft_benchmark_data`.

---

## 3. Codebase Architecture

### A. Data Generation Engine (`data/`)
- `data/generate_car_bench_sft_data.py`: Source code generating 8,568 OpenAI-formatted SFT samples. Supports dual execution backends: `--mode simulated` (0-cost offline rule-based simulation) and `--mode api` (online vLLM server or OpenAI API endpoint).
- `data/generation_code_documentation.md`: Detailed technical specification of the generator architecture, Mermaid execution flowcharts, and error resolution mapping.

### B. SFT Fine-Tuning Module (`llm-training/`)
- `llm-training/train_base.py` & `llm-training/train_base.sh`: SFT training pipeline for Base Tasks and Safety Confirmations.
- `llm-training/train_disambiguation.py` & `llm-training/train_disambiguation.sh`: SFT training pipeline for Disambiguation Tasks (prioritizing internal preference lookups before user clarification).
- `llm-training/train_hallucination.py` & `llm-training/train_hallucination.sh`: SFT training pipeline for Hallucination Tasks (1-sentence polite refusals on pruned capabilities and multi-turn feature switching).
- `llm-training/pyproject.toml` & `llm-training/uv.lock`: Dependency definitions for Unsloth, PyTorch, and Transformers.

### C. Benchmark Evaluation Suite (`scenarios/`, `src/`, `scripts/`)
- `scenarios/track_1_agent_under_test/`: TOML evaluation scenario configurations (`benchmark_sft_hallucination.toml`, `local_base_test.toml`, `local_disambiguation_test.toml`).
- `src/track_1_agent_under_test/car_bench_agent.py`: Agent execution module interfacing with CAR-bench environment tool APIs.
- `src/evaluator/server.py`: Benchmark evaluation server validating tool call execution correctness and policy adherence.
- `scripts/run_vllm_*.sh` & `scripts/run_bench_*.sh`: Shell wrappers to launch vLLM inference servers and trigger automated benchmark evaluation runs.

---

## 4. Execution Guide

### 1. Generate Training Data
```bash
# Offline simulation mode (0% API cost)
uv run data/generate_car_bench_sft_data.py --mode simulated

# Online API mode via local vLLM server
uv run data/generate_car_bench_sft_data.py --mode api --api-base http://localhost:8000/v1 --model Qwen/Qwen2.5-7B-Instruct
```

### 2. Execute SFT Training
```bash
# Train Base tasks
bash llm-training/train_base.sh

# Train Disambiguation tasks
bash llm-training/train_disambiguation.sh

# Train Hallucination tasks
bash llm-training/train_hallucination.sh
```

### 3. Run Benchmark Evaluation
```bash
# Step 1: Launch vLLM inference server
bash scripts/run_vllm_disambig.sh

# Step 2: Trigger benchmark evaluator
bash scripts/run_bench_disambig.sh
```
