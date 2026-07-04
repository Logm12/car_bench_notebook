import pandas as pd
from huggingface_hub import hf_hub_download
import pyarrow as pa

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

# Clean
full_df["tools"] = full_df["tools"].apply(lambda x: x if isinstance(x, list) else [])

weird_indices = []
for idx, item in enumerate(full_df["tools"]):
    if not isinstance(item, list):
        print(f"Index {idx} is not a list! Type: {type(item)}")
        weird_indices.append(idx)
    else:
        # Check elements inside the list
        for sub_idx, sub_item in enumerate(item):
            if not isinstance(sub_item, dict):
                print(f"Index {idx}, sub-index {sub_idx} is not a dict! Type: {type(sub_item)}, Value: {sub_item}")
                weird_indices.append(idx)
                break

print(f"Total weird indices: {len(weird_indices)}")
if weird_indices:
    print("Weird values:", [full_df["tools"].iloc[i] for i in weird_indices[:5]])

# Let's inspect pyarrow schema mapping
# If we convert tools to JSON string, does it work?
# SFT doesn't need PyArrow to understand tools as a struct! SFT only needs tools as a JSON string or we can just apply the chat template FIRST, and then drop the tools column!
# YES!
# In the SFT pipeline, do we even need the 'tools' column in the final Arrow Dataset?
# NO!
# The only column SFTTrainer needs is the 'text' column (the formatted conversation text)!
# So we can format the text column inside pandas, and then drop all other columns (especially 'tools') BEFORE converting to Arrow Dataset!
# That way, the Arrow Dataset will ONLY contain the 'text' column (which is just strings) and 'length' column (which is just integers)!
# This completely bypasses any PyArrow conversion issues with the 'tools' column!
# Let's verify this idea!
try:
    print("\nTesting drop tools before convert:")
    # Create text column
    # Just a dummy text column for test
    full_df["text"] = "dummy text"
    # Keep only text
    clean_df = full_df[["text"]]
    dataset = Dataset.from_pandas(clean_df)
    print("Dataset conversion from pandas after dropping tools successful!")
except Exception as e:
    print("Dataset conversion failed:", str(e))
