#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "torch",
#     "transformers",
#     "datasets",
#     "trl",
#     "unsloth",
#     "huggingface_hub",
# ]
# ///
"""
CAR-Bench Base Task SFT Training Script using Unsloth.
Fine-tunes Qwen 3.5 4B on Base / Confirmation vehicle control tool execution scenarios.
Auto-downloads dataset from Hugging Face (upwitu/carbench_sft_benchmark_data) if local file is missing.
"""

import builtins
builtins.input = lambda *args, **kwargs: "y"

import os
import re
import json
import ctypes
import glob
import logging

# Suppress fingerprint hashing warnings
logging.getLogger("datasets.fingerprint").setLevel(logging.ERROR)

# Pre-load Nvidia CUDA libraries to prevent bitsandbytes loading errors
nvidia_paths = [
    "/mnt/hungpv/miniconda3/envs/carbench_env/lib/python3.10/site-packages/nvidia/*/lib/*.so*",
    "/mnt/hungpv/miniconda3/envs/carbench_env/lib/python3.10/site-packages/nvidia/cu13/lib/*.so*"
]
for pattern in nvidia_paths:
    for so_file in glob.glob(pattern):
        try:
            ctypes.CDLL(so_file, mode=ctypes.RTLD_GLOBAL)
        except Exception:
            pass

os.environ["HF_TRUST_REMOTE_CODE"] = "1"

import torch
from datasets import load_dataset, Dataset
from unsloth import FastLanguageModel, train_on_responses_only
from trl import SFTTrainer, SFTConfig
from huggingface_hub import hf_hub_download

MODEL_NAME = "Qwen/Qwen3.5-4B"
PERSISTENT_DIR = "./outputs_base"
ADAPTER_PATH = os.path.join(PERSISTENT_DIR, "sft_lora_adapter")
MERGED_PATH = os.path.join(PERSISTENT_DIR, "sft_merged_model")

os.makedirs(PERSISTENT_DIR, exist_ok=True)

HF_REPO_ID = "upwitu/carbench_sft_benchmark_data"
HF_FILE_NAME = "data/car_base_sft.jsonl"
LOCAL_DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/car_base_sft.jsonl")

if os.path.exists(LOCAL_DATA_FILE):
    print(f"Found local in-domain dataset: '{os.path.abspath(LOCAL_DATA_FILE)}'")
    target_data_path = LOCAL_DATA_FILE
else:
    print(f"Local dataset not found. Auto-downloading '{HF_FILE_NAME}' from Hugging Face '{HF_REPO_ID}'...")
    target_data_path = hf_hub_download(repo_id=HF_REPO_ID, filename=HF_FILE_NAME, repo_type="dataset")
    print(f"Downloaded dataset to '{target_data_path}'")

samples = []
with open(target_data_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            samples.append(json.loads(line))

print(f"Loaded {len(samples)} base task SFT samples.")

formatted_data = []
for sample in samples:
    messages = sample.get("messages", [])
    if messages:
        formatted_data.append({"messages": messages})

dataset = Dataset.from_list(formatted_data)
dataset_split = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = dataset_split["train"]
eval_dataset = dataset_split["test"]
print(f"Split completed: {len(train_dataset)} train samples, {len(eval_dataset)} evaluation samples")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=16384,
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    load_in_4bit=False,
    trust_remote_code=True
)

text_tokenizer = tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
tokenizer.eos_token = "<|im_end|>"
text_tokenizer.eos_token = "<|im_end|>"

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,
    lora_dropout=0.0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

training_args = SFTConfig(
    output_dir=PERSISTENT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=1,
    num_train_epochs=3,
    save_strategy="epoch",
    save_total_limit=1,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    optim="adamw_8bit",
    lr_scheduler_type="cosine",
    warmup_steps=10,
    seed=42,
    report_to="none",
    dataset_text_field="text",
    max_seq_length=16384,
    packing=False,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    dataset_text_field="text",
    max_seq_length=16384,
    dataset_num_proc=4,
    packing=False,
    args=training_args,
)

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)

print("Starting Base Task SFT Fine-Tuning...")
trainer.train()

print(f"Saving LoRA adapter to {ADAPTER_PATH}...")
model.save_pretrained(ADAPTER_PATH)
tokenizer.save_pretrained(ADAPTER_PATH)
print("Base task SFT training completed successfully!")
