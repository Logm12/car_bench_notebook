import json
from datasets import load_dataset

print("Loading dataset from HF...")
dataset = load_dataset("upwitu/trash_draft_am", split="train")
print(f"Total samples: {len(dataset)}")
print("Columns:", dataset.column_names)

first_sample = dataset[0]
print("\n--- RAW MESSAGES ---")
print(json.dumps(first_sample.get("raw_messages", [])[:4], indent=2, ensure_ascii=False))

print("\n--- AUGMENTED MESSAGES ---")
print(json.dumps(first_sample.get("augmented_messages", [])[:4], indent=2, ensure_ascii=False))

print("\n--- TOOLS ---")
print(json.dumps(first_sample.get("tools", []), indent=2, ensure_ascii=False))
