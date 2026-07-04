import sys
import torch
from transformers import AutoTokenizer
from datasets import load_dataset

sys.stdout.reconfigure(encoding='utf-8')

# Vá tương thích
for i in range(1, 8):
    int_attr = f"int{i}"
    uint_attr = f"uint{i}"
    if not hasattr(torch, int_attr):
        setattr(torch, int_attr, torch.int8)
    if not hasattr(torch, uint_attr):
        setattr(torch, uint_attr, torch.uint8)

import transformers
transformers.utils.import_utils.is_torchao_available = lambda *args, **kwargs: False
transformers.utils.is_torchao_available = lambda *args, **kwargs: False

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-4B", trust_remote_code=True)
dataset = load_dataset("upwitu/trash_draft_am", split="train")
first_sample = dataset[0]

tools = first_sample.get("tools")
augmented_messages = first_sample.get("augmented_messages")

formatted_text = tokenizer.apply_chat_template(
    augmented_messages,
    tokenize=False,
    add_generation_prompt=False,
    tools=tools
)

with open("scratch/formatted_text_full.txt", "w", encoding="utf-8") as f:
    f.write(formatted_text)

print("Saved to scratch/formatted_text_full.txt")
