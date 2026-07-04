import pandas as pd
from huggingface_hub import hf_hub_download
from datasets import Dataset

jsonl_files = [
    "data/interactive_agent_disambiguation.jsonl",
    "data/interactive_agent_hallucination.jsonl",
    "data/search_disambiguation.jsonl",
    "data/search_hallucination.jsonl"
]

dfs = []
for filename in jsonl_files:
    local_file_path = hf_hub_download(
        repo_id="upwitu/trash_draft_am",
        filename=filename,
        repo_type="dataset"
    )
    dfs.append(pd.read_json(local_file_path, lines=True))

full_df = pd.concat(dfs, ignore_index=True)

# Create dummy text and length columns for testing
full_df["text"] = "dummy text"
full_df["length"] = 123

# Drop all columns EXCEPT text and length (to completely bypass PyArrow tools schema errors!)
clean_df = full_df[["text", "length"]]

try:
    print("Attempting Dataset.from_pandas after dropping tools and messages columns...")
    dataset = Dataset.from_pandas(clean_df)
    print("Dataset.from_pandas successful! Size:", len(dataset))
except Exception as e:
    print("Dataset.from_pandas failed:", str(e))
