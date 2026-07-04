import json
from datasets import load_dataset

dataset = load_dataset("upwitu/trash_draft_am", split="train")
first_sample = dataset[0]
for idx, msg in enumerate(first_sample["conversations"]):
    print(f"Message {idx}: keys={list(msg.keys())}")
    for k, v in msg.items():
        if v is not None:
            print(f"  {k}: {repr(v)[:200]}")
