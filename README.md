# CAR-Bench SFT Training & Benchmark Suite

This repository provides an end-to-end pipeline for generating in-domain SFT datasets in OpenAI Chat Completions specification, fine-tuning Qwen 3.5 4B using Unsloth (LoRA / BF16), and evaluating model execution across the official CAR-bench suite covering 58 automotive tools and 19 operational policies.

---

## 1. Quickstart Workflow

The setup workflow is designed to be completed in three simple commands:

```bash
# Step 1: Clone the repository
git clone https://github.com/Logm12/car_bench_openai_dataset.git
cd car_bench_openai_dataset

# Step 2: Create .env configuration from template
cp .env.example .env
# Edit .env to set your HF_TOKEN, OPENAI_API_BASE, OPENAI_API_KEY, etc.

# Step 3: Run the single master pipeline script
bash run_pipeline.sh
```

Executing `bash run_pipeline.sh` automatically performs:
1. Environment variable loading from `.env`.
2. Python environment synchronization via `uv sync` or Conda.
3. In-domain SFT dataset generation (`data/generate_car_bench_sft_data.py`).
4. End-to-end SFT fine-tuning across Base, Disambiguation, and Hallucination tasks (`llm-training/train_*.sh`).

---

## 2. CAR-Bench Execution Environment (`carbench_env`)

Training scripts and benchmark evaluations run inside the `carbench_env` environment stack (Python 3.10, PyTorch 2.11.0, CUDA 12.8/13.0, Unsloth 2026.6.9, vLLM 0.24.0).

