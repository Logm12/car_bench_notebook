import json
import sys
from datasets import load_dataset

sys.stdout.reconfigure(encoding='utf-8')

print("Loading dataset from HF...")
dataset = load_dataset("upwitu/trash_draft_am", split="train")
print(f"Total samples: {len(dataset)}")
print("Columns:", dataset.column_names)
first_sample = dataset[0]
print("First sample:")
# Print representation safely
print(json.dumps(first_sample, indent=2, ensure_ascii=False)[:2000])
