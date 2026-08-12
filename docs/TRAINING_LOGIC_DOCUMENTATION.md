# CAR-bench SFT Training: Technical Documentation

**Version**: 1.1.0 | **Last Updated**: 2026-08-12  
**Files**: `train_base.py`, `train_hallucination.py`, `train_disambiguation.py`  
**Model**: Qwen/Qwen3.5-4B via Unsloth | **Hardware**: NVIDIA A40 44GB / CUDA 12.8 / 13.0  
**Environment**: `carbench_env` (Conda / uv)

---

## 1. Overview & Objectives

The CAR-bench training system fine-tunes the **Qwen 3.5 4B** language model across three distinct automotive assistant tasks:

1. **Base & Safety Confirmation Tasks** (`train_base.py`): Teaches the model to execute complex multi-step tool call chains (`dependent_on_action_index`), parallel tool calls, and request user confirmation before performing sensitive vehicle operations (`send_email`, `open_close_trunk_door`, `set_head_lights_high_beams`).
2. **Disambiguation Tasks** (`train_disambiguation.py`): Teaches the model to **resolve ambiguous user requests** by first querying internal lookup tools (`get_user_preferences`, `get_vehicle_status`) before asking the user for clarification. This enforces an "Internal Resolution First" policy.
3. **Hallucination Tasks** (`train_hallucination.py`): Teaches the model to **correctly refuse** requests that require tools or parameters not available in its current environment (1-sentence polite refusal), followed by multi-turn feature switching recovery.

---

## 2. CAR-Bench Environment (`carbench_env`) & Setup

Training scripts and benchmark evaluation run inside the `carbench_env` environment stack. The exact pinned package versions extracted from the production GPU server are stored in [`requirements.txt`](file:///e:/VinAI/VSG/car-bench-ijcai-vsf/requirements.txt) and [`llm-training/requirements.txt`](file:///e:/VinAI/VSG/car-bench-ijcai-vsf/llm-training/requirements.txt).

### Key Pinned Dependencies:
- **PyTorch & CUDA Accelerators**: `torch==2.11.0`, `triton==3.6.0`, `xformers==0.0.35`, `bitsandbytes==0.49.2`, `torchao==0.17.0`.
- **Unsloth Fine-Tuning Stack**: `unsloth==2026.6.9`, `unsloth_zoo==2026.7.1`, `transformers==5.13.0`, `tokenizers==0.22.2`, `trl==0.24.0`, `datasets==5.0.0`.
- **Inference & Evaluation**: `vllm==0.24.0`, `openai==2.44.0`, `pydantic==2.13.4`, `uvicorn==0.50.2`.

### Replicating `carbench_env`:
```bash
# Using Conda
conda create -n carbench_env python=3.10 -y
conda activate carbench_env
pip install -r requirements.txt

# Or using uv (Recommended)
uv venv .venv --python 3.10
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 3. System Initialization & CUDA Pre-Loading

Both training scripts perform the following initialization steps before model loading:

| Step | Purpose |
|------|---------|
| **CUDA Pre-load** | Pre-loads all Nvidia `.so` libraries via `ctypes.CDLL()` to prevent `bitsandbytes` loading errors on older servers |
| **Input Monkeypatch** | Overrides `builtins.input` with `lambda: "y"` to auto-confirm Unsloth's `trust_remote_code` interactive prompt |
| **TorchAO Compatibility** | Patches missing PyTorch `int1-int7`/`uint1-uint7` dtypes and `_pytree.register_constant` for compatibility with older Torch versions |
| **Transformers Torchao Block** | Disables `is_torchao_available()` in Transformers to prevent AttributeErrors during import |
| **DDP Cleanup** | Unsets DDP environment variables (`WORLD_SIZE`, `RANK`, etc.) to ensure clean single-GPU training |
| **Dataset Logger Suppression** | Suppresses `datasets.fingerprint` hashing warnings during Arrow map operations |

---

## 4. Model Loading & PEFT LoRA Configuration

The base model is loaded using Unsloth's `FastLanguageModel.from_pretrained()` with BF16 precision:

```python
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen3.5-4B",
    max_seq_length=16384,       # Extended context for enriched system prompts + multi-turn tool conversations
    dtype=torch.bfloat16,       # BF16 precision for A40 GPU
    load_in_4bit=False,         # Full precision (unquantized) for optimal LoRA gradients
    trust_remote_code=True
)
```

**LoRA Configuration**:
```python
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                           # LoRA rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,                  # Scaling factor
    lora_dropout=0,                 # No dropout for Unsloth efficiency
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)
```

---

## 5. Loss Masking via `train_on_responses_only`

To ensure the model learns to generate tool calls and assistant responses rather than memorizing system prompts and user queries, loss calculation is strictly masked using Unsloth's `train_on_responses_only`:

```python
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)
```

All tokens corresponding to system prompts, environment state, and user instructions have `labels = -100` (ignored in cross-entropy loss calculation). Only assistant tool calls and text completions contribute to parameter updates.