Exact pinned package versions from the production GPU server are stored in [`requirements.txt`](file:///e:/VinAI/VSG/car-bench-ijcai-vsf/requirements.txt) and [`llm-training/requirements.txt`](file:///e:/VinAI/VSG/car-bench-ijcai-vsf/llm-training/requirements.txt).

### Replicating `carbench_env` via Conda

```bash
# Create Conda environment with Python 3.10
conda create -n carbench_env python=3.10 -y
conda activate carbench_env

# Install exact pinned packages from server carbench_env
pip install -r requirements.txt
```

### Replicating `carbench_env` via `uv` (Recommended for Speed)

```bash
# Create virtual environment with Python 3.10
uv venv .venv --python 3.10
source .venv/bin/activate  # On Linux/macOS (.venv\Scripts\activate on Windows)

# Install pinned requirements via uv
uv pip install -r requirements.txt

# Or synchronize environment automatically
uv sync
```

---

## 3. Environment Configuration (`.env`)

The project uses a `.env` file (copied from `.env.example`) to configure tokens, API backends, and repository targets:

```env
# 1. Hugging Face Authentication Token
HF_TOKEN=your_huggingface_token_here

# 2. LLM API Backend Configuration (vLLM / OpenAI / LiteLLM)
OPENAI_API_BASE=http://localhost:8000/v1
OPENAI_API_KEY=your_openai_or_vllm_key_here
CAR_BENCH_MODEL=Qwen/Qwen2.5-7B-Instruct

# 3. Hugging Face Target Repositories
HF_DATASET_REPO=upwitu/carbench_sft_benchmark_data
HF_MODEL_LORA_REPO=upwitu/qwen3.5-4b-sft-carbench-lora
HF_MODEL_MERGED_REPO=upwitu/qwen3.5-4b-sft-carbench
```

---

## 4. Automatic Dataset Ingestion from Hugging Face

All SFT training datasets are packaged and published on the Hugging Face Hub:
- **Dataset Repository**: [upwitu/carbench_sft_benchmark_data](https://huggingface.co/datasets/upwitu/carbench_sft_benchmark_data)

### Dataset Catalog
- `data/car_base_sft.jsonl`: 3,500 SFT samples for Base Tasks & Safety Confirmation.
- `data/car_disambiguation_sft.jsonl`: 2,520 SFT samples for Disambiguation Tasks.
- `data/car_hallucination_sft.jsonl`: 2,548 SFT samples for Hallucination Tasks.
- `data/car_sft_dataset_openai.jsonl`: 8,568 combined master dataset samples across all categories.

*Note*: Training scripts (`train_base.py`, `train_disambiguation.py`, `train_hallucination.py`) include automatic fallback handlers: if local data files are absent, scripts automatically download the target dataset file from `upwitu/carbench_sft_benchmark_data`.

---

## 5. Documentation Catalog

- **Training Code Logic**: [`docs/TRAINING_LOGIC_DOCUMENTATION.md`](file:///e:/VinAI/VSG/car-bench-ijcai-vsf/docs/TRAINING_LOGIC_DOCUMENTATION.md) (Detailed breakdown of Unsloth initialization, CUDA pre-loading, loss masking via `train_on_responses_only`, and LoRA hyperparameter configuration).
- **Data Generator Architecture**: [`data/generation_code_documentation.md`](file:///e:/VinAI/VSG/car-bench-ijcai-vsf/data/generation_code_documentation.md) (Architecture of `--mode simulated` vs `--mode api`, Mermaid flowcharts, and 58-tool registry specs).

---

## 6. Codebase Architecture

### A. Data Generation Engine (`data/`)
- `data/generate_car_bench_sft_data.py`: Source code generating 8,568 OpenAI-formatted SFT samples. Supports dual execution backends: `--mode simulated` (0-cost offline rule-based simulation) and `--mode api` (online vLLM server or OpenAI API endpoint).
- `data/generation_code_documentation.md`: Detailed technical specification of the generator architecture, Mermaid execution flowcharts, and error resolution mapping.

### B. SFT Fine-Tuning Module (`llm-training/`)
- `llm-training/train_base.py` & `llm-training/train_base.sh`: SFT training pipeline for Base Tasks and Safety Confirmations.
- `llm-training/train_disambiguation.py` & `llm-training/train_disambiguation.sh`: SFT training pipeline for Disambiguation Tasks (prioritizing internal preference lookups before user clarification).
- `llm-training/train_hallucination.py` & `llm-training/train_hallucination.sh`: SFT training pipeline for Hallucination Tasks (1-sentence polite refusals on pruned capabilities and multi-turn feature switching).
- `llm-training/requirements.txt`: Pinned package requirements from server `carbench_env`.
- `llm-training/TRAINING_LOGIC_DOCUMENTATION.md`: Technical documentation for training pipeline logic.

### C. Benchmark Evaluation Suite (`scenarios/`, `src/`, `scripts/`)
- `scenarios/track_1_agent_under_test/`: TOML evaluation scenario configurations (`benchmark_sft_hallucination.toml`, `local_base_test.toml`, `local_disambiguation_test.toml`).
- `src/track_1_agent_under_test/car_bench_agent.py`: Agent execution module interfacing with CAR-bench environment tool APIs.
- `src/evaluator/server.py`: Benchmark evaluation server validating tool call execution correctness and policy adherence.
- `scripts/run_vllm_*.sh` & `scripts/run_bench_*.sh`: Shell wrappers to launch vLLM inference servers and trigger automated benchmark evaluation runs.

---

## 7. Execution Commands Summary

### Master Pipeline (All-in-One)
```bash
bash run_pipeline.sh
```

### Individual Step Execution

#### 1. Generate Training Data
```bash
# Offline simulation mode (0% API cost)
uv run data/generate_car_bench_sft_data.py --mode simulated

# Online API mode via local vLLM server
uv run data/generate_car_bench_sft_data.py --mode api --api-base http://localhost:8000/v1 --model Qwen/Qwen2.5-7B-Instruct
```

#### 2. Execute SFT Training
```bash
# Train Base tasks
bash llm-training/train_base.sh

# Train Disambiguation tasks
bash llm-training/train_disambiguation.sh

# Train Hallucination tasks
bash llm-training/train_hallucination.sh
```

#### 3. Run Benchmark Evaluation
```bash
# Step 1: Launch vLLM inference server
bash scripts/run_vllm_disambig.sh

# Step 2: Trigger benchmark evaluator
bash scripts/run_bench_disambig.sh
```
